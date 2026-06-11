#!/usr/bin/env python3

""" Create new job definition based on another name
"""

import argparse
import sys

# import pandas as pd
import boto3
import json
from pprint import pprint
#import re

def get_args():
    parser = argparse.ArgumentParser(description='Description')

    type_choices = [
        'batch_job_definition',
        'batch_job_queue',
        'ecs_task_definition',
        'cloudwatch_rule',
        'iam_policy',
        'iam_user',
        'iam_role',
    ]
    parser.add_argument("-t", "--type", default=None,
        choices=type_choices,
        help="Type of resource to duplicate")

    parser.add_argument("-d", "--debug_options", action='store_true',
                    help="Debug options passed and exit")

    args = parser.parse_args()

    if args.type is None:
        while args.type is None:
            print('Please choose a type:')
            for i, choice in enumerate(type_choices):
                print(f'{i}: {choice}')
            choice = input('Please type your choice:')

            if choice in type_choices:
                args.type = choice
                break
            elif int(choice) < len(type_choices)-1:
                args.type = type_choices[int(choice)]
                break

            print('Your choice was not among the valid choices. Please try again or cancel the script.')

    if not any(vars(args).values()):
        parser.parse_args(['--help'])
        # parser.error('No arguments provided.')

    if args.debug_options:
        print(args)
        sys.exit()

    return args

def duplicate_ecs_task_definition():
    """ Duplicate ecs_task_definition """
    print(f"___ duplicate_ecs_task_definition ___")
    client = boto3.client('ecs')
    resource_name = input('Input name of resource to copy: ')
    resource_json = client.describe_task_definition(taskDefinition=resource_name)
    print('Source resource and targets found.')
    new_resource_name = input('What is the name for the copy? ')
    new_resource = resource_json.copy()
    del new_resource['ResponseMetadata']
    new_resource = new_resource['taskDefinition']
    del new_resource['taskDefinitionArn']
    del new_resource['revision']
    del new_resource['status']
    del new_resource['requiresAttributes']
    del new_resource['compatibilities']
    new_resource['family'] = new_resource_name
    response = client.register_task_definition(**new_resource)
    pprint(response)
    print('^ Resource duplicated')

def duplicate_batch_job_definition():
    """ Duplicate batch job definition """
    print(f"___ duplicate_batch_job_definition ___")
    batch = boto3.client('batch')
    source_jf_name = input('Input name of the source job definition to copy: ')
    source_jf = batch.describe_job_definitions(jobDefinitionName=source_jf_name)
    if len(source_jf_name) == 0:
        print(f'Job definition "{source_jf}" not found.')
        sys.exit(1)
    print('Job definition found.')
    new_jd_name = input('What is the name for the new job definition? ')
    new_jf = source_jf['jobDefinitions'][0].copy()
    del new_jf['jobDefinitionArn']
    del new_jf['revision']
    del new_jf['status']
    new_jf['jobDefinitionName'] = new_jd_name
    response = batch.register_job_definition(**new_jf)
    print('Job Definition created')

def duplicate_batch_job_queue():
    """ Duplicate batch_job_queue """
    print(f"___ duplicate_batch_job_queue ___")
    client = boto3.client('batch')
    resource_name = input('Input name of resource to copy: ')
    resource_json = client.describe_job_queues(jobQueues=[resource_name])
    print('Source resource and targets found.')
    # pprint(resource_json)
    # pprint(targets_json)
    new_resource_name = input('What is the name for the copy? ')
    new_resource = resource_json.copy()
    del new_resource['ResponseMetadata']
    new_resource.update(new_resource['jobQueues'][0])
    del new_resource['jobQueues']
    del new_resource['status']
    del new_resource['statusReason']
    del new_resource['jobQueueArn']
    new_resource['jobQueueName'] = new_resource_name
    response = client.create_job_queue(**new_resource)
    pprint(response)
    print('^ Resource duplicated')


def duplicate_iam_policy():
    """ Duplicate IAM policy """
    print(f"___ duplicate_iam_policy ___")
    client = boto3.client('iam')
    resource_name = input('Input name of resource to copy: ')
    resource_arn = f"arn:aws:iam::661095214357:policy/{resource_name}"
    resource_json = client.get_policy(PolicyArn=resource_arn)
    resource_id = resource_json.get('Policy')['DefaultVersionId']
    policy_version = client.get_policy_version(
        PolicyArn=resource_arn,
        VersionId=resource_id
    )['PolicyVersion']
    print('Source resource found.')
    # pprint(resource_json)
    # pprint(targets_json)
    new_resource_name = input('What is the name for the copy? ')
    new_resource = resource_json.copy()

    response = client.create_policy(
        PolicyName=new_resource_name,
        PolicyDocument=json.dumps(policy_version['Document']),
    )

    print(f'Created rule {new_resource_name}')

def duplicate_cloudwatch_rule():
    """ Duplicate duplicate_cloudwatch_rule """
    print(f"___ duplicate_cloudwatch_rule ___")
    client = boto3.client('events')
    resource_name = input('Input name of resource to copy: ')
    resource_json = client.describe_rule(Name=resource_name)
    targets_json = client.list_targets_by_rule(Rule=resource_name)
    print('Source resource and targets found.')
    # pprint(resource_json)
    # pprint(targets_json)
    new_resource_name = input('What is the name for the copy? ')
    new_resource = resource_json.copy()
    del new_resource['ResponseMetadata']
    del new_resource['EventBusName']
    del new_resource['Arn']
    del new_resource['CreatedBy']
    new_resource['Name'] = new_resource_name
    new_targets = targets_json['Targets'].copy()



    client.put_rule(**new_resource)
    print(f'Created rule {new_resource_name}')

    client.put_targets(
        Rule=new_resource_name,
        Targets=new_targets
    )
    print(f'Put {len(new_targets)} targets')

def duplicate_iam_user():
    """ duplicate_iam_user """
    print(f"___ duplicate_iam_user ___")


    client = boto3.client('iam')
    resource_name = input('Input name of resource to copy: ')

    # get user
    # get user policies
    response = client.list_attached_user_policies(
        UserName=resource_name
    )
    managed_policies = response.get("AttachedPolicies")

    response = client.list_user_policies(
        UserName=resource_name,
    )
    inline_policies = response.get("PolicyNames")

    print('Source resource found.')

    new_resource_name = input('What is the name for the copy? ')

    try:
        # create user
        response = client.create_user(
            UserName=new_resource_name,
        )
    except Exception as error:
        print(error)
        ans = input(f"User name {new_resource_name} already exists. Delete? y/N: ")
        if ans != "y":
            ans = input("Do you wish to continue transferring policies and creating keys? y/N: ")
            if ans != "y":
                print(f"You selected {ans}. Exiting.")
                sys.exit(0)
        else:
            response = client.delete_user(
                UserName=new_resource_name
            )
            response = client.create_user(
                UserName=new_resource_name,
            )
            print(f"User {new_resource_name} created anew")

    # attach policies
    for policy in managed_policies:
        response = client.attach_user_policy(
            UserName=new_resource_name,
            PolicyArn=policy["PolicyArn"]
        )

    for policy in inline_policies:
        # get document
        response = client.get_user_policy(
            UserName=resource_name,
            PolicyName=policy
        )
        document = json.dumps(response.get('PolicyDocument'))

        # put inline policy to user
        response = client.put_user_policy(
            UserName=new_resource_name,
            PolicyName=policy,
            PolicyDocument=document
        )

    # create credentials
    response = client.create_access_key(
        UserName=new_resource_name
    )

    # print credentials
    access_key = response.get("AccessKey").get("AccessKeyId")
    secret_key = response.get("AccessKey").get("SecretAccessKey")

    print("User created:")
    print(f"Username: {new_resource_name}")
    print(f"Access Key: {access_key}")
    print(f"Secret Key: {secret_key}")

def duplicate_iam_role():
    """ duplicate_iam_role """
    print(f"___ duplicate_iam_role ___")


    client = boto3.client('iam')
    resource_name = input('Input name of resource to copy: ') or 'omni-scheduler-eu-prod-EcsTaskRole'

    # get user
    # get user policies
    resource = client.get_role(
        RoleName=resource_name
    )
    assume_role_policy_document = resource['Role']['AssumeRolePolicyDocument']
    response = client.list_attached_role_policies(
        RoleName=resource_name
    )
    managed_policies = response.get("AttachedPolicies")

    response = client.list_role_policies(
        RoleName=resource_name,
    )
    inline_policies = response.get("PolicyNames")

    print('Source resource found.')

    new_resource_name = input('What is the name for the copy? ') or 'omni-scheduler-eu-dev-EcsTaskRole'

    try:
        # create user
        response = client.create_role(
            RoleName=new_resource_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy_document),
        )
    except Exception as error:
        print(error)
        ans = input(f"User name {new_resource_name} already exists. Delete? y/N: ")
        if ans != "y":
            ans = input("Do you wish to continue transferring policies and creating keys? y/N: ")
            if ans != "y":
                print(f"You selected {ans}. Exiting.")
                sys.exit(0)
        else:
            response = client.delete_role(
                RoleName=new_resource_name
            )
            response = client.create_role(
                RoleName=new_resource_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy_document),
            )
            print(f"User {new_resource_name} created anew")

    # attach policies
    for policy in managed_policies:
        response = client.attach_role_policy(
            RoleName=new_resource_name,
            PolicyArn=policy["PolicyArn"]
        )

    for policy in inline_policies:
        # get document
        response = client.get_role_policy(
            RoleName=resource_name,
            PolicyName=policy
        )
        document = json.dumps(response.get('PolicyDocument'))

        # put inline policy to user
        response = client.put_role_policy(
            RoleName=new_resource_name,
            PolicyName=policy,
            PolicyDocument=document
        )
    print('^ Resource duplicated')





if __name__ == "__main__":
    args = get_args()

    # calling duplicate function
    globals()[f"duplicate_{args.type}"]()
