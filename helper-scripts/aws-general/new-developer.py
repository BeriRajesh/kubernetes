""" script to grant required access to new developers """

import sys
import os
import psycopg2
import get_parameter_secrets
import argparse
import boto3
import re
import string
import random
import traceback

aws_host = "cluster-c488xyottj77.us-east-1.rds.amazonaws.com"

databases = {
    'dev': [
        {
            'ssmPath': '/dev/rds/',
            'hostId': 'audiencebuilder-dev',
            'port': 5432,
            'dbname': 'audience_builder',
            'groups': ['abdb_rw']
        }
    ]
}


def get_args():
    parser = argparse.ArgumentParser(description='Helper to grant access to new users')

    parser.add_argument("-e", "--email",
                    help="email of user, '.' is converted to '_' to generate db username")


    parser.add_argument("-d", "--debug_options", action='store_true',
                    help="Debug options passed and exit")

    args = parser.parse_args()

    # if not any(vars(args).values()):
    #     parser.parse_args(['--help'])
    #     # parser.error('No arguments provided.')

    if args.debug_options:
        print(args)
        sys.exit()

    return args

def randompassword():
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    size = random.randint(8, 12)
    pw = ''.join(random.choice(chars) for x in range(size))
    pw += random.choice(string.digits) + random.choice(string.ascii_lowercase) + random.choice(string.ascii_uppercase)
    return pw

def grant_database_access(db):

    # parse dbusername from email
    try:
        db_user = re.search('^(.*)@', args.email).group(1).replace('.', '_')
    except Exception:
        traceback.print_exc()
        print('ERROR: username could not be parsed from email')
        sys.exit(1)


    # setup connection info and connect
    db_password = randompassword()

    db_host = f"{db['hostId']}.{aws_host}"
    db_name = db['dbname']
    db_port = db['port']

    ssmPath = os.path.join(db['ssmPath'], db['hostId'], "admin_user")
    admin_user = get_parameter_secrets.getCredentials(ssmPath)
    ssmPath = os.path.join(db['ssmPath'], db['hostId'], "admin_password")
    admin_password = get_parameter_secrets.getCredentials(ssmPath)
    stop = 1

    conn = psycopg2.connect(
        f"dbname='{db_name}' host='{db_host}' port='{db_port}' "
        f"user='{admin_user}' password='{admin_password}'"
    )
    # conn.set_session(autocommit=True)
    conn.set_session(autocommit=False)
    cur = conn.cursor()

    groups = db['groups']
    queries = [
        {
            'query': "CREATE USER %s WITH PASSWORD %s;",
            'params': [db_user, db_password]
        }
    ]

    for group in groups:
        schema = re.search('(.*)_.*', group).groups(1)
        queries.append({
            'query': "ALTER GROUP %s ADD USER %s",
            'params': [group, db_password]
        })

        if "_rw" in group:
            queries.append({
                'query': "ALTER DEFAULT PRIVILEGES FOR USER %s in SCHEMA %s GRANT SELECT ON tables TO GROUP %s;",
                'params': [db_user, schema, f"{schema}_ro"]
            })

            queries.append({
                'query': "ALTER DEFAULT PRIVILEGES FOR USER {} in SCHEMA {} GRANT ALL ON tables TO GROUP {};",
                'params': [db_user, schema, f"{schema}_rw"]
            })

    for query in queries:
        cur.execute(query['query'], query['params'])
        print(cur.query)











if __name__ == '__main__':
    args = get_args()

    for db in databases['dev']:
        grant_database_access(db)

