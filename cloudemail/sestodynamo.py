""" Converts annalect.cloud SES rules to cloudmails DynamoDB records """

import json
import subprocess
import re
import sys

with open("cloudmailrules.json", "r") as fh:
    rules = json.loads(fh.read())

for rule in rules["Rules"]:
    clientid = rule["Name"]
    if len(clientid) != 16 or re.search("[^a-zA-Z0-9]", clientid):
        continue

    destination_bucket = ""
    prefix = ""
    for act in rule["Actions"]:
        try:
            if act["AddHeaderAction"]["HeaderName"] == "destbucket":
                destination_bucket = act["AddHeaderAction"]["HeaderValue"]
            if act["AddHeaderAction"]["HeaderName"] == "destbucketprefix":
                prefix = act["AddHeaderAction"]["HeaderValue"]
        except:
            pass

    if destination_bucket and prefix:
        print("create dynamo clientid: {}, bucket:{}, prefix: {}".format(clientid, destination_bucket, prefix))

        value = {
            "destination_bucket": destination_bucket,
            "prefix": prefix
        }

        dynamodb_json = {
            "id": {"S": clientid},
            "value": {"S": json.dumps(value)}
        }

        cmd = "aws dynamodb put-item --table-name cloudemails --item '{}'".format(
            json.dumps(dynamodb_json)
        )

        # sys.exit(cmd)
        output = subprocess.check_output(cmd, shell=True).decode().strip()
        print(output)
