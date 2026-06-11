""" Enables access logging for all buckets """

import argparse
import sys

try:
    from tqdm import tqdm
    # import pandas as pd
except:
    print('Please install tqdm: pip3 install tqdm pandas')
    sys.exit(1)
import boto3
#import json
from pprint import pprint
#import re

def get_args():
    parser = argparse.ArgumentParser(description='Description')

    parser.add_argument("-n", "--name", default=None,
                    help="Name of ...")

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
    """ Enable access logging for all buckets """

    s3 = boto3.client('s3')
    target_bucket_us = 'ann01-tioprod-s3access-logs'
    target_bucket_eu = 'ann01-tioprod-aew1-s3access-logs'

    print('Fetching bucket list')
    buckets = s3.list_buckets()['Buckets']
    errored_buckets = {}
    for bucket in tqdm(buckets):
        try:
            bucket_name = bucket['Name']
            location = s3.get_bucket_location(
                Bucket=bucket_name
            )
            if location.get('LocationConstraint') and location.get('LocationConstraint')[0:2].lower != 'us':
                target_bucket = target_bucket_eu
            elif not location.get('LocationConstraint') or location.get('LocationConstraint')[0:2].lower == 'us':
                target_bucket = target_bucket_us
            else:
                print(f"ERROR: Unknown region {location.get('LocationConstraint')}")
                sys.exit()

            response = s3.put_bucket_logging(
                Bucket=bucket_name,
                BucketLoggingStatus={
                    'LoggingEnabled': {
                        'TargetBucket': target_bucket,
                        'TargetPrefix': 'bucket=' + bucket_name + '/'
                    }
                },

            )
            tqdm.write(f"{bucket_name}...OK")
        except Exception as e:
            if e.response['Error']['Code'] == 'InvalidTargetBucketForLogging':
                tqdm.write(f'InvalidTargetBucketForLogging: are you sure bucket "{target_bucket}" exists?')
                tqdm.write(e.args[0])
                sys.exit(1)
            elif e.response['Error']['Code'] == 'CrossLocationLoggingProhibitted':
                errored_buckets[bucket_name] = e.args[0]
                tqdm.write(f"Error {bucket_name}: {e.args[0]}")
            elif e.response['Error']['Code'] == 'AccessDenied':
                errored_buckets[bucket_name] = e.args[0]
                tqdm.write(f"Error {bucket_name}: {e.args[0]}")
            else:
                raise

    print('Errored buckets:')
    pprint(errored_buckets)



if __name__ == "__main__":
    # args = get_args()

    main()