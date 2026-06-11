#!/usr/bin/env python3

"""delete tags from ec2 instances"""

import argparse
from pprint import pprint
import sys

import boto3


parser = argparse.ArgumentParser(description='Export resources from AWS')
parser.add_argument("type", choices=['all', 'rds'], nargs='?', default='all',
                    help="Action to perform (defaults to all)")
parser.add_argument("-v", "--verbose", default=0, help="Increase output verbosity", action='count')
parser.add_argument("-p", "--profile", default='', help="AWS profile to use. Defaults to 'default'")
parser.add_argument("-i", "--interactive", default='', help="Presents a prompt before executing copying commands to"
                                                            "source files", action='store_true')
args = parser.parse_args()

ec2 = boto3.client('ec2')

ec2s = ec2.describe_instances()

tags_to_delete = open("tags-to-delete.txt", "r").read().splitlines()

for reservation in ec2s["Reservations"]:
    for ec2instance in reservation["Instances"]:
        InstanceId = ec2instance["InstanceId"]
        tags = ec2instance["Tags"]
        for tag in tags:
            tagname = tag["Key"]
            if tagname in tags_to_delete:
                print(f"removing tag {tagname} from {InstanceId}")
                response = ec2.delete_tags(
                    DryRun=False,
                    Resources=[
                        InstanceId,
                    ],
                    Tags=[
                        {
                            'Key': tagname,
                        },
                    ]
                )
                print(response)
