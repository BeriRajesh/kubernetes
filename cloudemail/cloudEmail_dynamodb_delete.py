"""
Deletes cloud email from SES and DynamoDB

Example usage:
python3 cloudEmail_sesRules_s3Event_setup.py \
    --dest_s3_path=s3://bucketname/dest_folder \
    --cloudemail=tclna+clientid@annalect.cloud
"""
import argparse
import datetime
import json
import re
import subprocess
import sys

import boto3
from botocore.client import ClientError
from boto3.dynamodb.conditions import Key, Attr

dynamoTableName = 'cloudemails'
ruleSetName = 'default-rule-set'

ses = boto3.client('ses', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(dynamoTableName)


def delete_from_dynamodb(record):
    response = table.delete_item(
        Key={
            'id': record['id']
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

def main(cloudemail):
    # Create an SES/S3 client
    # s3 = boto3.resource('s3', region_name='us-east-1')


    # s3_client = boto3.client('s3', region_name='us-east-1')

    # Filter cloudemail for clientid
    clientid = ""
    if "+" in cloudemail:
        clientid = re.search('.*\+(.*)@', cloudemail).group(1)
        ses_rule_name = clientid

    print("cloud_email=" + cloudemail)
    print("clientid=" + clientid)

    print("***************************************************************")
    print("*** Searching SES ***")
    response = ses.describe_receipt_rule_set(
        RuleSetName=ruleSetName
    )

    # print(json.dumps(response, indent=4, default=str))
    for rule in response["Rules"]:
        for recipient in rule["Recipients"]:
            if cloudemail in recipient or (clientid !="" and clientid in recipient):
                if len(rule["Recipients"]) > 1:
                    print()
                    print(f"There is more than one recipient this rule. Ignoring.")
                    print(f"RuleName={rule['Name']}. Recipients:\n{json.dumps(rule['Recipients'], indent=4, default=str)}")
                    continue
                # print()
                ans = input(f"Delete {recipient} from SES rule, it would delete {json.dumps(rule, indent=4, default=str)} \n (y/N) ? ")
                if ans == "y":
                    delete_from_ses(rule)

    print("***************************************************************")
    print("*** Searching DynamoDB ***")
    response = table.scan(
        Select='ALL_ATTRIBUTES',
        FilterExpression=Attr('id').contains(cloudemail)
    )

    print(response["Items"])
    for email in response["Items"]:
        ans = input(f"Delete {email['id']} from Dynamo (y/N) ?")
        if ans == "y":
            delete_from_dynamodb(email)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Manage CloudEmail SES Rules and S3 Event Notifications setup')

    parser.add_argument('-e', '--cloudemail', required=True,
                        help='string to match cloudemail')

    args = parser.parse_args()

    main(cloudemail=args.cloudemail)
