#!/usr/bin/python
import sys
import argparse
from subprocess import PIPE,Popen
import shlex
import datetime 
from getParameterSecrets import getCredentials
from bamboo_backup_script import dump_table ,dump_database
global svar_username,svar_password,svar_hostname,dump_file_name,shostnm,sfullhostnm


def main():
    
    #env,type:database/table,dbname,schema,tablename
    print ("Take table dump and restore specific the table")

    print(f"Arguments count: {len(sys.argv)}") 
    #for i, arg in enumerate(sys.argv):
    #    print ("\narg",(sys.argv[2]))
    #    print (arg.upper())
    #    print(f"\nArgument {i:>5}: {arg}")
    
    #varibale declartion
    svar_username =""
    svar_password =""
    svar_hostname =""
    shostnm =""
    sfullhostnm =""

    # construct the argument parse and parse the arguments
    cmparlen = len(sys.argv)
    ap = argparse.ArgumentParser()
    ap.add_argument("-ev", "--env", required=True,help="name of the environement dev/qa/stg/prod")
    ap.add_argument("-ht", "--host", required=True,help="Name of the host")
    ap.add_argument("-ty", "--type", required=True,help="Type of dump database/table")
    ap.add_argument("-db", "--dbname", required=True,help="name of database",nargs='?', const='dbnm')
    ap.add_argument("-sc", "--schemaname", help="name of schema",nargs='?', const='scnm')
    ap.add_argument("-tb", "--tablename", help="name of the table",nargs='?', const='tbnm')
    args = vars(ap.parse_args())
        
    
    print("length :",cmparlen)
    # display a friendly message to the user
    #print("\nHi env {}, ".format(args["env"]))
    #print("\nHi type {}, ".format(args["type"]))
    #print("\nHi dbname {}, ".format(args["dbname"]))
    #print("\nHi schemaname {}, ".format(args["schemaname"]))
    #print("\nHi tablename {}, ".format(args["tablename"]))
    
    #table and database file dump date process 
    global today ,file_date
    today = datetime.date.today()
    year, month, day = str(today).split('-')
    file_date=year + month + day

    #Env assignment 
    senv = args["env"].lower()

    #Host name setup
    shostnm = args["host"].lower()
    sfullhostnm = shostnm +"-"+senv

    # common code 
    try:
        if (len(sfullhostnm) >0):
            print("\n pgdump process for {}  environment ".format(senv))
            svar_username, svar_password ,svar_hostname = getCredentials('/rds/{0}/master/user'.format(sfullhostnm),'/rds/{0}/master/password'.format(sfullhostnm),'/rds/{0}/master/endpoint'.format(sfullhostnm))
            print("svar_username  =", svar_username)
            print ("svar_password  =", svar_password)
            print ("svar_hostname  =", svar_hostname)
    except:
        print ("Error in getcredentials  :",sys.exc_info()[0])

    print ("\nfinal hsot name:",svar_hostname)
    if len(svar_hostname)>0 :
        if (args["type"].lower() =='table'):
                if (args["dbname"] !=None and args["schemaname"] !=None and args["tablename"] !=None):
                    print("------- Inside table dump process -------")
                    print("\n dbname  =", args["dbname"])
                    print("\n schemaname  =", args["schemaname"])
                    print("\n tablename  =", args["tablename"])
                    
                    dump_file_name = senv+"_"+args["dbname"]+"_"+args["schemaname"]+"_"+args["tablename"]+"_"+file_date
                    #pg_dump table backup query
                    dump_table(svar_hostname,args["dbname"],svar_username,svar_password,args["schemaname"],args["tablename"],dump_file_name)                    
                   
                else:
                    print(" Err:---- Schema name and Tablename required for Table dump ----")   

        #Condition for database backup
        if (args["type"].lower() =='database'):
            if (args["dbname"] !=None):
                print("------- Inside database dump process -------")
                print("\n dbname  =", args["dbname"])
                
                dump_file_name = senv+"_"+args["dbname"]+"_"+file_date
                #pg_dump table backup query
                dump_database(svar_hostname,args["dbname"],svar_username,svar_password,dump_file_name)  
                
            else:
                print(" Err:---- Database Name required for Datbase dump ----") 
    else:
        print("Err : Host name not defined/Host name issue ")                

    #Dump/Restore query
    #restore_table('audiencebuilder-upgrade-dev-v9.c488xyottj77.us-east-1.rds.amazonaws.com,'audience_builder','annalect_admin','','abdb','res_ab_audience_test')
    #dump_table('audiencebuilder-dev.cluster-c488xyottj77.us-east-1.rds.amazonaws.com','audience_builder','annalect_admin','','abdb','ab_audience')
    
    print (" DB dump process End now......")

if __name__ == "__main__":
    main()