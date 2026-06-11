#!/usr/bin/env python3

"""Script to export users and groups from AWS Redshift """

import sys

try:
    from halo import Halo
    import psycopg2
except ImportError as e:
    print('Please install required dependencies: pip3 install halo psycopg2')
    sys.exit(e)

sys.path.append('../')
import lib.helper_functions as hf
import lib.amazon_helper as ah
from aws_redshift.redshift_conf import redshift_endpoints


def fetch_data(sql_string, parameters=[]):
    # print(sql_string)
    cur.execute(sql_string, parameters)
    colnames = [desc[0] for desc in cur.description]

    data = list(cur)

    ret = []
    for d in data:
        ret.append(dict(zip(colnames, d)))

    return ret


hf.verbose = 1
AmazonHelper = ah.AmazonHelper()
spinner = Halo()

aws_session = AmazonHelper.session()

redshift = aws_session.client('redshift')
rsclusters = redshift.describe_clusters()

users = []

# headers
users.append([
    'host',
    'dbname',
    'UserName',
    'UserId',
    'MembershipType',
    'MembershipName'
])

spinner.start('Fetching Redshift clusters')
rsclusters = redshift.describe_clusters()
spinner.succeed()

for rscluster in rsclusters['Clusters']:
    endpoint = rscluster['Endpoint']['Address']
    for configuration in redshift_endpoints:
        if configuration['host'] == endpoint:
            # hf.debug(configuration, 1)
            db_name = configuration['dbname']
            db_host = configuration['host']
            db_user = configuration['username']
            db_pw = configuration['password']
            try:
                conn = psycopg2.connect(
                        "dbname='{dbname}' host='{dbhost}' port='5439' user='{username}' \
                        password='{password}'".format(dbname=db_name, dbhost=db_host, username=db_user,password=db_pw)
                )
                conn.set_session(autocommit=True)
                cur = conn.cursor()
            except:
                print('Error connecting to {}'.format(db_name))
                continue
            hf.debug('Connected to {}'.format(db_name))
            break
    else:
        hf.debug('Endpoint {} is not configured'.format(endpoint))
        continue

    # fetching users
    q_users = "SELECT * FROM pg_user order by usename;"
    db_users = fetch_data(q_users)

    for user in db_users:
        q_user_groups = "SELECT * FROM pg_group where '{}' = ANY( grolist); ".format(user["usesysid"])
        groups = fetch_data(q_user_groups)

        for group in groups:
            users.append([
                db_host,
                db_name,
                user['usename'],
                user["usesysid"],
                'group',
                group['groname']
            ])

filename = 'users-redshift.csv'

spinner.start('Writing output file `{}`'.format(filename))
hf.write_csv(filename, users)
spinner.succeed()
