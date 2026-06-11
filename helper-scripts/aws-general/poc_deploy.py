#!/usr/bin/env python3

import argparse
import sys
import os

import requests
import json
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
import s3_upload

def get_args():
    parser = argparse.ArgumentParser(
        description='Utility to deploy sites to AWS ECS as a POC')

    if len(sys.argv[1:])==0:
        parser.print_help()
        sys.exit(1)

    parser.add_argument("-s", "--site_id", required=True,
        help=("Site identifier or path/to/zip/site_id.zip \n"
            "Maps to site_id.poc.annalect.com."))

    parser.add_argument("-a", "--action", default="u", choices=["u","c","d"],
        help=("Whether to [c]reates,[u]pdates or [d]eletes the POC site. \n"
            "Update creates the site if it doesn't exist."))

    parser.add_argument("-f", "--folder", required=False,
                    help="Compresses, uploads and deploys the POC. Not yet implemented.")

    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.parse_args(['--help'])

    return args

def main(**kwargs):
    """ Creates/updates or deletes a POC site based on the arguments received"""

    site_id = kwargs["site_id"]
    if site_id[-4:].lower() != ".zip":
        site_id += ".zip"

    if not os.path.isfile(site_id):
        print(f'ERROR: {site_id} could not be found.')
        sys.exit(1)

    # getting stack_name from a string like path/to/stack_name.zip
    stack_name = site_id.split('/')[-1].split('.')[0]

    action = kwargs["action"]
    if action == 'c':
        appName = "create_stack"
    elif action == 'd':
        appName = "delete_stack"

    payload = {
        "appName": appName,
        "StackName": stack_name
    }

    auth = BotoAWSRequestsAuth(aws_host='4o5lis9njd.execute-api.us-east-1.amazonaws.com',
                            aws_region='us-east-1',
                            aws_service='execute-api')

    r = requests.post(
        'https://vpce-09209225d0b441eac-azzwwnjl.execute-api.us-east-1.vpce.amazonaws.com/v1/poc/cfstack',
        headers={"Host":"4o5lis9njd.execute-api.us-east-1.amazonaws.com"},
        json=payload,
        auth=auth
    )
    print(r.text)

if __name__ == '__main__':

    args = get_args().__dict__

    # if len(sys.argv) != 3:
    #     print(f'\nError: expected two parameters.\nUse like for ex: $ ./{sys.argv[0].split("/")[-1]} <folder_to_compress> <site_id>\nNote: site_id later maps to https://site_id.poc.annalect.com\n')
    #     sys.exit(1)

    main(**args)
