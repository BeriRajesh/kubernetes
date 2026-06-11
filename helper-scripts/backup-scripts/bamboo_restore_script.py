#!/usr/bin/python
from subprocess import PIPE,Popen
import shlex
from getParameterSecrets import getCredentials


def restore_table(host_name,database_name,user_name,database_password,schema_name,table_name,sfilepath):
    print ("Table Restore process is starting ......")
    try :
        #Remove the '<' from the pg_restore command.
        command = 'pg_restore --dbname=''postgres://{0}:{1}@{2}/{3}'' -n {4} -t {5} -c -1 -Fc "{6}"'\
                .format(user_name,database_password,host_name,database_name,schema_name,table_name,sfilepath)   
        print (command)
     
        #Use shlex to use a list of parameters in Popen instead of using the
        #command as is.        
        command = shlex.split(command)

        #Let the shell out of this (i.e. shell=False)
        pgrestr_prccmd = Popen(command,shell=True,stdin=PIPE,stdout=PIPE,stderr=PIPE,encoding='utf8')
        return pgrestr_prccmd.communicate()
       
    except pgrestr_prccmd.CalledProcessError as e:
        error_res = e.returncode   
        print(error_res)
    
    print (" Table restore process end now......")

def restore_database(host_name,database_name,user_name,database_password,sfilepath):
    print ("DB Restore process is starting ......")
    try :
        #Remove the '<' from the pg_restore command.
        command = 'pg_restore --dbname=''postgres://{0}:{1}@{2}/{3}'' -c -Fc "{4}"'\
                .format(user_name,database_password,host_name,database_name,sfilepath)   
        print (command)
        
        #Use shlex to use a list of parameters in Popen instead of using the
        #command as is.        
        command = shlex.split(command)

        #Let the shell out of this (i.e. shell=False)
        pgrestr_prccmd = Popen(command,shell=True,stdin=PIPE,stdout=PIPE,stderr=PIPE,encoding='utf8')
        return pgrestr_prccmd.communicate()
       
    except pgrestr_prccmd.CalledProcessError as e:
        error_res = e.returncode   
        print(error_res)
    
    print (" Table restore process end now......") 

def main():
    print (" DB restore process end now......")

if __name__ == "__main__":
    main()