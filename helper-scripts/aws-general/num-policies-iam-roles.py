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

# update date as a security measure if you really intend to delete roles
DELETE_ROLES = False and str(datetime.datetime.now()) < '2020-07-30'

iam = boto3.client('iam')
paginator = iam.get_paginator('list_roles')

users = []

def delete_role(rolename):
    """ deletes role by rolename """

    try:
        iam.delete_role(
            RoleName=rolename
        )

        tqdm.write(f"Deleted role {rolename}!")
    except Exception as e:
        tqdm.write(f"Error deleing role {rolename}!")
        tqdm.write(str(e))

page_iterator = paginator.paginate()

for page in tqdm(page_iterator):
    for user in tqdm(page['Roles']):
        user_policies = iam.list_role_policies(RoleName=user['RoleName'])
        num_user_policies = len(user_policies['PolicyNames'])
        user_policies = iam.list_attached_role_policies(RoleName=user['RoleName'])
        num_attached_user_policies = len(user_policies['AttachedPolicies'])
        # user_groups = iam.list_groups_for_rolesuser(UserName=user['UserName'])
        # num_user_groups = len(user_groups['Groups'])

        if DELETE_ROLES:
            if num_user_policies == 0 and num_attached_user_policies == 0:
                delete_role(rolename=user['RoleName'])
                continue

        users.append({
            "RoleName": user['RoleName'],
            "RoleId": user['RoleId'],
            "CreateDate": user['CreateDate'],
            "NumRolePolicies": num_user_policies,
            "NumAttachedRolePolicies": num_attached_user_policies,
        })

filename = 'num-policies-iam-roles.csv'

df = pd.DataFrame(users)

df.to_csv(open(filename, 'w'), index=False)