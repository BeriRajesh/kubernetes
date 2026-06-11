import sys
import boto3
from datetime import datetime, timedelta
import psycopg2
import pandas as pd
from getParameterSecrets import getCredentials
#from IPython.display import display
from tabulate import tabulate

def main():
    rds_usage_crsd_cluster = diskspace_check()
    print(rds_usage_crsd_cluster)
    if len(rds_usage_crsd_cluster) >0:
      Sendmail_with_users(rds_usage_crsd_cluster)
    else:
      return()

#check the overused cluster and send mail
def diskspace_check():
  client = boto3.client('redshift', region_name='us-east-1')
  cluster_list = client.describe_clusters()
  rds_usg_hgh_clst=[]
 
  for r in cluster_list['Clusters']:
      rdsft_cls_nm = r['ClusterIdentifier']
      rdsft_db_nm = r['DBName']
      print(r['ClusterIdentifier'] + "---"+rdsft_db_nm)

      client = boto3.client('cloudwatch',region_name='us-east-1')

      rdclusters_pdsu = client.get_metric_statistics(Namespace='AWS/Redshift',MetricName='PercentageDiskSpaceUsed',
              Dimensions=[{'Name':'NodeID','Value':'Compute-1'},
                          {'Name':'ClusterIdentifier','Value':rdsft_cls_nm}
                          ],
              StartTime=datetime.utcnow() - timedelta(seconds=60),
              EndTime=datetime.utcnow(),
              Period=60,
              Statistics=['Average']
              )
      for rc in rdclusters_pdsu['Datapoints']:
          dsk_per = float(rc['Average'])
          print('avg:',dsk_per)

      if ( dsk_per >=85.00 ):
        rdshft_endpoint = rdsft_cls_nm +":"+ rdsft_db_nm
        rds_usg_hgh_clst.append(rdshft_endpoint)   
        print('Disk utilization crossed limit')
      else:
        print('Disk utilization crossed limit')
  return rds_usg_hgh_clst

#check the overused cluster and send mail
def Sendmail_with_users(rds_cls_list = [], *args):

    for rdl in rds_cls_list:
        splt_str = rdl.split(":",1)
        cluster_name = splt_str[0]
        dbname = splt_str[1]
        print("cluster name :",cluster_name)  
        print("DB name :",dbname)  
        print("Avg :",rdl)  
        try:
            svar_para = getCredentials('/redshift/{0}/creds'.format(cluster_name))
            #convert to List variable    
            s_str = list(svar_para)       
            #print("credes2:",s_str)    
            s_str2 = s_str[0].split('\n')
            #split the each row in credential details
            s_str3 = s_str2[0].split('\n')
            s_str4 = s_str2[1].split('\n')
            s_str5 = s_str2[2].split('\n')
            #split the Indiviual credential details
            s_host = s_str3[0].split('= ')
            s_user = s_str4[0].split('= ')
            s_pwd  = s_str5[0].split('= ')
            endpoint = s_host[1]
            dbuser = s_user[1]
            dbpw = s_pwd[1]
            print("credes3:",endpoint) 
        except:
          #print ("Error in getcredentials :",sys.exc_info()[0])
          print("Unexpected error in getcredentials:", sys.exc_info()[0])
          sys.exit
        
        #Execute Query
        try:
          con = psycopg2.connect(dbname=dbname, host=endpoint, port='5439', user=dbuser, password=dbpw)
          script = """
          set query_group to 'superuser';
          SELECT TOP 30 owner_name,Table_name,DB_SIZE_gbytes FROM
          (
          SELECT trim(owner) as owner_name ,trim(database) as database_name,trim(SCHEMA) as schema_name,trim(schema_table) as Table_name ,SUM(Gigabytes) as DB_SIZE_gbytes from
          (
          SELECT CAST(use2.usename AS VARCHAR(50)) AS OWNER
          ,TRIM(pgdb.datname) AS DATABASE
          ,TRIM(pgn.nspname) AS SCHEMA
          ,TRIM(a.NAME) AS TABLE
          ,TRIM(pgn.nspname) + '.' + TRIM(a.NAME) as schema_table
          ,(b.mbytes) / 1024 AS Gigabytes
          ,a.ROWS
          FROM (
          SELECT db_id
          ,id
          ,NAME
          ,SUM(ROWS) AS ROWS
          FROM stv_tbl_perm a
          GROUP BY db_id
          ,id
          ,NAME
          ) AS a
          JOIN pg_class AS pgc ON pgc.oid = a.id
          LEFT JOIN pg_user use2 ON (pgc.relowner = use2.usesysid)
          JOIN pg_namespace AS pgn ON pgn.oid = pgc.relnamespace
          JOIN pg_database AS pgdb ON pgdb.oid = a.db_id
          JOIN (
          SELECT tbl
          ,COUNT(*) AS mbytes
          FROM stv_blocklist
          GROUP BY tbl
          ) b ON a.id = b.tbl
          --ORDER BY mbytes DESC,a.db_id,a.NAME;
          ) a
          group by owner_name,database ,schema,schema_table
          ) b 
          WHERE DB_SIZE_gbytes>0
          order by DB_SIZE_gbytes desc,owner_name asc 
          """
          cur = con.cursor()
          #query1 = open(script,"r")
          #cur.execute(query1.read())
          cur.execute(script)
          query1_results = cur.fetchall()
          result = query1_results
          nameset = []
          df = pd.DataFrame(result,columns=['Ownername','Table_name','DB_SIZE_gbytes'])
          print(tabulate(df, tablefmt="pipe", headers="keys", showindex=False))
        except :
             print ("Unexpected error in  query execution :", sys.exc_info()[0])
             sys.exit

        try: 
            #print(df.to_markdown(index=False))
            exec(open("sendmail_redshift_usage.py").read())
            print("sending mail")
        except :
             print("Unexpected error in sendmail:", sys.exc_info()[0])
             sys.exit

    con.close()

#start module
main()
