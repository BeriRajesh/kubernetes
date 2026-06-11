#!/usr/bin/env python3

"""
Helper script that cycle through redshift connections (redshift_conf.py) and executes an SQL file
"""
import argparse
import glob
import os
import subprocess
import sys
import time
import re

import psycopg2
from redshift_conf_cycle import redshift_endpoints


def get_args():
    """Get arguments for script"""
    parser = argparse.ArgumentParser(
        description='Executes .sql files found in --path_files on all configured redshift instanes')

    parser.add_argument("-n", "--name",
                        help="Only execute specific files in the cluster " \
                             "(`name` parameter in redshift_conf.py)")
    parser.add_argument("-p", "--path_files", required=True,
                        help="Only execute specific files (or contents of dir)")

    parser.add_argument("-c", "--connection",
                        help="Only run on specified connection, by name as " \
                            "specified in redshift_conf.py. Ex: -c adedev")

    parser.add_argument("-y", "--assume-yes", action="store_true",
                        help="Only run on specified connection, by name as " \
                        "specified in redshift_conf.py. Ex: -c adedev")

    args = parser.parse_args()

    # print(args)
    # sys.exit()
    return args


def connect(configuration):
    db_name = configuration['dbname']
    db_host = configuration['host']
    db_user = configuration['username']
    db_pw = configuration['password']

    conn = psycopg2.connect(
        "dbname='{dbname}' host='{dbhost}' port='5439' user='{username}' \
        password='{password}'".format(dbname=db_name, dbhost=db_host, username=db_user, password=db_pw)
    )
    conn.set_session(autocommit=True)
    cur = conn.cursor()

    return conn, cur


class SafeDict(dict):
    """Default class for using in 'format_map' and avoid missing key error"""

    def __missing__(self, key):
        return '{' + key + '}'


def process_file(*, configuration, file):
    """
    Uses the psql shell command to execute contents of file in `configuration`.
    `psql` must be present in system.

    TODO: allow ports other than 5439

    Arguments:
        configuration: dictionary with host, username, password, dbname keys
        and corresponding values to make connection
        file: path/to/file whose contents are goind to be executed in `connection`
    """

    if not os.path.isfile(file):
        print("Warning: not a valid file {}".format(file))
        return False

    print("Connection `{}` - Processing file `{}`".format(configuration["name"], file))

    while True:
        try:
            command = "PGPASSWORD='{password}' psql -U {username} -h {host} " \
                      "-d {dbname} -p {port} -f {file}".format_map(
                {
                    "username": configuration["username"],
                    "host": configuration["host"],
                    "dbname": configuration["dbname"],
                    "password": configuration["password"],
                    "port": "5439",
                    "file": file
                }
            )
            # print(command)
            out = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode().strip()
            relationre = re.search('relation \"(.*?)\" already exists', out)
            if relationre:
                relation = relationre.group(1)
                if len(relation) < 10:
                    args.assume_yes = False

                if args.assume_yes is not True:
                    ans = input("Relation `{}` already exists. Do you wish to `DROP VIEW admin.{}` and (R)etry, (s)kip file or (q)uit? R/s/q: ".format(relation, relation))
                else:
                    ans = "r"

                if ans == "q":
                    sys.exit('Quitting! BYE!')
                elif ans == "s":
                    print("Skipping file: `{}`".format(file))
                    return None
                else:
                    stm = "DROP VIEW admin.{};".format(relation)
                    print("Deleting view with `{}`".format(stm))
                    command = "PGPASSWORD='{password}' psql -U {username} -h {host} -d {dbname} -p {port} -c '{command}'".format_map(
                        {
                            "username": configuration["username"],
                            "host": configuration["host"],
                            "dbname": configuration["dbname"],
                            "password": configuration["password"],
                            "port": "5439",
                            "command": stm
                        }
                    )
                    print(stm)
                    out = subprocess.check_output(command, shell=True,
                    stderr=subprocess.STDOUT).decode().strip()
                    continue

            print(out)
            break
        except Exception as exc:
            error_msg = exc
            print("\n---------- ERROR ----------")
            print(error_msg)
            print("---------- ERROR ----------")


            ans = input("Do you wish to Retry/Skip/Quit? R/s/q: ")
            if ans == "q":
                sys.exit('Quitting! BYE!')
            elif ans == "s":
                print("Skipping file: `{}`".format(file))
                return None
            else:
                print("Retrying")
                continue


if __name__ == '__main__':
    try:
        PSQL = subprocess.check_output("which psql", shell=True).decode().strip()
        print("Using `psql` in: {}".format(PSQL))
    except subprocess.CalledProcessError:
        sys.exit('Please install `psql` utility in your path.')

    start_time = time.time()
    args = get_args()

    # in this path_files we have the .sql files we want to execute
    PATH_FILES = args.path_files

    # making sure we have a list of files to process
    if os.path.isdir(PATH_FILES):
        FILES = sorted(glob.glob(os.path.join(PATH_FILES, "*.sql")))
    elif os.path.isfile(PATH_FILES):
        FILES = [PATH_FILES]
    else:
        sys.exit("Invalid path {}".format(PATH_FILES))

    for rs in redshift_endpoints:
        if args.connection is not None and rs["name"] != args.connection:
            print("Skipping connection `{}`".format(rs["name"]))
            continue


        print("Executing files into database `{}`".format(rs["name"]))

        for file in FILES:
            process_file(file=file, configuration=rs)

        # sys.exit()
