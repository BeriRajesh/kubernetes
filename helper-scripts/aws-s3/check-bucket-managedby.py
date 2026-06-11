"""
Outputs the value of the ManagedBy tag of a bucket.
The bucket is specified as first parameter

Example:
    python3 this_script.py <bucket_name>
"""


import json
import os
import subprocess
import sys

import boto3

s3 = boto3.client('s3')


if len(sys.argv) == 0:
    print(f"Please input the bucket name as first parameter. Ex. python3 {sys.argv[0]} bucket_name")
    sys.exit(1)

bucket_name = sys.argv[1]

try:
    # tagging = subprocess.check_output(f'aws --output json s3api get-bucket-tagging --bucket {bucket_name}', shell=True)
    tagging = s3.get_bucket_tagging(
        Bucket=bucket_name
    )
except Exception as e:
    print("There was an error. Is the bucket name correct?")
    print(e)
    sys.exit(1)

for tag in tagging.get('TagSet'):
    if tag['Key'] == 'ManagedBy':
        print(f"Bucket '{bucket_name}' is managed by '{tag['Value']}'")
        break
else:
    print(f"No ManagedBy tag found for bucket '{bucket_name}' ")
    sys.exit(1)