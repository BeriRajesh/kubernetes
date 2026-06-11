""" Use role to export iam information from EMEA account
"""
import argparse
import sys

import pandas as pd
import boto3
import json
from pprint import pprint
#import re

def get_args():
    parser = argparse.ArgumentParser(description='Description')

    parser.add_argument("-r", "--resource", choices=['iam'], default=None,
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

def get_client(client_name, account, role_name):
    # Create IAM client
    sts_default_provider_chain = boto3.client('sts')

    # print('Default Provider Identity: : ' + sts_default_provider_chain.get_caller_identity()['Arn'])

    role_to_assume_arn=f'arn:aws:iam::{account}:role/{role_name}'
    role_session_name=f'emea_admin_session_{account}'

    response=sts_default_provider_chain.assume_role(
        RoleArn=role_to_assume_arn,
        RoleSessionName=role_session_name
    )

    creds=response['Credentials']

    sts_assumed_role = boto3.client(client_name,
        aws_access_key_id=creds['AccessKeyId'],
        aws_secret_access_key=creds['SecretAccessKey'],
        aws_session_token=creds['SessionToken'],
    )

    # print('AssumedRole Identity: ' + sts_assumed_role.get_caller_identity()['Arn'])
    return sts_assumed_role

# def get_policies(item, type):
def get_policy_document(arn, iam):
    get_policy = iam.get_policy(
        PolicyArn=arn
    )

    policy_version = iam.get_policy_version(
        PolicyArn=arn,
        VersionId=get_policy['Policy']['DefaultVersionId']
    )['PolicyVersion']

    return policy_version['Document']

def get_iam():
    """ put your code here """

    roles = [
        {
            'account': '005533607590',
            'role_name': 'Admin',
            'account_name': 'Root'
        },
        {
            'account': '257841078254',
            'role_name': 'Admin',
            'account_name': 'Live'
        },
        {
            'account': '340659147180',
            'role_name': 'Admin',
            'account_name': 'Dev'
        },
    ]

    output = []

    for role in roles:
        account = role["account"]
        account_name = role["account_name"]

        print(f'Account: {account}, {account_name}')
        iam = get_client('iam', account=role['account'], role_name=role['role_name'])

        iam_type = 'user'
        response = iam.list_users()
        for item in response['Users']:
            inline_policies = iam.list_user_policies(UserName=item['UserName'])['PolicyNames']
            for policy in inline_policies:
                policy_document= iam.get_user_policy(UserName=item['UserName'], PolicyName=policy)['PolicyDocument']
                output.append({
                    'account': account,
                    'account_name': account_name,
                    'type': iam_type,
                    'type_name': item['UserName'],
                    'policy_type': 'inline',
                    'policy_name': policy,
                    'policy_document': json.dumps(policy_document, indent=4)

                })

            attached_policies = iam.list_attached_user_policies(UserName=item['UserName'])['AttachedPolicies']
            for policy in attached_policies:
                policy_document= get_policy_document(arn=policy['PolicyArn'], iam=iam)

                output.append({
                    'account': account,
                    'account_name': account_name,
                    'type': iam_type,
                    'type_name': item['UserName'],
                    'policy_type': 'managed',
                    'policy_name': policy['PolicyName'],
                    'policy_document': json.dumps(policy_document, indent=4)
                })

        iam_type = 'role'
        response = iam.list_roles()
        for item in response['Roles']:
            inline_policies = iam.list_role_policies(RoleName=item['RoleName'])['PolicyNames']
            for policy in inline_policies:
                policy_document= iam.get_role_policy(RoleName=item['RoleName'], PolicyName=policy)['PolicyDocument']
                output.append({
                    'account': account,
                    'account_name': account_name,
                    'type': iam_type,
                    'type_name': item['RoleName'],
                    'policy_type': 'inline',
                    'policy_name': policy,
                    'policy_document': json.dumps(policy_document, indent=4)

                })

            attached_policies = iam.list_attached_role_policies(RoleName=item['RoleName'])['AttachedPolicies']
            for policy in attached_policies:
                policy_document= get_policy_document(arn=policy['PolicyArn'], iam=iam)
                output.append({
                    'account': account,
                    'account_name': account_name,
                    'type': iam_type,
                    'type_name': item['RoleName'],
                    'policy_type': 'managed',
                    'policy_name': policy['PolicyName'],
                    'policy_document': json.dumps(policy_document, indent=4)
                })

        iam_type = 'group'
        response = iam.list_groups()
        for item in response['Groups']:
            inline_policies = iam.list_group_policies(GroupName=item['GroupName'])['PolicyNames']
            for policy in inline_policies:
                policy_document= iam.get_group_policy(GroupName=item['GroupName'], PolicyName=policy)['PolicyDocument']
                output.append({
                    'account': account,
                    'account_name': account_name,
                    'type': iam_type,
                    'type_name': item['GroupName'],
                    'policy_type': 'inline',
                    'policy_name': policy,
                    'policy_document': json.dumps(policy_document, indent=4)

                })

            attached_policies = iam.list_attached_group_policies(GroupName=item['GroupName'])['AttachedPolicies']
            for policy in attached_policies:
                policy_document= get_policy_document(arn=policy['PolicyArn'], iam=iam)
                output.append({
                    'account': account,
                    'account_name': account_name,
                    'type': iam_type,
                    'type_name': item['GroupName'],
                    'policy_type': 'managed',
                    'policy_name': policy['PolicyName'],
                    'policy_document': json.dumps(policy_document, indent=4)
                })

        iam_type = 's3_bucket'
        s3 = get_client('s3', account=role['account'], role_name=role['role_name'])
        response = s3.list_buckets()
        for item in response['Buckets']:
            policy_document = '{}'
            try:
                policy_document = s3.get_bucket_policy(
                    Bucket=item['Name']
                )['Policy']
            except Exception as error:
                if "NoSuchBucketPolicy" not in error.args[0]:
                    raise

            output.append({
                'account': account,
                'account_name': account_name,
                'type': iam_type,
                'type_name': item['Name'],
                'policy_type': 'bucket_policy',
                'policy_name': '',
                'policy_document': json.dumps(json.loads(policy_document), indent=4)

            })

    df = pd.DataFrame(output)
    df.to_excel('iam.xlsx', index=False)



if __name__ == "__main__":
    args = get_args()

    # get resource
    globals()[f'get_{args.resource}']()

