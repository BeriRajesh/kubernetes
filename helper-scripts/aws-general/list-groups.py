""" Writes CSV file with the list of IAM groups and members per groups """

import argparse
import sys

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

iam = boto3.client('iam')
OUTPUT_FNAME = 'groups-num-users.csv'

def get_args():
    parser = argparse.ArgumentParser(description='Description')

    # parser.add_argument("-n", "--name", default=None,
    #                 help="Name of ...")

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

def get_groups_dictionary(group_name):
    """ Returns group dictionary"""

    group_dict = {}

    group_dict["Name"] = group_name

    try:
        response = iam.get_group(
            GroupName=group_name,
        )
    except Exception as e:
        print(e)
        # group_dict["Location"] = '-'

    group_dict["num.members"] = len(response['Users'])

    return group_dict

def get_groups():
    """ Returns group list """

    group_list = []
    marker = None
    params = {}

    while True:
        print('.', end="")
        if marker:
            params['Marker'] = marker

        groups = iam.list_groups(**params)

        group_list.extend([g["GroupName"] for g in groups['Groups']])

        if groups.get("Marker"):
            marker = groups.get("Marker")
            continue

        break
    print(f" {len(group_list)} groups found")


    return group_list

def main():
    """Writes csv of group descriptions"""

    descriptions = []

    print('Fetching groups ', end="")
    groups = get_groups()
    print('Fetching number of users per group ... ', end="")
    for group in tqdm(groups):
        descriptions.append(get_groups_dictionary(group))
    print("Done!")

    print(f'Writing {OUTPUT_FNAME}')
    df = pd.DataFrame(descriptions)
    df.to_csv(f"{OUTPUT_FNAME}-deleted", index=False)
    print('Done!')

    return descriptions

def delete_empty_groups(df_group_descriptions):
    """ delete empty groups from a dataframe `df_group_description` """

    iam = boto3.resource('iam')


    for i, row in df_group_descriptions.iterrows():
        num_members = row.get("num.members")
        if num_members == 0:
            try:
                group_name = row.get("Name")
                print(f"Deleting group {group_name} ... ", end="")

                group = iam.Group(group_name)
                attached_policies = group.attached_policies.all()
                # if len(attached_policies):
                for policy in attached_policies:
                    policy_arn = policy.arn
                    response = group.detach_policy(
                        PolicyArn=policy_arn
                    )

                policies = group.policies.all()
                # if len(attached_policies):
                iam = boto3.resource('iam')
                for policy in policies:
                    group_policy = iam.GroupPolicy(group_name, policy.name)
                    response = group_policy.delete()
                group.delete()
                print('Deleted!')
            except Exception as e:
                print()
                if "cannot be found":
                    print('Group cannnot be found')
                    continue
                print(e)

if __name__ == "__main__":
    args = get_args()

    action = 'generate-csv'
    # action = 'delete-empty-groups'
    if action == 'generate-csv':
        group_descriptions = main()
    elif action == 'delete-empty-groups':
        df = pd.read_csv(open(OUTPUT_FNAME))
        delete_empty_groups(df)

