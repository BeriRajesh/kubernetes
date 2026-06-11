""" process csv of aws keys with columns
    ```type,aws key,location,comment,environment,db host,database,table,server ip```
"""
import argparse
import sys
import botocore
from botocore.exceptions import ClientError

import pandas as pd
import boto3
import json
from pprint import pprint
#import re

def get_args():
    parser = argparse.ArgumentParser(description='Description')

    parser.add_argument("-f", "--file", default=None,
                    help="Filename to process")

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
    """ process the file """
    fname = args.file
    df = pd.read_csv(fname)
    df['username'] = ''
    df['key status'] = ''
    df['last used'] = ''


    dfu = df['aws key'].unique().copy()

    iam = boto3.client('iam')
    iam_res = boto3.resource('iam')

    for key in dfu: 
        try:
            response = iam.get_access_key_last_used(
                AccessKeyId=key
            )
            print(f'{key} found')
            access_key = iam_res.AccessKey(response['UserName'], key)
            df.loc[df['aws key'] == key, "username"] = response['UserName']
            df.loc[df['aws key'] == key, "last used"] = json.dumps(response['AccessKeyLastUsed'], default=str)
            # df.loc[df['aws key'] == key, "key status"] = access_key["status"]
        except ClientError as e:
            print(f'{key} was not found')
            df.loc[df['aws key'] == key, 'username'] = 'not found'
            continue

    df.to_csv(f"{fname}-processed.csv")
    stop = 1



if __name__ == "__main__":
    args = get_args()

    main()