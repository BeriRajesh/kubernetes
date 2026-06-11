import datetime
import json
import psycopg2
import re
import sys

from pprint import pprint
import string
import random

from redshift_conf import redshift_endpoints


def main():
    user_input = ''
    user_input = input("Enter the first letters of a user : ")

    for redshift in redshift_endpoints:
        db_name = redshift['dbname']
        db_host = redshift['host']
        db_user = redshift['username']
        db_pw = redshift['password']
        db_port = 5439
        bcolors = '\033[1;31m'
        endc = '\033[0m'
        try:
            print("\n____________________________________________________________________________________________________________")
            print('\nSearching Cluster : ' + db_host + '\n')
            connection = psycopg2.connect(user=db_user,password=db_pw,host=db_host,port=db_port, database=db_name)        
            cur = connection.cursor()
            postgreSQL_select_Query = "SELECT * FROM pg_user WHERE usename like '" + user_input  +"%' ORDER BY usename;"
            cur.execute(postgreSQL_select_Query)
            user_records = cur.fetchall() 
            print("Printing the list of users matching the username provided\n")
            for row in user_records:
                print("\n\t"+ bcolors + row[0] + endc)
        except (Exception, psycopg2.Error) as error :
                print ("Error while fetching data from PostgreSQL", error)
        finally:
            #closing database connection.
            if(connection):
                cur.close()
                connection.close()
                print("\nPostgreSQL connection is closed")
                


if __name__ == "__main__":
    # execute only if run as a script
    main()