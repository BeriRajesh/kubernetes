import json
import boto3
from pprint import pprint
import time

client = boto3.client('logs')
paginator = client.get_paginator('describe_log_groups')

response_iterator = paginator.paginate()

n=0
for pages in response_iterator:
    for loggroup in pages.get('logGroups'):
        n+=1
        pprint(loggroup)
        if not loggroup.get('retentionInDays'):
            # response = client.put_retention_policy(
            #     logGroupName=loggroup['logGroupName'],
            #     retentionInDays=30
            # )
            a=1
            time.sleep(0.1)
        elif loggroup.get('retentionInDays') != 30:
            a=1

print(f"total of {n}")