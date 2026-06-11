"""
Adds record to DynamoDB table `cloudemails`

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


def remove_cloudemail(cloudemail):
    """ removes cloudemail from dynamodb """

    dynamodb = boto3.client('dynamodb', region_name='us-east-1')

    dynamodb.delete_item(
        TableName="cloudemails",
        Key={"id": {"S": cloudemail}}
    )


def add_cloud_email(dest_s3_path, cloudemail):
    # Create an SES/S3 client
    s3 = boto3.resource('s3', region_name='us-east-1')
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')

    # Filter bucket and prefix from dest_s3_path
    dbp = dest_s3_path

    if dbp.startswith('s3://'):
        dbp = dbp[5:]
    if dbp.startswith('/'):
        dbp = dbp[1:]
    if dbp.endswith('/'):
        dbp = dbp[:-1]

    p = dbp.split('/')
    destbucket = p[0]
    destbucketprefix = '/'.join(p[1:])

    try:
        bucket = s3.Bucket(destbucket)
        s3.meta.client.head_bucket(Bucket=bucket.name)
    except ClientError:
        print("Dest S3 Bucket named %s does not exist, please provide valid "
              "s3 bucket" % bucket.name)
        exit(1)

    # verify valid email address with regex, it HAS to have a '+' and text to both side of it: xxx+anylabel@domain.com
    valid_email = re.search(r'[a-zA-Z0-9_\-\.]+\+[a-zA-Z0-9_\-\.]+@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([a-zA-Z0-9\-]+\.)+))([a-zA-Z]{2,5}|[0-9]{1,5})(\]?)', cloudemail)
    if valid_email:
        clientid = valid_email[0]
        print("Validated email {}".format(clientid))
    else:
        print('Error, not valid email. Does it have a "+" before the "@"?')
        sys.exit(1)

    print("dest_bucket=" + destbucket)
    print("dest_bucket_prefix=" + destbucketprefix)
    print("cloud_email=" + cloudemail)
    print("dest_s3_path_to_store_data=" + dest_s3_path)
    print("clientid=" + clientid)

    value = {
        "destination_bucket": destbucket,
        "prefix": destbucketprefix
    }

    dynamodb_json = {
        "id": {"S": clientid},
        "value": {"S": json.dumps(value)}
    }

    # cmd = "aws --region us-east-1 dynamodb put-item --table-name cloudemails --item '{}'".format(
    #     json.dumps(dynamodb_json)
    # )

    # # sys.exit(cmd)
    # subprocess.check_output(cmd, shell=True).decode().strip()

    dynamodb.put_item(
        TableName='cloudemails',
        Item=dynamodb_json
    )




if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Manage CloudEmail SES Rules and S3 Event Notifications setup')

    parser.add_argument('--remove',
                        help='Cloudemail address to remove')
    parser.add_argument('--dest_s3_path', dest='dest_s3_path',
                        help='Name of the dest S3 path to save data')
    parser.add_argument('--cloudemail', dest='cloudemail',
                        help='annalectcloud email address')

    args = parser.parse_args()
    if args.remove:
        cloudemail = args.remove
        print(f"Removing cloudemail {cloudemail}.")
        remove_cloudemail(cloudemail)
        print('Done!!')
        sys.exit(0)

    if not args.dest_s3_path or not args.cloudemail:
        print("\nError: Missing --cloudemail and/or --dest_s3_path parameters\n\n")
        parser.print_help()
        sys.exit(1)

    add_cloud_email(args.dest_s3_path, args.cloudemail)
