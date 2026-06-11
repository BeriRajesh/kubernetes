#!/usr/bin/env python3

"""
Launch any lambda function with a payload
Has helper plugins to help with common Lambda functions
"""
import argparse
import base64
import boto3
import json
import logging
import sys

# showing INFO log lines
logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.INFO)


def get_args():
    parser = argparse.ArgumentParser(
        description='Helps showing IPs of hosts filtering by AWS tags, optionally also executing a command in each host')
    # parser.add_argument("action", choices=['list', 'patch'],
    #                     help="action to perform")
    # parser.add_argument("-v", "--verbose", default=0,
    #                     help="increase output verbosity", actions='count')
    parser.add_argument("-n", "--name",
                        help="Name of lambda function")

    parser.add_argument("-p", "--payload",
                        help="Payload for function")

    parser.add_argument("-q", "--qualifier",
                        help="Qualifier of function (ex.: production, 11, dev, versionX)")

    parser.add_argument("-c", "--command",
                        help="Command to override docker container")


    args = parser.parse_args()

    return args

def get_lambda_name():
    return 'annalect_job_submit'

def get_lambda_payload():
    command_list = [
        "/src/execute.sh",
        "dsdk_file_processing",
        "python",
        "dcmFileProcess.py",
        "dcm_account6049",
        "20181003",
        "ACTIVITY"
    ]
    command_list = [
        "/src/execute.sh",
        "wfDCM",
        "python",
        "dcmFileProcess.py",
        "dcm_account6049",
        "20181003",
        "ACTIVITY"
    ]

    command_list = [
        "/src/execute.sh",
        "wfDCM",
        "python",
        "dcmFileProcess.py",
        "dcm_account6049",
        "20181003",
        "ACTIVITY"
    ]
    # command_str = ",".join(command_list)
    # command_str = "/src/execute.sh,wfDCM,python,dcmFileProcess.py,WFDI,search"

    # if args.command is None:
    #     logger.error(
    #         f"Command argument not passed with the -c or --command option. Here's an example command string:"
    #         f"\n\n\{command_str}\n")
    #     sys.exit()

    payload = {
        "annalect_type": "cloudWatchEvent",
        "appName": "prod_generic",
        "environment": [
            {"name": "VALIDATION_SCRIPT", "value": "wfDCM-verify-monitorDcmFileProcess-search-display.sh"},
            {"name": "jobType", "value": "devops"},
            {"name": "topicArn", "value": "arn:aws:sns:us-east-1:661095214357:annalect_job_submit_prod_generic_batch_execution"},
        ],
        "jobCommand": command_list
    }

    # payload = {
    #     "annalect_type": "cloudWatchEvent",
    #     "appName": "prod_generic_ecs",
    #     "environment": [
    #         {"name": "NOVALIDATION", "value": "1"},
    #         {"name": "jobType", "value": "devops"},
    #         {"name": "topicArn", "value": "arn:aws:sns:us-east-1:661095214357:annalect_job_submit_prod_generic_batch_execution"},
    #     ],
    #     "jobCommand": command_list
    # }

    payload_str = json.dumps(payload)

    if args.payload is None:
        logger.error(
            f"Payload argument not passed with the -p or --payload option. Here's an example command string:"
            f"\n\n\t{payload_str}\n")
        sys.exit()

    return json.dumps(payload)

def invoke_lambda(**kwargs):
    """Invokes a AWS lambda function with a payload
    Arguments: dictionary with
        name: string
        paylod: JSON string with the payload
    """

    response = client.invoke(**kwargs)


if __name__ == '__main__':
    args = get_args()

    if args.name is None:
        args.name = get_lambda_name()

    if args.payload is None:
        sys.exit('ERROR: Please specify a payload.')
        args.payload = get_lambda_payload()

    if args.qualifier is None:
        logger.error(f"Please specify a qualifier with option -q or --qualifier")
        sys.exit()

    logger.info(f"Using qualifier '{args.qualifier}'")

    lambdaclient = boto3.client('lambda')
    args.payload = json.dumps(json.loads(args.payload))
    response = lambdaclient.invoke(
        FunctionName=args.name,
        InvocationType='RequestResponse',
        LogType='Tail',
        Payload=args.payload,
        Qualifier=args.qualifier
    )

    logger.info(base64.b64decode(response["ResponseMetadata"]["HTTPHeaders"]["x-amz-log-result"]).decode())
    # logger.info(response)
