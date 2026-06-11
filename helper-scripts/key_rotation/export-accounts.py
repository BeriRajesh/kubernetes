"""
Script to export AWS IAM account keys
"""

import boto3
from pprint import pprint

client = boto3.client('iam')
paginator = client.get_paginator('list_users')

response_iterator = paginator.paginate()

saccounts = []
for user_page in response_iterator:
    # pprint(user_page)
    # print(len(user_page['Users']))
    for user in user_page['Users']:

        # looking for a string in the UserName
        if "service" in user['UserName']:
            username = user['UserName']
            # print(f"Account: {username}")
            response = client.list_access_keys(
                UserName=username
            )
            for key in response["AccessKeyMetadata"]:
                accesskey = key['AccessKeyId']
                print(accesskey+"|",end="")
                saccounts.append({
                    'account': username,
                    'accesskey': accesskey
                })

pprint(saccounts)

