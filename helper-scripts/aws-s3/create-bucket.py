#!/usr/bin/env python3

import argparse
import boto3
from botocore.exceptions import ProfileNotFound
from botocore.client import ClientError
from pprint import pprint
import re
import sys
import json
import time


def get_args():
    parser = argparse.ArgumentParser(description='Helper to create S3 buckets')

    parser.add_argument("-n", "--name", default=None,
                    help="Name of the bucket when bucket")

    parser.add_argument("-r", "--region", default='us-east-1',
                        help="Name of the region where bucket is created (defaults to us-east-1)")

    parser.add_argument("-p", "--profile", default='default',
                        help="Name of the profile to use to start boto3 sessions (defaults to default)")

    parser.add_argument("-o", "--owner",
                        help="Value for the owner tag of the bucket.")

    parser.add_argument("-d", "--debug_options", action='store_true',
                    help="Debug options passed and exit")

    parser.add_argument("-y", "--yes", action='store_true',
                        help="Defaults to yes in all questions")

    parser.add_argument("-f", "--force", action='store_true',
                        help="Forces the creation of any bucket name")

    args = parser.parse_args()

    # if not any(vars(args).values()):
    #     parser.parse_args(['--help'])
    #     # parser.error('No arguments provided.')

    if args.debug_options:
        print(args)
        sys.exit()

    return args

def create_bucket(bucket_name):
    print('Checking if bucket already exist...')
    # response = s3.list_buckets()
    # buckets = [bucket['Name'] for bucket in response['Buckets']]
    # if bucket_name in buckets:
    #     answer = ""
    #     while answer is "" or not re.match("[nN]", answer):
    #         if not args.yes:
    #             answer = input('\nError: Bucket already exist. Continue? [Y/n]: ')
    #         if answer.lower() == 'n':
    #             sys.exit()
    #         else:
    #             break
    print("Creating bucket {}.".format(bucket_name))
    # creating bucket and printing response

    print(f"region: {args.region}")
    params = dict(
        Bucket=bucket_name
    )
    if args.region != 'us-east-1':
        params['CreateBucketConfiguration'] = {
            'LocationConstraint': args.region
        }

    response = s3.create_bucket(**params)
    # print("\nResponse from AWS was:")
    # pprint(response)

    # adding default security for bucket
    print('Adding default security for bucket...')
    response = s3.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
        }
    )
    # pprint(response)

    # setting default ownership
    response = s3.put_bucket_ownership_controls(
        Bucket=bucket_name,
        # ContentMD5='string',
        # ExpectedBucketOwner='string',
        OwnershipControls={
           'Rules': [
                {
                    'ObjectOwnership': 'BucketOwnerPreferred'
                },
            ]
        }
    )

    #Enforce access to the buckets only through HTTPS Secure Socket Layer (SSL)
    print('Adding bucket policy only through HTTPS Secure Socket Layer (SSL)...')

    policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ForceSSLOnlyAccess",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::"+bucket_name+"/*",
            "Condition": {
                "Bool": {
                    "aws:SecureTransport": "false"
                }
            }
        },
        {
            "Sid": "forceBucketOwnerFullControlTIO",
            "Effect": "Deny",
            "Principal": {
                "AWS": "arn:aws:iam::661095214357:root"
            },
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::" + bucket_name + "/*",
            "Condition": {
                "StringNotEquals": {
                    "s3:x-amz-acl": "bucket-owner-full-control"
                }
            }
        }
    ]
}
    time.sleep(10)
    response = s3.put_bucket_policy(
        Bucket=bucket_name,
        Policy= json.dumps(policy)
    )

    #print(response)

    print("Adding default encryption")
    response = s3.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            'Rules': [
                {
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'AES256'
                    }
                },
            ]
        }
    )
    # print("\nResponse from AWS was:")
    # pprint(response)
    print('Configuring access logging...')
    try:
        if args.region == "us-east-1":
            target_bucket = 'ann01-tioprod-s3access-logs'
        elif args.region == "eu-west-1":
            target_bucket = 'ann01-tioprod-aew1-s3access-logs'

        response = s3.put_bucket_logging(
            Bucket=bucket_name,
            BucketLoggingStatus={
                'LoggingEnabled': {
                    'TargetBucket': target_bucket,
                    'TargetPrefix': 'bucket='+ bucket_name +'/'
                }
            },

        )
    except Exception as e:
        if e.response['Error']['Code'] == 'InvalidTargetBucketForLogging':
            print(f'InvalidTargetBucketForLogging: are you sure bucket "{target_bucket}" exists?')
            print(e.args[0])
            sys.exit(1)
        elif e.response['Error']['Code'] == 'CrossLocationLoggingProhibitted':
            errored_buckets[bucket_name] = e.args[0]
            print(f"Error {bucket_name}: {e.args[0]}")
        else:
            raise

def tag_bucket(bucket_name):
    # tagging bucket
    print("Tagging bucket")
    bucket_tagging = s3_res.BucketTagging(bucket_name)
    if args.owner:
        owner_name = args.owner
    response = bucket_tagging.put(Tagging={
        'TagSet': [
            {'Key': 'Agency', 'Value': agency_name},
            {'Key': 'Client', 'Value': '{}-{}'.format(agency_name, client_name)},
            {'Key': 'Project', 'Value': '{}-{}-{}'.format(agency_name, client_name, project_name)},
            {'Key': 'Owner', 'Value': owner_name}
        ]
    })
    print("\nResponse from AWS was:")
    pprint(response)


def get_policy_readOnly(bucket_name):
    policy_readonly = """{{
    "Version": "2012-10-17",
    "Statement": [
        {{
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:ListBucketMultipartUploads"
            ],
            "Resource": "arn:aws:s3:::{0}",
            "Condition": {{}}
        }},
        {{
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::{1}/*"
            ],
            "Condition": {{}}
        }}
        ]
}}""".format(bucket_name, bucket_name)

    return policy_readonly


def get_policy_readWrite(bucket_name):
    policy_readWrite = """{{
    "Version": "2012-10-17",
    "Statement": [
        {{
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:ListBucketMultipartUploads"
            ],
            "Resource": "arn:aws:s3:::{0}",
            "Condition": {{}}
        }},
        {{
            "Effect": "Allow",
            "Action": [
                "s3:AbortMultipartUpload",
                "s3:DeleteObject",
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::{1}/*",
            "Condition": {{}}
        }}
    ]
}}""".format(bucket_name, bucket_name)

    return policy_readWrite


def create_policy(bucket_name, permission_type):
    policy_name = "{}-{}".format(bucket_name, permission_type)
    policy = globals()['get_policy_{}'.format(permission_type)](bucket_name)

    try:
        response = iam.create_policy(
            PolicyName=policy_name,
            PolicyDocument=policy
        )
        print("\nResponse from AWS was:")
        pprint(response)
        return response
    except iam.exceptions.EntityAlreadyExistsException:
        answer = ""
        while answer == "" or not re.match("[nN]", answer):
            if not args.yes:
                answer = input('\nError: Policy already exist. Continue? [Y/n]: ')
            if answer.lower() == 'n':
                sys.exit()
            else:
                break


def create_group(bucket_name, permission_type):
    group_name = "{}-{}".format(bucket_name, permission_type)
    group_arn = "arn:aws:s3:::{}".format(bucket_name)
    try:
        response = iam.create_group(
            Path='/' + group_arn + '/',
            GroupName=group_name
        )
        print("\nResponse from AWS was:")
        pprint(response)
        return response
    except iam.exceptions.EntityAlreadyExistsException:
        answer = ""
        while answer == "" or not re.match("[nN]", answer):
            print("no")
            if args.yes:
                print("si")
            if not args.yes:
                answer = input('\nError: Group already exist. Continue? [Y/n]: ')
            if answer.lower() == 'n':
                sys.exit()
            else:
                break


def attach_policy(policy_arn, group_name):
    print("Attaching policy `{}` to group `{}`".format(policy_arn, group_name))
    group = iam_res.Group(group_name)
    response = group.attach_policy(
        PolicyArn=policy_arn
    )
    print("\nResponse from AWS was:")
    pprint(response)

    return True


if __name__ == "__main__":
    args = get_args()

    # defining AWS Region to use
    print(args.region)
    if args.region is None:
        default_region = "us-east-1"
        region = input("Please input the region you wish to use [{}]: ".format(default_region))
        if region == "":
            region = default_region
    else:
        region = args.region

    print("Using region {}".format(region))

    # instantiating resources
    boto3_session = boto3.session.Session(region_name=region, profile_name=args.profile)
    s3 = boto3_session.client('s3')
    s3_res = boto3_session.resource('s3')
    iam_res = boto3_session.resource('iam')
    iam = boto3_session.client('iam')

    valid_chars_regex = re.compile("[a-zA-Z0-9]+")

    agency_name = ""
    client_name = ""
    project_name = ""
    owner_name = args.owner or ""
    if args.name:
        split_name = args.name.split('-')
        if len(split_name) == 3:
            agency_name, client_name, project_name = split_name
        elif ("emea" in split_name and len(split_name) == 4):
            agency_name, emea, client_name, project_name = split_name
            agency_name = f"{agency_name}-{emea}"
        elif args.force:
            agency_name = args.name
            client_name = project_name = ""
        else:
            sys.exit(
                'Error: option `-name` requires exactly two hyphens: agency-client-project but `{}` provided'.format(args.name))

    if not args.force:
        while owner_name == "" or not valid_chars_regex.match(owner_name):
            owner_name = input('Enter the owner name of this new Bucket that  you want to Create (no spaces or special chars. allowed): ')

        while agency_name == "" or not valid_chars_regex.match(agency_name):
            agency_name = input('Enter agency name (no spaces or special chars. allowed): ')

        while client_name == "" or not valid_chars_regex.match(client_name):
            client_name = input('Enter client name (no spaces or special chars. allowed): ')

        while project_name == "" or not valid_chars_regex.match(project_name):
            project_name = input('Enter project name (no spaces or special chars. allowed): ')

    # lowering case
    agency_name = agency_name.lower()
    client_name = client_name.lower()
    project_name = project_name.lower()
    owner_name = owner_name.lower()

    if args.force:
        bucket_name = agency_name
    else:
        bucket_name = "{0}-{1}-{2}".format(agency_name, client_name, project_name)

    while True:
        print("\nReview:")
        print("Bucket name: {}".format(bucket_name))
        print("Owner tag value: {}".format(args.owner))
        ans = "y"
        if not args.yes:
            ans = input("\nShould I proceed to creation of bucket and policies? [y/N] (press P to review policies): ")
        if not re.match('[yYP]', ans):
            print("Your answer was ``. Quitting... bye!".format(ans))
            sys.exit()

        if ans == 'P':
            print("Review:")
            print("Bucket name: {}".format(bucket_name))
            print("ReadOnly policy:{}".format(get_policy_readOnly(bucket_name)))
            print("ReadWrite policy:{}".format(get_policy_readWrite(bucket_name)))
        else:
            break

    create_bucket(bucket_name)
    tag_bucket(bucket_name)
    for permission_type in ['readOnly', 'readWrite']:
        policy = create_policy(bucket_name, permission_type)

        # deprecating creation of groups
        # group = create_group(bucket_name, permission_type)

        # if policy is not None and group is not None:
        #     answer = ""
        #     policy_arn = policy['Policy']['Arn']
        #     group_name = group['Group']['GroupName']
        #     response = attach_policy(policy_arn, group_name)
        #     print('Policy `{}` attached to group `{}`'.format(group_name, group_name))
        # else:
        #     print("Not attaching policy to  group, because policy=`{0}` and group=`{1}`.".format(policy, group))
