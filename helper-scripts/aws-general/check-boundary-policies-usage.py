""" check if boundary policies are only used as boundary policies """

import argparse
import re
import sys
from pprint import pprint

import boto3

# try:
#     from tqdm import tqdm
#     import pandas as pd
# except:
#     print('Please install tqdm: pip3 install tqdm pandas')
#     sys.exit(1)
#import json

def get_args():
    parser = argparse.ArgumentParser(description='Description')

    # parser.add_argument("-n", "--name", default=None,
                    # help="Name of ...")

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
    """ check policies """

    client = boto3.client('iam')
    policies = []
    marker = False

    params = dict(
        Scope='Local',
        OnlyAttached=True,
        PolicyUsageFilter='PermissionsPolicy',
    )
    while marker is not None:
        response = client.list_policies(**params)
        policies.extend(response.get('Policies'))
        marker = response.get('Marker')
        params['Marker'] = marker

    print(f'{len(policies)} found')

    misused_policies = []
    for policy in policies:
        policy_name = policy['PolicyName']
        if re.search('boundary|boundari', policy_name, re.IGNORECASE):
            misused_policies.append(policy_name)

    pprint(misused_policies)


if __name__ == "__main__":
    args = get_args()

    main()