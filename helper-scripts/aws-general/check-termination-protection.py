import argparse
import sys

# try:
#     from tqdm import tqdm
#     import pandas as pd
# except:
#     print('Please install tqdm: pip3 install tqdm pandas')
#     sys.exit(1)
import boto3
import json
from pprint import pprint
import re

# def get_args():
#     parser = argparse.ArgumentParser(description='Description')

#     parser.add_argument("-n", "--name", default=None,
#                     help="Name of ...")

#     parser.add_argument("-d", "--debug_options", action='store_true',
#                     help="Debug options passed and exit")

#     args = parser.parse_args()

#     # if not any(vars(args).values()):
#     #     parser.parse_args(['--help'])
#     #     # parser.error('No arguments provided.')

#     if args.debug_options:
#         print(args)
#         sys.exit()

#     return args

def check_tag(check_tag, tags, return_value=False):
    for tag in tags:
        if tag["Key"].upper() == check_tag.upper():
            if not tag["Value"] == '':
                return tag["Value"] if return_value else True

    return False

def enable_termination_protection_from_ec2():
    """ enables termination protection for EC2s """

    client = boto3.client("ec2")
    paginator = client.get_paginator('describe_instances')
    response_iterator = paginator.paginate()
    without_monitoring_tag = []
    for page in response_iterator:
        for reservation in page['Reservations']:
            for instance in reservation['Instances']:
                # pprint(instance["Tags"])
                tag_exists = check_tag('Monitoring', instance["Tags"])
                if tag_exists:
                    response = client.modify_instance_attribute(
                        SourceDestCheck={
                            'Value': True|False
                        },
                        Attribute='disableApiTermination',
                        InstanceId=instance["InstanceId"],
                        Value='true'
                    )
                else:
                    instance_name = check_tag('Name', instance["Tags"], return_value=True)
                    without_monitoring_tag.append({
                        'id': instance["InstanceId"],
                        'name': instance_name
                    })

    json.dump(without_monitoring_tag, open('without_monitoring_tag.json', 'w'))

def enable_termination_protection_from_rds():
    """ enables termination protection for RDSs """

    client = boto3.client("rds")
    paginator = client.get_paginator('describe_db_instances')
    response_iterator = paginator.paginate()
    without_monitoring_tag = []
    for page in response_iterator:
        for instance in page['DBInstances']:
            if instance.get("DBClusterIdentifier"):
                db_instance_id = instance["DBClusterIdentifier"]
                pprint(db_instance_id)
                client.modify_db_cluster(
                    DBClusterIdentifier=db_instance_id,
                    DeletionProtection=True,
                )
            elif instance.get("DBInstanceIdentifier"):
                db_instance_id = instance["DBInstanceIdentifier"]
                pprint(db_instance_id)
                client.modify_db_instance(
                    DBInstanceIdentifier=db_instance_id,
                    DeletionProtection=True,
                )
            pass

def enable_termination_protection_from_cloudformation():
    """ enables termination protection for RDSs """

    client = boto3.client("cloudformation")
    params = dict(
        StackStatusFilter=[
            'CREATE_COMPLETE'
        ]
    )
    resources = []
    while True:
        response = client.list_stacks(**params)
        resources.extend(response['StackSummaries'])
        if response.get('NextToken'):
            params['NextToken'] = response.get('NextToken')
        else:
            break

    without_monitoring_tag = []
    for resource in resources:
        stack_name = resource['StackName']
        ignore_stack_name_pattern = '^ab' # audience_builder stacks
        if re.search(ignore_stack_name_pattern, stack_name):
            continue

        try:
            pass
            response = client.update_termination_protection(
                EnableTerminationProtection=True,
                StackName=resource['StackName']
            )
        except Exception as e:
            if e.response['Error']['Code'] == 'ValidationError':
                if "substack" in e.response['Error']['Message']:
                    continue
            raise e

def main():
    """ check termination protection """
    enable_termination_protection_from_ec2()
    enable_termination_protection_from_rds()
    enable_termination_protection_from_cloudformation()
    pass

if __name__ == "__main__":
    # args = get_args()

    main()