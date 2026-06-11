"""
Deletes duplicate cloudemail record from DynamoDB's 'cloudemails' table

"""
import argparse
import datetime
import json
import re
import subprocess
import sys
from pprint import pprint

import boto3
from botocore.client import ClientError
from boto3.dynamodb.conditions import Key, Attr

dynamoTableName = 'cloudemails'
ruleSetName = 'default-rule-set'
ruleName = 'CloudEmail-Dynamo'

ses = boto3.client('ses', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
table = dynamodb.Table(dynamoTableName)


def delete_from_dynamodb(record_id):
    if "id" in record_id:
        record_id = record["id"]
    response = table.delete_item(
        Key={
            'id': record_id
        }
    )
    # print(json.dumps(record, indent=4, default=str))
    print(response)

def delete_from_ses(rule):
    # print("Deleting:")
    # print(ruleSetName)
    # print(rule["Name"])
    response = ses.delete_receipt_rule(
        RuleSetName=ruleSetName,
        RuleName=rule["Name"]
    )
    print(response)

def clean_duplicate_emails_in_dynamo():
    paginator = dynamodb_client.get_paginator('scan')
    response_iterator = paginator.paginate(
        TableName=dynamoTableName,
    )

    cloudemail_ids = []
    cloudemail_values = []
    for records in response_iterator:
        for record in records['Items']:
            cloudemail_ids.append(record['id']['S'])
            cloudemail_values.append(record['value']['S'])

    for i, cloudemail_id_main in enumerate(cloudemail_ids):
        if "@" in cloudemail_id_main:
            # this is well formed email
            continue

        # we try to find a duplictate
        for j, cloudemail_id_search in enumerate(cloudemail_ids):
            if (    cloudemail_id_main != cloudemail_id_search
                and cloudemail_id_main in cloudemail_id_search
            ):
                input(f"Delete id '{cloudemail_id_main}'")
                delete_from_dynamodb(cloudemail_id_main)


if __name__ == '__main__':
    # parser = argparse.ArgumentParser(
    #     description='Manage CloudEmail SES Rules and S3 Event Notifications setup')

    # parser.add_argument('-e', '--cloudemail', required=False,
    #                     help='string to match cloudemail')

    # args = parser.parse_args()

    clean_duplicate_emails_in_dynamo()
