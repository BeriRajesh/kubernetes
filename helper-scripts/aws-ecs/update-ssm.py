""" Updates SSM with the key values for files locates in SECRETS_FOLDER

Example usage:
    python3 update-ssm.py


The script will scan ./secrets folder.
Overrides files must have this structure

$ ls secrets/
total 4
-rw-r--r-- 1 an an 1401 Jul  9 13:28 audiencebuilder-dev-serveroverride.cfg

In this case, this script read the override file's sections, keys and values and will update /dev/audiencebuilder/<section>/<key> -> value

"""

import argparse
import os
import sys
import json
import configparser
import glob
import re

from pprint import pprint

import boto3
import pylect_infra as pinfra
# try:
#     from tqdm import tqdm
#     import pandas as pd
# except:
#     print('Please install tqdm: pip3 install tqdm pandas')
#     sys.exit(1)


SECRETS_FOLDER = './secrets/'

def get_args():
    parser = argparse.ArgumentParser(description='Description')

    parser.add_argument("-a", "--app", default=None,
                    help="Only update SSM parameters for this appname ...")

    parser.add_argument("-e", "--env", default=None,
                    help="Only update SSM parameters for this environment ...")

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

def main():
    """ scans secret folder and updates SSM according to arguments """

    files = glob.glob(os.path.join(SECRETS_FOLDER, "*"))
    for filename in files:
        config = configparser.ConfigParser()
        config.read(filename)

        for section in config.sections():
            for key in config[section]:
                ssm_key = build_ssm_key(filename=filename, section=section, key=key)
                ssm_value = config[section][key]
                print(f"{ssm_key}->{ssm_value}")


                if ssm_value == '':
                    ssm_value = '_empty'

                pinfra.ssm.set_value(
                    key=ssm_key,
                    value=ssm_value,
                    no_file=True,
                    overwrite=True,
                    encrypt=True
                )
                a=1



        # content = open(file).read()
    print(files)

def build_ssm_key(section, key, filename=None, environment=None, app_name=None):
    """ build the SSM key for the parameter store following our standards """

    keyname = None
    if not filename and not (environment and app_name):
        raise Exception("Specify file or environment && appname")
    if filename and (environment and app_name):
        raise Exception("Specify only file or environment && appname")

    if filename:
        basename = os.path.basename(filename)
        matches = re.match('(.*)-(.*)-(.*)\.', basename)
        app_name = matches[1]
        environment = matches[2]

    if environment and app_name:
        keyname =f"/{environment}/{app_name}/{section}/{key}"


    return keyname.lower()



if __name__ == "__main__":
    args = get_args()

    main()