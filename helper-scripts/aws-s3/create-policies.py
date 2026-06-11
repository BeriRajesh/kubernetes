#!/usr/bin/env python3

import boto3
from botocore.exceptions import ProfileNotFound
import getopt
from pprint import pprint
import re
import subprocess
import sys
import uuid

# global uuid to uniquely name the Welcome file
uuid = uuid.uuid1()

# global session variable
boto3_session = None

# regex to validate bucket names
valid_chars_regex = re.compile("[a-zA-Z0-9\-]+")  # regex to validate bucket names
valid_chars_directory_regex = re.compile("[a-zA-Z0-9\-/]+")


def main():
    global boto3_session

    verbose = False
    bucket_name = ""
    directory = ""

    try:
        profile_name = 'default'
        region = "us-east-1"
        # parse CLI options
        opts, argvs = getopt.getopt(sys.argv[1:], "hp:vb:d:f:", ["help", "profile=", "verbose", "bucket=", "directory=", "fullname="])
        config_fullpath = ""
        fullname = None
        for option, argument in opts:
            if option in ("-p", "--profile"):
                profile_name = argument
            elif option in ("-r", "--region"):
                region = argument
            elif option in ("-v", "--verbose"):
                verbose = True
            elif option in ("-b", "--bucket"):
                bucket_name = argument
            elif option in ("-d", "--directory"):
                directory = argument
            elif option in ("-f", "--fullname"):
                fullname = argument
            elif option in ("-h", "--help"):
                raise getopt.GetoptError('help')
    except getopt.GetoptError as err:
        print(
            """
            Please use as:
            $ ./create-policies.py [options]

            Possible options are:
                -f, --fullname <full name>              ex: bucketname/folder/name
                -p, --profile <profile>                 aws profile to use
                -b, --bucket <bucket_name>              name of the bucket
                -d, --directory <directoty/name>        directory (path) inside bucket
                -h, --help                              this help
            """
        )
        raise(err)
        sys.exit(2)

    try:
        # print(profile_name)
        boto3_session = boto3.session.Session(profile_name=profile_name, region_name=region)
    except ProfileNotFound as e:
        profile_name = input(
            'The profile `' + profile_name + '` could not be found. Please input the name of a profile to use ['
                                             'default]: ')
        if profile_name == "":
            profile_name = 'default'

    # regex while...
    # while bucket_name is None:
    #     bucket_name input()

    if fullname is not None:
        folder_split = fullname.split("/")
        bucket_name = folder_split[0]
        directory = "/".join(folder_split[1:])
        print(f"-f: {fullname}")
        print(f"bucket: {bucket_name}")
        print(f"path: {directory}")

    while bucket_name is "" or not valid_chars_regex.match(bucket_name):
        bucket_name = input('Enter "bucket_name" (no spaces or special chars. allowed): ')

    while directory is "" or not valid_chars_directory_regex.match(directory):
        if fullname is not None:
            directory = "/"
        else:
            directory = input('Enter "directory" (path/to/folder) (no spaces or special chars. allowed): ')

    permission_types = ['readOnly', 'readWrite', 'listOnly']

    # check if bucket exists
    # TODO: check if bucket exists

    for permission_type in permission_types:
        policy = create_policy(bucket_name, directory, permission_type)

        # deprecating creation of groups
        # if policy is None:
        #     continue

        # policy_arn = policy['Policy']['Arn']
        # group_name = policy['Policy']['PolicyName']

        # created = create_group(group_name)
        # if created is not None:
        #     print("Attaching policy `{}` to group `{}`".format(group_name, group_name))
        #     attach_policy(policy_arn, group_name)
        # else:
        #     print("Not attaching policy because there is no group name.")


def get_policy_wholebucket_readOnly(bucket_name, directory):
    directory = re.sub('[/]+$', '', directory)
    directory = re.sub('^[/]+', '', directory)

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
            "Resource": "arn:aws:s3:::{}"
        }},
        {{
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::{}/*"
            ]
        }}
    ]
}}""".format(bucket_name, bucket_name)

    return policy_readonly

def get_policy_wholebucket_listOnly(bucket_name, directory):
    directory = re.sub('[/]+$', '', directory)
    directory = re.sub('^[/]+', '', directory)

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
            "Resource": "arn:aws:s3:::{}"
        }}
    ]
}}""".format(bucket_name)

    return policy_readonly


def get_policy_wholebucket_readWrite(bucket_name, directory):
    directory = re.sub('[/]+$', '', directory)
    directory = re.sub('^[/]+', '', directory)

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
            "Resource": "arn:aws:s3:::{}"
        }},
        {{
            "Effect": "Allow",
            "Action": [
                "s3:AbortMultipartUpload",
                "s3:DeleteObject",
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::{}/*"
            ]
        }}
    ]
}}""".format(bucket_name, bucket_name)

    return policy_readWrite

def get_policy_folder_readOnly(bucket_name, directory):
    directory = re.sub('[/]+$', '', directory)
    directory = re.sub('^[/]+', '', directory)

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
            "Resource": "arn:aws:s3:::{}",
            "Condition": {{
                "StringLike": {{
                    "s3:prefix": [
                        "{}/*"
                    ]
                }}
            }}
        }},
        {{
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::{}/{}/*"
            ],
            "Condition": {{}}
        }}
    ]
}}""".format(bucket_name, directory, bucket_name, directory)

    return policy_readonly

def get_policy_folder_listOnly(bucket_name, directory):
    directory = re.sub('[/]+$', '', directory)
    directory = re.sub('^[/]+', '', directory)

    policy_listonly = """{{
    "Version": "2012-10-17",
    "Statement": [
        {{
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:ListBucketMultipartUploads"
            ],
            "Resource": "arn:aws:s3:::{}",
            "Condition": {{
                "StringLike": {{
                    "s3:prefix": [
                        "{}/*"
                    ]
                }}
            }}
        }}
        ]
    }}""".format(bucket_name, directory)

    return policy_listonly


def get_policy_folder_readWrite(bucket_name, directory):
    directory = re.sub('[/]+$', '', directory)
    directory = re.sub('^[/]+', '', directory)

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
            "Resource": "arn:aws:s3:::{}",
            "Condition": {{
                "StringLike": {{
                    "s3:prefix": [
                        "{}/*"
                    ]
                }}
            }}
        }},
        {{
            "Effect": "Allow",
            "Action": [
                "s3:AbortMultipartUpload",
                "s3:DeleteObject",
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::{}/{}/*"
            ],
            "Condition": {{}}
        }}
    ]
}}""".format(bucket_name, directory, bucket_name, directory)

    return policy_readWrite


def create_policy(bucket_name, directory, permission_type):
    global boto3_session
    iam = boto3_session.client('iam')

    # removing trailing or initial "/"
    bucket_name = re.sub("^/*|/*$", "", bucket_name.strip())
    directory = re.sub("^/*|/*$", "", directory.strip())

    try:
        response = None
        if directory == "":
            policy_name = "{}-{}".format(bucket_name, permission_type)
        else:
            policy_name = "{}-{}-{}".format(bucket_name, re.sub('/', '-', directory), permission_type)

        policy_name = policy_name.replace(" ", "_")
        if input('Create policy {}? [N/y] '.format(policy_name)) != "y":
            print("Not creating policy.")
            return None

        # getting policy dynamically
        if directory == "":
            # whole bucket policy
            policy_type = "wholebucket"
        else:
            # folder policy
            policy_type = "folder"
        policy = globals()[f'get_policy_{policy_type}_{permission_type}'](bucket_name, directory)

        print("Creating folder policy `{}`".format(policy_name))
        response = iam.create_policy(
            PolicyName=policy_name,
            PolicyDocument=policy
        )
        pprint(response)

    except iam.exceptions.EntityAlreadyExistsException:
        answer = ""
        while answer is "" or not re.match("[nN]", answer):
            answer = input('\nError: Policy already exist. Continue? [Y/n]: ')
            if answer.lower() == 'n':
                sys.exit()
            else:
                break
    finally:
        pass
        ans = input('Upload file to bucket [N/y]? ')
        if ans == "y":
            subprocess.check_call(f"aws s3 cp Welcome s3://{bucket_name}/{directory}/Welcome-{uuid} --sse", shell=True)
            print(f"Welcome file uploaded to s3://{bucket_name}/{directory}/")


    return response


def create_group(group_name):
    global boto3_session
    iam = boto3_session.client('iam')

    group_arn = "arn:aws:s3:::{}".format(group_name)
    try:
        if input('Create group {}? [N/y] '.format(group_name)) != "y":
            print("Not creating group.")
            return None

        print("Creating group `{}`".format(group_name))
        response = iam.create_group(
            Path='/' + group_arn + '/',
            GroupName=group_name
        )
        print("\nResponse from AWS was:")
        pprint(response)
        return group_name
    except iam.exceptions.EntityAlreadyExistsException:
        answer = ""
        while answer is "" or not re.match("[nN]", answer):
            answer = input('\nError: Group already exist. Continue? [Y/n]: ')
            if answer.lower() == 'n':
                sys.exit()
            else:
                break


def attach_policy(policy_arn, group_name):
    global boto3_session
    iam_res = boto3_session.resource('iam')

    if policy_arn is None or group_name is None:
        print("Not attaching policy to group, because policy=`{0}` and group_name=`{1}`."
              .format(policy_arn, group_name))
        return None

    print("Attaching policy `{}` to group `{}`".format(policy_arn, group_name))
    group = iam_res.Group(group_name)
    response = group.attach_policy(
        PolicyArn=policy_arn
    )
    print("\nResponse from AWS was:")
    pprint(response)

    return True


if __name__ == "__main__":
    # execute only if run as a script
    main()
