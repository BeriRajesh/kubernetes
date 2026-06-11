#!/usr/bin/env python3

"""Script to export iam users, groups and policies from AWS"""

import sys
import boto3
import datetime

try:
    from tqdm import tqdm
    import pandas as pd
except ImportError as e:
    print('Please install required dependencies')
    sys.exit(e)

# update date as a security measure if you really intend to delete users
DELETE_USERS = False and str(datetime.datetime.now()) < '2020-07-30'

iam = boto3.client('iam')
paginator = iam.get_paginator('list_users')

users = []

def delete_user(username):
    """ deletes user by username """

    # get and delete access keys
    keys = iam.list_access_keys(
        UserName=username,
    )
    for key in keys.get('AccessKeyMetadata', []):
        access_key = key.get('AccessKeyId')
        try:
            iam.delete_access_key(
                UserName=username,
                AccessKeyId=access_key
            )
        except Exception as e:
            print(e)

    iam.delete_user(
        UserName=username
    )



page_iterator = paginator.paginate()

for page in tqdm(page_iterator):
    for user in tqdm(page['Users']):
        user_policies = iam.list_user_policies(UserName=user['UserName'])
        num_user_policies = len(user_policies['PolicyNames'])
        user_policies = iam.list_attached_user_policies(UserName=user['UserName'])
        num_attached_user_policies = len(user_policies['AttachedPolicies'])
        user_groups = iam.list_groups_for_user(UserName=user['UserName'])
        num_user_groups = len(user_groups['Groups'])

        if DELETE_USERS:
            if num_user_policies == 0 and num_attached_user_policies == 0 and num_user_groups == 0:
                delete_user(username=user['UserName'])
                continue

        users.append({
            "Username": user['UserName'],
            "UserId": user['UserId'],
            "CreateDate": user['CreateDate'],
            "RowType": "user",
            "NumUserPolicies": num_user_policies,
            "NumAttachedUserPolicies": num_attached_user_policies,
            "NumGrouops": num_user_groups,
        })

filename = 'num-policies-iam-users.csv'

df = pd.DataFrame(users)

df.to_csv(open(filename, 'w'), index=False)