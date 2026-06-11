#!/usr/bin/env python3

"""
Helper script that cycle through redshift connections (redshift_conf.py) and executes an SQL file
"""
import argparse
import glob
import os
import subprocess
import sys
import textwrap
import time
import re

import pymssql
from db_conf import db_endpoints
from users_conf import users_conf


def get_args():
    """Get arguments for script"""
    parser = argparse.ArgumentParser(
        description='Executes hard coded commands to create/drop users')

    parser.add_argument("action", choices=['create', 'drop'],
                        help="Create or drop configured users")

    parser.add_argument("-u", "--user", default='all',
                        help="Limit the script to work with a specified user (must exist in user configuration file")

    parser.add_argument("-n", "--dry-run", action='store_true',
                        help="Prints the queries to stdout instead of executing it.")

    parser.add_argument("-c", "--connection",
                        help="Only run on specified connection, by name as "
                             "specified in db_conf.py. Ex: -c adedev")

    # parser.add_argument("-y", "--assume-yes", action="store_true",
    #                     help="Only run on specified connection, by name as "
    #                          "specified in db_conf.py. Ex: -c adedev")

    args = parser.parse_args()

    # print(args)
    # sys.exit()
    return args


def connect(configuration):
    db_name = configuration['dbname']
    db_host = configuration['host']
    db_user = configuration['username']
    db_pw = configuration['password']

    conn = pymssql.connect(
        "dbname='{dbname}' host='{dbhost}' port='5439' user='{username}' \
        password='{password}'".format(dbname=db_name, dbhost=db_host, username=db_user, password=db_pw), autocommit=True
    )
    # conn.set_session(autocommit=True)
    cur = conn.cursor()

    return conn, cur


class SafeDict(dict):
    """Default class for using in 'format_map' and avoid missing key error"""

    def __missing__(self, key):
        return '{' + key + '}'


def create_users(*, configuration):
    """
    Executes command in connection to create users

    Arguments:
        configuration: dictionary with host, username, password, dbname keys
        and corresponding values to make connection
    """

    conn = pymssql.connect(server=configuration["host"], user=configuration["username"], password=configuration["password"], autocommit=True)
    cursor = conn.cursor()
    for user_conf in users_conf:
        if args.user != "all" and args.user != user_conf["username"]:
            continue

        user = user_conf["username"]
        passwd = user_conf["password"]

        if args.action == 'create':
            general_user_sql = textwrap.dedent(
                f"CREATE LOGIN [{user}] WITH PASSWORD = '{passwd}',"
                "DEFAULT_DATABASE=[master], CHECK_EXPIRATION=OFF,"
                "CHECK_POLICY=ON")
            db_user_sql = textwrap.dedent(
                f"CREATE USER [{user}] FOR LOGIN [{user}];"
                "EXEC sp_addrolemember ''db_datareader'', [{user}];"
                "EXEC sp_addrolemember ''db_datawriter'', [{user}]")
        elif args.action == 'drop':
            general_user_sql = f"DROP LOGIN [{user}]"
            db_user_sql = f"DROP USER [{user}]"
        else:
            sys.exit(
                "Error: action must be drop or create."
                "(Also, you shouldnt be seeing this error")

        mssql_script = textwrap.dedent(
            f"""
            Use master

            IF NOT EXISTS(select * from sys.server_principals where name = '{user}') BEGIN
                -- create/drop a server login first
                {general_user_sql}
            END

            DECLARE @dbname VARCHAR(50)
            DECLARE @statement NVARCHAR(max)

            DECLARE @use_statement NVARCHAR(max)

            DECLARE db_cursor CURSOR
            LOCAL FAST_FORWARD
            FOR
            SELECT name
            FROM MASTER.dbo.sysdatabases
            WHERE name NOT IN ('master', 'model', 'msdb', 'tempdb', 'distribution', 'rdsadmin')
            OPEN db_cursor
            FETCH NEXT FROM db_cursor INTO @dbname
            WHILE @@FETCH_STATUS = 0
            BEGIN

            BEGIN TRY
                SELECT @statement = 'use ' + @dbname +'; {db_user_sql}'
                exec sp_executesql @statement
            END TRY
            BEGIN CATCH
                select DB_Name()
            END CATCH;

            FETCH NEXT FROM db_cursor INTO @dbname
            END
            CLOSE db_cursor
            DEALLOCATE db_cursor
            """)

        if args.dry_run:
            print(mssql_script)
            print("------------------------")
        else:
            cursor.execute(mssql_script)


if __name__ == '__main__':
    # try:
    #     PSQL = subprocess.check_output("which psql", shell=True).decode().strip()
    #     print("Using `psql` in: {}".format(PSQL))
    # except subprocess.CalledProcessError:
    #     sys.exit('Please install `psql` utility in your path.')

    start_time = time.time()
    args = get_args()

    # in this path_files we have the .sql files we want to execute
    # PATH_FILES = args.path_files

    # # making sure we have a list of files to process
    # if os.path.isdir(PATH_FILES):
    #     FILES = sorted(glob.glob(os.path.join(PATH_FILES, "*.sql")))
    # elif os.path.isfile(PATH_FILES):
    #     FILES = [PATH_FILES]
    # else:
    #     sys.exit("Invalid path {}".format(PATH_FILES))

    for rs in db_endpoints:
        if args.connection is not None and rs["name"] != args.connection:
            print("Skipping connection `{}`".format(rs["name"]))
            continue

        print("Executing commands in database `{}`".format(rs["name"]))

        create_users(configuration=rs)
        # break

        # sys.exit()
