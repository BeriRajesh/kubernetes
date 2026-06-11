#!/usr/bin/python
from subprocess import PIPE,Popen
import shlex
from getParameterSecrets import getCredentials

def dump_table(host_name,database_name,user_name,database_password,schema_name,table_name,dump_file_name):
    print (" DB dump process is starting ......")
    try :

        command = 'pg_dump --dbname=''postgres://{0}:{1}@{2}/{3}'' -p 5432 -t {4}.{5} -Fc -v -f "{6}.dmp"'\
                .format(user_name,database_password,host_name,database_name,schema_name,table_name,dump_file_name)   
 
        print(command)
        pgdump_prccmd = Popen(command,stdin=PIPE,stdout=PIPE,stderr=PIPE,encoding='utf8')
        return pgdump_prccmd.communicate()

    except pgdump_prccmd.CalledProcessError as e:
        error_res = e.returncode   
        print (error_res)
    
    print (" Table dump process end now......")
    
def dump_database(host_name,database_name,user_name,database_password,dump_file_name):

    print (" DB dump process is starting ......")
    
    try :
         command = 'pg_dump --dbname=''postgres://{0}:{1}@{2}/{3}'' -p 5432  -Fc -v -f "{4}.dmp"'\
                .format(user_name,database_password,host_name,database_name,dump_file_name)  
         print(command)
         pgdump_prccmd = Popen(command,stdin=PIPE,stdout=PIPE,stderr=PIPE,encoding='utf8')    
         return pgdump_prccmd.communicate()
              
    except pgdump_prccmd.CalledProcessError as e:
        error_res = e.returncode   
        print (error_res)
    
    print (" Table restore process end now......")
    
def main():

    print ("\n Process for DB/ Table restore ")
    print ("\n DB/Table  restore process end now......")

if __name__ == "__main__":
    main()