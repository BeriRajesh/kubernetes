#!/usr/bin/env python3

import datetime
import json
import psycopg2
import re
import sys


from pprint import pprint
import string
import random

from redshift_conf import redshift_endpoints

sys.path.append('../')
import lib.helper_functions as hf

# query log filename
query_filename = 'query.log'

# queries to be issued depending on options selected
queries = []

# comment strings that can be added to ticket
ticket_comments = []

# initializing global variables
schema = ""
group_rows = []
groups = []
group = ""
group_list = []
schema_rows = []

def check_tableowner(username):
    global schema_table,schema_table_rows,schema_table_list,group_idx
    
    chk_query="""SELECT n.nspname AS schema_name , pg_get_userbyid(c.relowner) AS table_owner, c.relname AS table_name
                , CASE WHEN c.relkind = 'v' THEN 'view' ELSE 'table' END AS table_type, d.description AS table_description
                FROM pg_class As c
                LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
                LEFT JOIN pg_tablespace t ON t.oid = c.reltablespace
                LEFT JOIN pg_description As d 
                ON (d.objoid = c.oid AND d.objsubid = 0)
                WHERE c.relkind IN('r', 'v') 
                and n.nspname not in ('information_schema','pg_catalog','pg_internal')		
                and pg_get_userbyid(c.relowner) =%s
                ORDER BY n.nspname, c.relname ;"""

    all_schemas, tablenames = fetch_data(chk_query,[username])

    if len(all_schemas) >0 :
        schema_table=[]
        schema_table_rows=[]
        index = 0
        for scm in all_schemas:
            schema_table.append(scm[0])
            schema_table_rows.append(scm)
            #print('{}) {}'.format(index,scm[0]))
            index += 1
        #print ('schema_table :',schema_table)    
        #print ('schema_table_rows :',schema_table_rows)    
        #print ('index :',index)
        
        #Code commented
        #for owner_ans in range(index):
        #    group_idx = int(owner_ans-1)
        #    schema_table = schema_table_rows[group_idx][0]
        #    schema_table_list = [schema_table]        
        #    print ('for loop : {}  {}',owner_ans,schema_table)
    else:
        return None, []
    
    return schema_table,schema_table_rows

def pick_schema(group):
    global schema_rows
    index = 0
    query = """SELECT nspname AS schema FROM pg_namespace pn,pg_group pg WHERE ARRAY_TO_STRING(nspacl,',') LIKE (%s ||pg.groname|| %s) AND pg.groname =%s AND  nspowner > 1;"""
    per1="%%%"
    per2="%%%"
    all_schemas, colnames = fetch_data(query,[per1,per2,group])

    #print ('back to group list')

    for d in all_schemas:
        # schemas.append(d[0])
        schema_rows.append(d)
        print('{}) {}'.format(index, d[0]))
        index += 1

    schema_idx = 0
    print('schema :',schema_idx)
    #schema_idx = input('Choose a schema for the Default Privileges: ')
    if len(all_schemas)> 0:
        schema_idx = int(schema_idx)
        schema = schema_rows[schema_idx][0]
    else:
        schema = []

    print('Schema `{}` selected'.format(schema_rows[schema_idx][0]))

    return schema


def determine_groups_schema(schema):
    with open('schema_groups.json', 'r') as fh:
        schema_groups = json.load(fh)

    try:
        schema_group_ro = schema_groups[configuration['host']][configuration['dbname']][schema]['group_ro']
    except KeyError:
        schema_group_ro, group_list = pick_group(
            only_groups=True,
            message='Please specify RO GROUP for schema `{}`: '.format(schema))
        hf.dict_merge(schema_groups, {
            configuration['host']: {
                configuration['dbname']: {
                    schema: {
                        'group_ro': schema_group_ro
                    }
                }
            }
        })
    print("Using `{}` as RO group".format(schema_group_ro))

    try:
        schema_group_rw = schema_groups[configuration['host']][configuration['dbname']][schema]['group_rw']
    except KeyError:
        schema_group_rw, group_list = pick_group(
            only_groups=True,
            message='Please specify RW GROUP for schema `{}`: '.format(schema))
        hf.dict_merge(schema_groups, {
            configuration['host']: {
                configuration['dbname']: {
                    schema: {
                        'group_rw': schema_group_rw
                    }
                }
            }
        })
    print("Using `{}` as RW group".format(schema_group_rw))

    with open('schema_groups.json', 'w') as fh:
        json.dump(schema_groups, fh, indent=4)

    return schema_group_ro, schema_group_rw


def queries_default_privileges(username,group):
    """Create DEFAULT PRIVILEGES queries

    Keyword Args:
        username (str): optionally can work with 'username' instead of choosing one

    Returns:
        updates global queries, and ticket_comments variables

    """
    global queries, ticket_comments
    print ('user name :',username)

    # if not schema:
    print('group name :',group)
    schema = pick_schema(group)

    schema_group_ro = group
    schema_group_rw = group

    print ('schema name :',schema)
    #schema_group_ro, schema_group_rw = determine_groups_schema(schema=schema)
    if group.find('ro')>0 :
        queries.append(
            "ALTER DEFAULT PRIVILEGES FOR USER {} in SCHEMA {} Revoke SELECT ON tables FROM GROUP {};".format(
                username, schema, schema_group_ro))
    elif  group.find('rw')>0 :  
        schema_group_ro = schema +'_ro'          
        queries.append(
            "ALTER DEFAULT PRIVILEGES FOR USER {} in SCHEMA {} Revoke ALL ON tables FROM GROUP {};".format(
                username, schema, schema_group_ro))
        queries.append(
            "ALTER DEFAULT PRIVILEGES FOR USER {} in SCHEMA {} Revoke ALL ON tables FROM GROUP {};".format(
                username, schema, schema_group_rw))


    ticket_comments.append('Revoke DEFAULT PRIVILEGES for user.')


    return queries, ticket_comments

def exec_query(sql_string, parameters=[]):
    return cur.execute(sql_string, parameters)

def query_log(string):
    if string =="": return False

    with open(query_filename,'a') as fp:
        fp.write(str(datetime.datetime.now()) + ": " + string+'\n')

def execute_queries():
    global queries, ticket_comments, schema

    # pprint(queries)
    print('---Queries to execute:')
    for q in queries:
        print(q)

    ans = input('Execute queries? [Y/n]')
    if ans.lower() == 'n':
        nxt_ins = input('Move to Next Instance? [Y/n]')
        if nxt_ins.lower() == 'y':
            choose_action()    
        else:    
            sys.exit("Not executing queries, bye!")

    for q in queries:
        try:
            res = exec_query(q)
            print('executed query: {}'.format(q))
            if res is not None:
                print(res)
            query_log('in `{}` EXECUTED `{}`'.format(configuration['dbname'], q))
        except:
            query_log('in `{}` ERROR executing `{}` "{}"'.format(configuration['dbname'], q, sys.exc_info()))
            print("There was an error: {}".format(sys.exc_info()))
            print('Query with error: {}'.format(q))
            input('Continue? (ctrl-c to cancel, enter to continue)')

    if len(ticket_comments) > 0:
        ticket_comments.append('------------')
        ticket_comments.append('Endpoint: `{}`'.format(configuration['host']))
        ticket_comments.append('Database name: `{}`'.format(configuration['dbname']))
        ticket_comments.append('Schema name: `{}`'.format(schema))
        print("---TICKET COMMENTS---")
        print("\n".join(ticket_comments))

def choose_conf():
    c=0
    for conf in redshift_endpoints:
        print("{}) {} ({})".format(c, conf['name'], conf['host']))
        c+=1

    resp = input('what configuration you want to use?')

    if int(resp) > len(redshift_endpoints)-1:
        print("Error: configuration not found")

        sys.exit()

    return redshift_endpoints[int(resp)]

def connect():
    db_name = configuration['dbname']
    db_host = configuration['host']
    db_user = configuration['username']
    db_pw = configuration['password']

    conn = psycopg2.connect(
            "dbname='{dbname}' host='{dbhost}' port='5439' user='{username}' \
            password='{password}'".format(dbname=db_name, dbhost=db_host, username=db_user,password=db_pw)
    )
    conn.set_session(autocommit=True)
    cur = conn.cursor()

    return conn, cur

def fetch_data(sql_string, parameters=[]):
    print('sql :',sql_string )
    print('\n psql :', parameters)

    cur.execute(sql_string, parameters)
    colnames = tuple([desc[0] for desc in cur.description])
    data = list(cur)
    print(data)
    return list(data), colnames

def pick_group(
    only_groups=False,
    message='Choose a group to drop user. (you can include many groups separated by `,` i.e. 1,2,6,8: ',
    **kwargs):
    global user_id, group_rows
    index = 0
    print('\n\n---------- All Groups in `{}`------------'.format(configuration['name']))
    #all_groups, colnames = fetch_data('SELECT * FROM pg_group order by groname; ')
    #for d in all_groups:
    #    groups.append(d[0])
    #    group_rows.append(d)
    #    print('{}) {}'.format(index, d[0]))
    #    index += 1
    
    
    if only_groups is False:
        if kwargs['username']:
            print('\n\n---------- User group of `` in `{}`------------'.format(kwargs['username'],
                                                                               configuration['name']))
            query = "SELECT * FROM pg_group where (SELECT usesysid FROM pg_user WHERE " \
                    "usename = %s) = ANY(grolist) ;"
            user_groups, colnames = fetch_data(query, [kwargs['username']])
            groups=[]
            group_rows=[]
            for d in user_groups:
                groups.append(d[0])
                group_rows.append(d)
                print('{}) {}'.format(index, d[0]))
                index += 1
    
    group_ans = input(message)
    if not group_ans:
        return None, []
    try:
        group_idx = int(group_ans)
        group = group_rows[group_idx][0]
        group_list = [group]
    except ValueError:
        group = False
        group_list = [group_rows[int(g.strip())][0] for g in group_ans.split(',')]

    return group, group_list

def shuffle_names(name):
    names = []
    name_split = name.split(" ")
    name = name_split[0][0]+'%'
    names.append(name)
    for i in range(1,len(name_split)):
        name += name_split[1][0]+'%'
        names.append(name)

    return names

def pick_user(name=""):
    if not name:
        name = input("Input some letters to find a username: ")
    shuffled_names = shuffle_names(name)
    # search users on configuration
    index = 0
    usernames = []
    user_rows = []
    #print('for shuffle_name : ',shuffled_names)
    for sn in shuffled_names:
        print('\n\n---------- Names with `{}`------------'.format(sn))
        data, colnames = fetch_data('SELECT * FROM pg_user WHERE usename like %s ORDER BY usename;', [sn])

        for d in data:
            usernames.append(d[0])
            user_rows.append(d)
            print('{}) {}'.format(index, d[0]))
            index += 1
    user_name_idx = input('Choose username (enter to search again): ')
    if not user_name_idx:
        pick_user()
    create_user = False
    try:
        user_name_idx = int(user_name_idx)
        username = user_rows[user_name_idx][0]
        user_id = user_rows[user_name_idx][1]
    except ValueError:
        username = user_name_idx
        if re.search(",", username):
            username, password = username.split(",")

        #user_id = 'create new user'
        #create_user = True

    print('User `{}`, id `{}` selected'.format(username, user_id))

    return username, create_user

def choose_action():
    global configuration ,queries, group, group_list, schema
    global conn,cur
    global chk_owner,chk_owner_table_list 
    global user_flg
    
    user_flg = 0
    name = input("Enter user name to drop : ")

    if name == "":
        if queries == []:
            return
    else:
       c=0 
       for conf in redshift_endpoints:
            print("{}) {} ({})".format(c, conf['name'], conf['host']))
            c+=1
        
    resp = input('what configuration you want to use?')

    if int(resp) > len(redshift_endpoints)-1:
        print("Error: configuration not found")
        sys.exit()
    else:
        configuration = redshift_endpoints[int(resp)]
        conn, cur = connect()
        print('call pick_user function():')
        username, create_user = pick_user(name)
        
        user_flg +=1 
        group = ""
        group_list = []
        chk_owner = ""
        chk_owner_table_list = []

        chk_owner,chk_owner_table_list = check_tableowner(username)

        print ('\nTable ownership belongs to this user',chk_owner)

        if not chk_owner and not chk_owner_table_list:
            print ('\nNo table ownership belongs to this user')
            #choose_action()
            #sys.exit()
        else:
            new_ownername = input("Please enter valid user to transfer : ")

            if name == "":
                if queries == []:
                    return
            else:
                new_ownername, create_user = pick_user(new_ownername)

                for chk_owner_ans in chk_owner_table_list:
                    schema_table = chk_owner_ans[0]
                    schema_table_list = chk_owner_ans[2]        
                    #print ("alter table",[schema_table],".", [schema_table_list],"owner to " ,[new_ownername])
                    queries.append("alter table "+schema_table+"."+schema_table_list+" owner to "+new_ownername )
                    #owner_ans=owner_ans+1
        
        print('\n\n---------- Revoke Priviliges from Groups Starts ------------')
        
        if user_flg > 0:    
            group, group_list = pick_group(username=username)

            if not group and not group_list:
                print('\nNo group selected. Restarting.')
                choose_action()
                sys.exit()

            if group_list is []:
                group_list = [group]

            print('Group `{}` selected'.format(group_list))
            print('Group len`{}` selected'.format(len(group_list)))
            gfpcnt=0
            for group in group_list:       
                while True :
                    # todo: determine if selected group is rw (from cache) and add DEFAULT PRIVILEGES query automatically
                    schema_idx = input('Choose a schema for revoke  default privileges (y/n) (will continue asking if `y`)?')
                    if schema_idx == "y":
                        q, c = queries_default_privileges(username,group)
                        #queries.append(q)
                        #ticket_comments.append(c)
                        queries.append("ALTER GROUP "+group+" DROP USER "+username)
                        #queries.append("DROP USER "+username)
                        ticket_comments.append('User dropped `{}` from group `{}`.'.format(username, group))
                        break
                    elif schema_idx == "n":
                        #ticket_comments.append(c)
                        queries.append("ALTER GROUP "+group+" DROP USER "+username)
                        ticket_comments.append('User dropped `{}` from group `{}`.'.format(username, group)) 
                        break                       
                    else:
                       break

                print('group end :',group)

        ans = input('Work with other user? [y/N]')

        if ans.lower() == 'y':
            del username
            del schema 
            del group
            group_rows == []
            choose_action()
            c+=1
        else:            
            execute_queries()
            print ("---end---")
            

choose_action()
print ('---code end --')
conn.close()