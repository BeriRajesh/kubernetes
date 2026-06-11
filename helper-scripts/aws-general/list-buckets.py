""" Writes CSV file with the list of buckets and other columns like
location, agency, client, project.

Can also write the bucket policies for the buckets

"""

import argparse
import sys
import os

try:
    from tqdm import tqdm
    import pandas as pd
except:
    print('Please install tqdm: pip3 install tqdm pandas')
    sys.exit(1)
import boto3
import json
#from pprint import pprint
#import re

EXPORT_BUCKET_POLICIES = True

s3 = boto3.client('s3')

def get_args():
    parser = argparse.ArgumentParser(description='Description')

    # parser.add_argument("-n", "--name", default=None,
    #                 help="Name of ...")

    # parser.add_argument("-d", "--debug_options", action='store_true',
    #                 help="Debug options passed and exit")

    args = parser.parse_args()

    # if not any(vars(args).values()):
    #     parser.parse_args(['--help'])
    #     # parser.error('No arguments provided.')

    # if args.debug_options:
    #     print(args)
    #     sys.exit()

    return args

def get_bucket_dictionary(bucket_name):
    """ Returns bucket dictionary"""

    bucket_dict = {}

    bucket_dict["Name"] = bucket_name

    try:
        location = s3.get_bucket_location(
            Bucket=bucket_name
        )['LocationConstraint']

        if not location:
            location = "us-east-1"

        bucket_dict["Location"] = location
    except:
        bucket_dict["Location"] = '-'

    try:
        tags = s3.get_bucket_tagging(
            Bucket=bucket_name
        )['TagSet']

        for tag in tags:
            key, value = tag.items()
            if key[1] == "Environment":
                bucket_dict["Enviroment"] = value[1]
            if key[1] == "Project":
                bucket_dict["Project-tag"] = value[1]
                if len(value[1].split("-")) == 3:
                    agency, client, project = value[1].split("-")
                    bucket_dict["Agency"] = agency
                    bucket_dict["Client"] = client
                    bucket_dict["Project"] = project
    except Exception as e:
        tqdm.write(f"Buckket {bucket_name} gave error {e.response['Error']['Code']}")

    if len(bucket_name.split("-")) == 3:
        agency, client, project = bucket_name.split("-")
        bucket_dict["Agency"] = agency
        bucket_dict["Client"] = client
        bucket_dict["Project"] = project

    return bucket_dict

def get_buckets():
    """ Returns bucket list """

    buckets = s3.list_buckets()
    return [b["Name"] for b in buckets["Buckets"]]

def export_bucket_policy(bucket_name):
    """ writes to policies/bucket_name.json the bucket policy for the bucket """

    response = {}
    response = s3.get_bucket_policy(
        Bucket=bucket_name
    )

    return response.get('Policy')

def main():
    """Writes csv of bucket descriptions"""

    buckets_description = []

    buckets = get_buckets()
    for bucket in tqdm(buckets):
        bucket_dictionary = get_bucket_dictionary(bucket)
        buckets_description.append(bucket_dictionary)
        if EXPORT_BUCKET_POLICIES:
            # configure the folder relating to the current default (environment) role
            dirname = f"bucket_policies_emea_root/{bucket_dictionary['Location']}"
            os.makedirs(dirname, exist_ok=True)
            try:
                policy_json = export_bucket_policy(bucket)
                if policy_json:
                    json.dump(json.loads(policy_json), open(f"{os.path.join(dirname, bucket)}.json", 'w'), indent=4, default=str)
                else:
                    tqdm.write(f"Bucket {bucket} gave error 'NoSuchBucketPolicy'. Ignoring.")
            except Exception as e:
                if e.response['Error']['Code'] == 'AccessDenied':
                    tqdm.write(f"Bucket {bucket} gave error 'NoSuchBucketPolicy'. Ignoring.")
                if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                    tqdm.write(f"Bucket {bucket} gave error 'NoSuchBucketPolicy'. Ignoring.")

    df = pd.DataFrame(buckets_description)

    df.to_csv('buckets.csv', index=False)





if __name__ == "__main__":
    args = get_args()

    main()