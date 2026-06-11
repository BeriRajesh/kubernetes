"""
Moves cloudemails on SES from individual rules to the general CloudEmail-Dynamo rule
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

def list_ses_rules():
    response = ses.describe_receipt_rule(
        RuleSetName=ruleSetName,
        RuleName=ruleName
    )
    dynamo_recipients = response['Rule']['Recipients']

    response = ses.describe_receipt_rule_set(
        RuleSetName=ruleSetName
    )
    receipt_rule_set = response

    recipients = []

    # print(json.dumps(response, indent=4, default=str))
    for rule in response["Rules"]:
        if len(rule["Recipients"]) > 1:
            print('More then one recipient in this rule. Continuing')
            continue

        # print()
        # pprint(rule)
        # input()
        # continue

        for recipient in rule["Recipients"]:

            if "@" not in recipient:
                continue

            if recipient not in dynamo_recipients:
                stop = 1
                input(f'Recipient {recipient} not found in dynamo recipients. Continue?')


            bucketname = "annalectcloudmail"
            for rule_action in rule["Actions"]:
                if "S3Action" not in rule_action:
                    continue
                if rule_action["S3Action"]["BucketName"] == bucketname:
                    break
                    # input('WARNING: recipient {recipient} does not point to {bucketname}. Continuing.')
                    # continue
            else:
                continue

            # resp = input(f"Disable individual rule '{recipient}?")

            # get rule
            individual_rule = ses.describe_receipt_rule(
                RuleSetName=ruleSetName,
                RuleName=rule['Name']
            )['Rule']

            individual_rule['Enabled'] = False

            response = ses.update_receipt_rule(
                RuleSetName=ruleSetName,
                Rule=individual_rule
            )

            print(f"Disabled individual rule '{recipient}.")


    #         response = table.scan(
    #             Select='ALL_ATTRIBUTES',
    #             FilterExpression=Attr('id').eq(recipient)
    #         )

    #         # pprint(response)

    #         if len(response["Items"]) > 1:
    #             print('More than one element in Item for rule {rule} and recipient {recipient}. Continuing.')
    #             continue

    #         # print(f'{recipient} was found in Dynamo. We can move to the rule {ruleName} on SES')

    #         recipients.append(recipient)

    #         break
    #     # break

    # # print('These recipients were found in DynamoDB and thus can be deleted from individual SES rules and added to main DynamoDB rule')
    # # pprint(recipients)


    # print(f"These recipients were found in DynamoDB and thus can be deleted from individual SES rules and added to main DynamoDB rule. \nFor now, these recipient were moved to the DynamoSES rule '{dynamo_receipt_rule}' from the rule set '{ruleSetName}'. Their individual rules can now be deleted from SES (since they're added to the single DynamoDB Rule).")
    # print(len(dynamo_recipients))





if __name__ == '__main__':
    # parser = argparse.ArgumentParser(
    #     description='Manage CloudEmail SES Rules and S3 Event Notifications setup')

    # parser.add_argument('-e', '--cloudemail', required=False,
    #                     help='string to match cloudemail')

    # args = parser.parse_args()

    list_ses_rules()
