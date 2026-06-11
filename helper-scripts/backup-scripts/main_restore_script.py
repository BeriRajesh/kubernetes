#!/usr/bin/python
import sys
import os
import argparse
import re
from subprocess import PIPE,Popen
import shlex
import datetime 
from getParameterSecrets import getCredentials
from bamboo_restore_script import restore_table ,restore_database
global svar_username,svar_password,svar_hostname,sfilepath,findindx,chkindex
global svar_bckup_path,svar_backup_name,script_dir,shostnm,sfullhostnm

def main():
    
    #env,type:database/table,dbname,schema,tablename
    print ("Take table and database restore specific the table")

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
    sfilepath=""


    # construct the argument parse and parse the arguments
    cmparlen = len(sys.argv)
    ap = argparse.ArgumentParser()
    ap.add_argument("-ev", "--env", required=True,help="name of the environement dev/qa/stg/prod")
    ap.add_argument("-ht", "--host", required=True,help="Name of the host")
    ap.add_argument("-ty", "--type", required=True,help="Type of dump database/table")
    ap.add_argument("-db", "--dbname", required=True,help="name of database",nargs='?', const='dbnm')
    ap.add_argument("-fp", "--filepath", required=True,help="file path ",nargs='?', const='fpnm')
    ap.add_argument("-sc", "--schemaname", help="name of schema",nargs='?', const='scnm')
    ap.add_argument("-tb", "--tablename", help="name of the table",nargs='?', const='tbnm')
    args = vars(ap.parse_args())
        
    
    print("length :",cmparlen)
    # display a friendly message to the user
    #print("\nHi there {}, it's nice to meet you!".format(args["env"]))
    #print("\nHi there {}, it's nice to meet you!".format(args["type"]))
    #print("\nHi there {}, it's nice to meet you!".format(args["dbname"]))
    #print("\nHi there {}, it's nice to meet you!".format(args["schemaname"]))
    #print("\nHi there {}, it's nice to meet you!".format(args["tablename"]))
    print("\nHi there {}, it's nice to meet you!".format(args["filepath"]))

    #database and  file path
    script_dir = os.path.dirname(os.path.abspath(__file__))#<-- absolute dir the script is in
    svar_backup_name = args["filepath"]
    svar_bckup_path = os.path.join(script_dir, svar_backup_name)
    print("------ \nsvar_bckup_path :",svar_bckup_path)


    chkindex = 0
    #verify path 
    findindx = re.search(r'[\/|]',svar_backup_name)
    print("findindx",findindx)
    if findindx:
        chkindex = 0
        print("\n Please avoid following special characters \ or | in the path")
    else:
        if  re.search(r'^\\',svar_backup_name):
            chkindex = 0
            print("\n Please dont start file path with '\\'")
        else:
            chkindex = 1
            
    #Env assignment 
    senv = args["env"].lower()

    #Host name setup
    shostnm = args["host"].lower()
    sfullhostnm = shostnm +"-"+senv

    # common code 
    try:
        if (len(sfullhostnm)>0) and (chkindex == 1):
            print("\n pgdump process for {}  environment ".format(senv))
            svar_username, svar_password ,svar_hostname = getCredentials('/rds/{0}/master/user'.format(sfullhostnm),'/rds/{0}/master/password'.format(sfullhostnm),'/rds/{0}/master/endpoint'.format(sfullhostnm))
            print("svar_username  =", svar_username)
            print ("svar_password  =", svar_password)
            print ("svar_hostname  =", svar_hostname)
    except:
        print ("Error in getcredentials  :",sys.exc_info()[0])
 
    #Condition for table restore
    print ("\n Final host name:",svar_hostname)
    if len(svar_hostname)>0 :
        if (args["type"].lower()=='table'):
                if (args["dbname"] !=None and args["schemaname"] !=None and args["tablename"] !=None):
                    print("------- Inside table restore process -------")
                    print("\n dbname  =", args["dbname"])
                    print("\n schemaname  =", args["schemaname"])
                    print("\n tablename  =", args["tablename"])
                    #pg_restore table restore query
                    restore_table(svar_hostname,args["dbname"],svar_username,svar_password,args["schemaname"],args["tablename"],svar_bckup_path)                    
                else:
                    print(" \nErr:---- Schema name and Tablename required for Table restore ----")   

        #Condition for database restore
        if (args["type"].lower()=='database'):
            if (args["dbname"] !=None):
                print("------- Inside database restore process -------")
                print("\n dbname  =", args["dbname"])
                #pg_restore  DB retore query
                restore_database(svar_hostname,args["dbname"],svar_username,svar_password,svar_bckup_path)                    
            else:
                print("\n Err:---- Database Name required for Datbase restore ----") 
    else:
        print("\nErr : Host name not defined/Host name issue ")                

    #Restore query
    #restore_table('audiencebuilder-upgrade-dev-v9.c488xyottj77.us-east-1.rds.amazonaws.com,'audience_builder','annalect_admin','','abdb','res_ab_audience_test')
    #dump_table('audiencebuilder-dev.cluster-c488xyottj77.us-east-1.rds.amazonaws.com','audience_builder','annalect_admin','','ab_audience')
    
    print ("\n ========= Restore process End now =============== ")

if __name__ == "__main__":
    main()