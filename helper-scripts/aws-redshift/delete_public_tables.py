#!/usr/bin/env python3

"""Delete tables from public schemas"""

import psycopg2
from redshift_conf import redshift_endpoints


def connect(configuration):
    """Connect to database

    Arguments:
        configuration {object} -- from redshift_conf.py. Contains all keys necessary for connection

    Returns:
        connection, cursor
    """

    db_name = configuration['dbname']
    db_host = configuration['host']
    db_user = configuration['username']
    db_pw = configuration['password']

    conn = psycopg2.connect(
        "dbname='{dbname}' host='{dbhost}' port='5439' user='{username}' "
        "password='{password}'".format(
            dbname=db_name, dbhost=db_host, username=db_user, password=db_pw)
    )
    conn.set_session(autocommit=True)
    cur = conn.cursor()

    return conn, cur


def fetch_data(sql_string, cursor, parameters=None):
    """Fetch data after executing sql_string

    Arguments:
        sql_string {str} -- sql statement to execute

    Keyword Arguments:
        parameters {list} -- parameter required by the sql statement

    Returns:
        list, tuple -- a list of rows, a tuple of column names
    """


    # print(sql_string)
    cursor.execute(sql_string, parameters)
    colnames = tuple([desc[0] for desc in cursor.description])

    data = list(cursor)

    return list(data), colnames


def main(configuration):
    """Main function that triggers the table deletion"""

    _, cur = connect(configuration)

    stm = "SELECT schemaname, tablename FROM pg_tables WHERE schemaname like '%_public';"

    deleted = 0
    data, _ = fetch_data(stm, cursor=cur)

    for row in data:
        drop_table = "DROP TABLE {}.{} CASCADE;".format(row[0], row[1])
        cur.execute(drop_table)
        deleted += 1

    print("Deleted {}/{} tables".format(deleted, len(data)))

if __name__ == '__main__':
    CONFIGURATION = next((item for item in redshift_endpoints if item["dbname"] == "dsdk"))
    main(CONFIGURATION)
