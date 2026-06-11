"""
List buckets without encryption.
Can encrypt buckets.
"""
import argparse
import sys

import pandas as pd
import boto3
import botocore
import json
from pprint import pprint
from tqdm import tqdm
#import re

# from botocore.exceptions import ServerSideEncryptionConfigurationNotFoundError

s3 = boto3.client('s3')

def get_args():
    parser = argparse.ArgumentParser(description='Description')

    parser.add_argument("action", choices=["list", "encrypt"], default=None,
                    help="List buckets without encryption")

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

def get_bucket_encryption(encrypt=False):
    client = s3
    buckets = client.list_buckets()
    bucket_encryptions = []
    for bucket in tqdm(buckets['Buckets']):
        bucket_name = bucket['Name']
        tqdm.write(bucket_name)
        bucket_encryption = {
            'bucket_name': bucket_name
        }
        try:
            response = client.get_bucket_encryption(
                Bucket=bucket_name
            )
            bucket_encryption["encryption"] = response["ServerSideEncryptionConfiguration"]
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == "ServerSideEncryptionConfigurationNotFoundError":
                if encrypt:
                    rules = {
                            'Rules': [
                                {
                                    'ApplyServerSideEncryptionByDefault': {
                                        'SSEAlgorithm': 'AES256'
                                    }
                                },
                            ]
                        }
                    response = client.put_bucket_encryption(
                        Bucket=bucket_name,
                        ServerSideEncryptionConfiguration=rules
                    )
                    if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                        stop=1
                    bucket_encryption["encryption"] = rules
                    a=1
                else:
                    bucket_encryption["encryption"] = ""
            else:
                bucket_encryption["encryption"] = error.response['Error']['Code']
                tqdm.write(f"Bucket: {bucket_name} Error: {error.response['Error']['Code']}")

        bucket_encryptions.append(bucket_encryption)

    return bucket_encryptions


def main():
    """ put your code here """

    if args.action == 'list':
        bucket_encryptions = get_bucket_encryption()
        df = pd.DataFrame(bucket_encryptions)
        fname = 'bucket_encryptions.csv'
    if args.action == 'encrypt':
        bucket_encryptions = get_bucket_encryption(encrypt=True)
        df = pd.DataFrame(bucket_encryptions)
        fnname = 'bucket_encryptions-encrypted.csv'

    df.to_csv(fname, index=False)
    print(f'Wrote {fname}!')


if __name__ == "__main__":
    args = get_args()

    main()