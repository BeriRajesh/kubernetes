#!/usr/bin/env python3

import datetime
import json
import psycopg2
import re
import sys
import traceback


from pprint import pprint
import string
import random

from redshift_conf import redshift_endpoints

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



def dict_merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None

    taken from: https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
    (adapted to Python3)
    """
        # pprint(dct)
        # pprint(merge_dct)
    for k, v in merge_dct.items():
        # print(k)
        if k in dct and isinstance(dct[k], dict) and isinstance(merge_dct[k], dict):
            # print('rec')
            # pprint(dct[k])
            # pprint(merge_dct[k])
            dict_merge(dct[k], merge_dct[k])
        else:
            # print('lin')
            dct[k] = merge_dct[k]

        # pprint(dct[k])
        # pprint(merge_dct[k])

def choose_conf():
    c=0
    for conf in redshift_endpoints:
        print("{}) {} ({} @ {} / {})".format(c, conf['name'], conf['username'], conf['host'], conf['dbname']))
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
    db_port = 5439
    if "port" in configuration:
        db_port = configuration["port"]

    conn = psycopg2.connect(
        "dbname='{dbname}' host='{dbhost}' port='{db_port}' user='{username}' \
            password='{password}'".format(dbname=db_name, dbhost=db_host, db_port=db_port, username=db_user,password=db_pw)
    )
    conn.set_session(autocommit=True)
    cur = conn.cursor()

    return conn, cur


def exec_query(sql_string, parameters=[]):
    try:
        r = cur.execute(sql_string, parameters)
    except Exception as error:
        # print(error)
        traceback.print_exc()
        raise

    return r


def fetch_data(sql_string, parameters=[]):
    # print(sql_string)
    cur.execute(sql_string, parameters)
    colnames = tuple([desc[0] for desc in cur.description])

    data = list(cur)

    return list(data), colnames


def randompassword():
  chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
  size = random.randint(8, 12)
  pw = ''.join(random.choice(chars) for x in range(size))
  pw += random.choice(string.digits) + random.choice(string.ascii_lowercase) + random.choice(string.ascii_uppercase)
  return pw


def shuffle_names(name):
    # names = []
    names = ["%"+namepart+"%" for namepart in name.split(" ") ]
    # name = name_split[0][0]+'%'
    # names.append(name)
    # for i in range(1,len(name_split)):
    #     name += name_split[1][0]+'%'
    #     names.append(name)

    return names


def query_log(string):
    if string =="": return False

    with open(query_filename,'a') as fp:
        fp.write(str(datetime.datetime.now()) + ": " + string+'\n')


def pick_schema():
    global schema_rows
    index = 0

    all_schemas, colnames = fetch_data("SELECT nspname FROM pg_namespace where nspname !~ 'pg_' order by nspname;")

    for d in all_schemas:
        # schemas.append(d[0])
        schema_rows.append(d)
        print('{}) {}'.format(index, d[0]))
        index += 1

    while True:
        try:
            schema_idx = input('Choose a schema for the Default Privileges: ')
            schema_idx = int(schema_idx)
            break
        except Exception as error:
            traceback.print_exc()

    schema = schema_rows[schema_idx][0]

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
        dict_merge(schema_groups, {
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
        dict_merge(schema_groups, {
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


def pick_user(name=""):
    if not name:
        name = input("Input some letters to find a username: ")
    shuffled_names = shuffle_names(name)
    # search users on configuration
    index = 0
    usernames = []
    user_rows = []
    for sn in shuffled_names:
        print('\n\n---------- Names with `{}`------------'.format(sn))
        data, colnames = fetch_data('SELECT * FROM pg_user WHERE usename like %s ORDER BY usename;', [sn])

        for d in data:
            usernames.append(d[0])
            user_rows.append(d)
            print('{}) {}'.format(index, d[0]))
            index += 1

    print("""\n\nYou can also type a username to create it\n\n""")

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

        user_id = 'create new user'
        create_user = True

    print('User `{}`, id `{}` selected'.format(username, user_id))

    return username, create_user


def queries_default_privileges(**kwargs):
    """Create DEFAULT PRIVILEGES queries

    Keyword Args:
        username (str): optionally can work with 'username' instead of choosing one

    Returns:
        updates global queries, and ticket_comments variables

    """
    global queries, ticket_comments

    if 'username' not in kwargs or kwargs['username'] == "":
        print('no username in kwargs')
        username, create_user = pick_user()
    else:
        username = kwargs['username']

    # if not schema:
    schema = pick_schema()

    schema_group_ro, schema_group_rw = determine_groups_schema(schema=schema)

    usernames_list = username.split(";")
    username_orig = username
    for _username in usernames_list:
        username = clean_username(_username)
        if configuration.get('port') == 5432:
            queries.append(
                "GRANT {} to {};".format(
                    username, configuration['username']))
        queries.append(
            "ALTER DEFAULT PRIVILEGES FOR USER {} in SCHEMA {} GRANT SELECT ON tables TO GROUP {};".format(
                username, schema, schema_group_ro))
        queries.append(
            "ALTER DEFAULT PRIVILEGES FOR USER {} in SCHEMA {} GRANT ALL ON tables TO GROUP {};".format(
                username, schema, schema_group_rw))
        queries.append(
            "ALTER DEFAULT PRIVILEGES FOR USER {} IN SCHEMA {} GRANT EXECUTE ON FUNCTIONS TO GROUP {};".format(
                username, schema, schema_group_rw))
        ticket_comments.append('Set DEFAULT PRIVILEGES for user {}.'.format(username))
    username = username_orig

    return queries, ticket_comments


def pick_group(
        only_groups=False,
        message='Choose a group to add user. (you can include many groups separated by `,` i.e. 1,2,6,8: ',
        **kwargs):
    global user_id, group_rows, group, group_list
    index = 0
    print('\n\n---------- All Groups in `{}`------------'.format(configuration['name']))
    all_groups, colnames = fetch_data('SELECT * FROM pg_group order by groname; ')
    for d in all_groups:
        groups.append(d[0])
        group_rows.append(d)
        print('{}) {}'.format(index, d[0]))
        index += 1

    if only_groups is False:
        if kwargs['username']:
            print('\n\n---------- User group of `` in `{}`------------'.format(kwargs['username'],
                                                                               configuration['name']))
            query = "SELECT * FROM pg_group where (SELECT usesysid FROM pg_user WHERE " \
                    "usename = %s) = ANY(grolist) ; "
            user_groups, colnames = fetch_data(query, [kwargs['username']])
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


def queries_reset_privileges():
    global queries, ticket_comments

    schema = pick_schema()

    schema_group_ro, schema_group_rw = determine_groups_schema(schema=schema)

    queries.append(
        "GRANT SELECT ON ALL TABLES IN SCHEMA {} TO GROUP {}".format(schema, schema_group_ro))
    queries.append(
        "GRANT ALL ON ALL TABLES IN SCHEMA {} TO GROUP {}".format(schema, schema_group_rw))
    queries.append(
        "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA {} TO GROUP {}".format(schema, schema_group_rw))

    ticket_comments.append('Reset privileges for ReadOnly and ReadWrite groups in schema `{}`.'.format(schema))

    return queries, ticket_comments


def queries_create_schema():
    global configuration, schema, queries, ticket_comments

    schema_name = input('Specify new schema name> ')

    group_ro = schema_name + '_ro'
    group_rw = schema_name + '_rw'

    queries.append('CREATE SCHEMA IF NOT EXISTS {};'.format(schema_name))
    queries.append('DROP SCHEMA public')
    queries.append('CREATE GROUP {};'.format(group_ro))
    queries.append('CREATE GROUP {};'.format(group_rw))

    queries.append('GRANT USAGE ON SCHEMA {} TO GROUP {};'.format(schema_name, group_ro))
    queries.append('GRANT SELECT ON ALL TABLES IN SCHEMA {} TO GROUP {};'.format(schema_name, group_ro))
    queries.append('REVOKE CREATE ON SCHEMA {} FROM GROUP {};'.format(schema_name, group_ro))
    queries.append('GRANT TEMPORARY ON DATABASE {} TO GROUP {}; '.format(configuration['dbname'], group_ro))

    queries.append('GRANT ALL ON SCHEMA {} TO GROUP {};'.format(schema_name, group_rw))
    queries.append('GRANT ALL ON ALL TABLES IN SCHEMA {} TO GROUP {};'.format(schema_name, group_rw))

    ticket_comments.append('Created schema `{}`, groups `{}` and `{}`, and granted privileges to groups accordingly'.
                           format(schema_name, group_ro, group_rw))

    while True:
        username = input('Please input username to grant CREATEUSER (s to skip): ')
        if username == 's':
            break

        password = randompassword()
        queries.append("CREATE USER " + username + "  WITH PASSWORD '" + password + "';")
        ticket_comments.append('Created user {}.'.format(username))

        queries.append("ALTER USER " + username + " CREATEUSER;")
        ticket_comments.append("Configuring user `{}` as superuser .".format(username))

        queries.append("ALTER GROUP " + group_rw + " ADD USER " + username)
        ticket_comments.append("Added user `{}` to group `{}`.".format(username, group_rw))

        ans = input("Create another one? [y/N]")
        if ans == "y":
            continue
        else:
            break

    return queries, ticket_comments


def execute_queries():
    global queries, ticket_comments, schema

    # pprint(queries)
    print('---Queries to execute:')
    for q in queries:
        print(q)

    ans = input('Execute queries? [Y/n]')
    if ans.lower() == 'n':
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

def clean_username(dirtyusername):
    dirtyusername = dirtyusername.split('@')[0].replace('.','_').lower()
    cleaned = re.sub('[^a-zA-Z]','_',dirtyusername)
    return cleaned

def choose_action():
    global queries, group, group_list, schema
    name = input("User complete name,"
                 "\n  enter `q` to input a custom query to the connection"
                 "\n  enter `d` to generate DEFAULT PRIVILEGES queries"
                 "\n  enter `r` to reset privileges in all tables in schema for groups"
                 "\n  enter `s` to CREATE SCHEMA, GROUPS, PRIVILEGES, etc"
                 "\n> ")

    if name == "":
        if queries == []:
            return

    elif name == 'q':
        while True:
            q = input('Issue default query command (or enter to exit loop)> ')
            if q == "": break
            try:
                res = exec_query(q)
                print('executed query: {}'.format(q))
                print(res)
                query_log('in `{}` EXECUTED `{}`'.format(configuration['name'], q))
            except:
                query_log(': in `{}` ERROR executing `{}` "{}"'.format(configuration['name'], q, sys.exc_info()[0]))
                print("There was an error: {}".format(sys.exc_info()[0]))
                input('Continue? (ctrl-c to cancel, enter to continue)')
    elif name == 'd':
        q, c = queries_default_privileges()
        # queries.append(q)
        # ticket_comments.append(c)
    elif name == 'r':
        q, c = queries_reset_privileges()
        # queries.append(q)
        # ticket_comments.append(c)
    elif name == 's':
        q, c = queries_create_schema()
    else:

        username, create_user = pick_user(name)

        group = ""
        group_list = []
        group, group_list = pick_group(username=username)

        if not group and not group_list:
            print('No group selected. Restarting.')
            choose_action()
            sys.exit()

        if group_list is []:
            group_list = [group]

        print('Group `{}` selected'.format(group_list))
        usernames_list = username.split(";")
        username_orig = username
        for _username in usernames_list:
            username = clean_username(_username)
            if create_user:
                password = randompassword()
                queries.append("CREATE USER "+username+"  WITH PASSWORD '"+password+"';")
                ticket_comments.append('Created user {}.'.format(username))

            for group in group_list:
                queries.append("ALTER GROUP "+group+" ADD USER "+username)
                ticket_comments.append('Added user `{}` to group `{}`.'.format(username, group))
        username = username_orig

        while True:
            # todo: determine if selected group is rw (from cache) and add DEFAULT PRIVILEGES query automatically
            schema_idx = input('Choose a schema for the Default Privileges (y/N) (will continue asking if `y`)?')
            if schema_idx != "y":
                print("Not creating DEFAULT PRIVILEGES queries")
                break
            else:
                q, c = queries_default_privileges(username=username)
                # queries.append(q)
                # ticket_comments.append(c)

    ans = input('Work with other user? [y/N]')

    if ans.lower() == 'y':
        # username = ""
        # schema = ""
        choose_action()
    else:
        execute_queries()


configuration = choose_conf()

conn, cur = connect()

choose_action()

print("Bye!")

conn.close()
