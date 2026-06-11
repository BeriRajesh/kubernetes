""" Generates new keys for old keys specified in csv file """

import botocore
import pandas as pd


import argparse
import boto3
import sys
import json
from pprint import pprint


def get_args():
    parser = argparse.ArgumentParser(description='Description')

    parser.add_argument("-f", "--file", default='keys.csv',
                    help="Name of input file the list of keys to be generated, one key per line")

    parser.add_argument("-a", "--action", default='generate', choices=['generate', 'disable'],
                    help="Action to perform with the keys listed on the csv")



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

def generate_keys():
    """ generate keys """

    client = boto3.client('iam')
    keys = []
    accounts_error = []
    new_keys = []


    keysdf = pd.read_csv(args.file, names=['key'])

    for i, row in keysdf.iterrows():
        key = row["key"]
        try:
            response = client.get_access_key_last_used(
                AccessKeyId=key
            )
            # print(response)
        except botocore.exceptions.ClientError as e:
            print(f'Received error: \n\t{e}\n Might be that key does not exist, or user does not have permissions.\n')
            continue

        username = response['UserName']

        response = client.list_access_keys(
            UserName=username
        )
        keys = []
        for key in response["AccessKeyMetadata"]:
            accesskey = key['AccessKeyId']
            # print(accesskey+"|",end="")
            keys.append({
                'account': username,
                'accesskey': accesskey
            })

        if len(keys) == 2:
            print(f'ERROR: Account {username} has already two keys. Please delete one.')
            accounts_error.append({'account': username, 'keys': keys})
            continue

        old_key = keys[0]['accesskey']

        # response = input(f'Do you want to generate a new key for {username}?  [y/N]: ')

        # if response != 'y':
        #     print(f'Not creating a new key for {username}.')
        #     continue

        if username == 'adedev':
            stop = 1

        if args.action == 'generate':
            print(f'Create key for {username}')
            response = client.create_access_key(
                UserName=username
            )
        elif args.action == 'disable':
            response = client.update_access_key(
                UserName=username,
                AccessKeyId=old_key,
                Status='Inactive'
            )

        # pprint(response)

        new_key = response['AccessKey']['AccessKeyId']
        new_secret = response['AccessKey']['SecretAccessKey']

        new_keys.append({
            'username': username,
            'old_key': old_key,
            'new_key': new_key,
            'new_secret': new_secret
        })

        deleteKey = True
        if deleteKey:
            print('Deleting key')
            response = client.delete_access_key(
                UserName=username,
                AccessKeyId=new_key
            )
            # print(response)

        # input()

    print('****************************')
    pprint(new_keys)
    pd.DataFrame(new_keys).to_csv('keys-new.csv', index=False)

if __name__ == "__main__":
    args = get_args()

    generate_keys()