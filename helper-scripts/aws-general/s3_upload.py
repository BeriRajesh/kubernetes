#!/usr/bin/env python3
from __future__ import print_function

import argparse
import glob
import os
import sys
import zipfile

import boto3
from botocore.exceptions import ClientError

DESTINATION_BUCKET = "annalect-deployment-artifacts"

def upload_to_s3(appId):
    """
    Uploads an artifact to Amazon S3
    """

    zipfile = appId + ".zip"

    try:
        client = boto3.client('s3')
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False
    try:
        print(zipfile)
        client.put_object(
            Body=open(zipfile, 'rb'),
            Bucket=DESTINATION_BUCKET,
            Key=zipfile
        )
    except ClientError as err:
        print("Failed to upload artifact to S3.\n" + str(err))
        return False
    except IOError as err:
        print("Failed to access artifact in this directory.\n" + str(err))
        return False
    return True

def zipdir(path, ziph):
    # ziph is zipfile handle
    curr_dir = os.getcwd()
    os.chdir(path)
    files = glob.glob('*')
    for file in files:
        print(file)
        if file == ziph.filename:
            print('   ... skipping')
            continue
        ziph.write(file)
    os.chdir(curr_dir)

def main():

    if len(sys.argv) != 3:
        print(f'\nError: expected two parameters.\nUse like for ex: $ ./{sys.argv[0].split("/")[-1]} <folder_to_compress> <site_id>\nNote: site_id later maps to https://site_id.poc.annalect.com\n')
        sys.exit(1)

    appId = sys.argv[1]
    siteId = sys.argv[2]
    zipname = siteId + '.zip'

    if not os.path.isdir(appId):
        raise Exception(appId + ' must be a valid path to a directory')

    zipf = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)
    zipdir(appId, zipf)
    zipf.close()

    # parser = argparse.ArgumentParser()
    # parser.add_argument("bucket", help="Name of the existing S3 bucket")
    # parser.add_argument("artifact", help="Name of the artifact to be uploaded to S3")
    # parser.add_argument("bucket_key", help="Name of the S3 Bucket key")
    # args = parser.parse_args()

    if not upload_to_s3(siteId):
        raise Exception('Failed uploading ' + appId + ' to S3.')

    print('Success!')

if __name__ == "__main__":
    main()
