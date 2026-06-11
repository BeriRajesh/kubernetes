#!/bin/env python3

import sys
import os
import json
import subprocess
import base64

import argparse

import boto3
events = boto3.client('events')


def get_args():
    parser = argparse.ArgumentParser(description='Script to invoke a test.json')

    parser.add_argument("test_name", nargs='?', default=None,
                    help="Name of test (default none)")

    parser.add_argument("-l", "--lambda-function", default=None,
                    help="Lambda function name or ARN")

    parser.add_argument("-j", "--json-payload", default=None,
                    help="JSON payload to pass to the lambda")

    parser.add_argument("-f", "--json-file", default=None,
                    help="File containing the JSON payload")

    parser.add_argument("-q", "--qualifier", default='production',
                    help="Function qualifier")

    parser.add_argument("-r", "--rule", default=None,
                    help="Fetches payload and function from CloudWatch Event rule name")

    parser.add_argument("-d", "--debug_options", action='store_true',
                    help="Debug options passed and exit")

    args = parser.parse_args()

    # if not any(vars(args).values()):
    #     parser.parse_args(['--help'])
    #     # parser.error('No arguments provided.')

    if args.debug_options:
        print(args)
        sys.exit()

    return args

args = get_args()

if args.test_name == []:
    args.test_name = None

input_file = args.test_name
qualifier = args.qualifier

if args.rule:
    rule_json = events.describe_rule(Name=args.rule)
    targets_json = events.list_targets_by_rule(Rule=args.rule).get('Targets')

    args.lambda_function = targets_json[0]['Arn']
    args.json_payload = targets_json[0]['Input']

    lambda_split = args.lambda_function.split(":")
    if len(lambda_split) != 8:
        print(f"Lambda {args.lambda_function} does not appear to have the correct length... missing qualifier?")
        sys.exit(1)


elif args.test_name is None and args.lambda_function is None:
    print('Please either specify the test file or specify a lambda function. Please check the --help option.')
    sys.exit(0)


if input_file is not None:
    print(f'Input file is\n: {input_file}')
    json_content = json.load(fp=open(input_file))
    target_input = json_content['input']
    target_arn = json_content['targetarn']

if args.lambda_function is None:
    print('Please specify a lambda function.')
    sys.exit(0)
else:
    target_arn = args.lambda_function

if args.json_payload is None and args.json_file is None:
    print('Please specify a JSON payload or a JSON file.')
    sys.exit(0)

if args.json_payload:
    target_input = args.json_payload
else:
    target_input = open(args.json_file).read()

qualifier_str = ''
if qualifier is not None and ":" in target_arn:
    *pieces, orig_qualifier = target_arn.split(":")
    pieces.append(qualifier)
    target_arn = ":".join(pieces)
else:
    qualifier_str == f'--qualifier {qualifier}'


# AWS=$(which aws)

cmd = (
    f"$(which aws) lambda invoke --function-name '{target_arn}' "
    f"--log-type Tail --payload '{target_input}' {qualifier_str}"
    # f"--qualifier {qualifier} "
    "out.txt"
)
print(f"Command:\n {cmd}")
output = subprocess.check_output(cmd, shell=True).strip()

output_json = json.loads(output)

print('Output:\n')
print(
    base64.b64decode(str(output_json['LogResult'])).decode("utf-8")
)

# "${AWS}" lambda invoke --function-name "${LAMBDA_FUNCTION_NAME}" --log-type Tail \
#     --payload fileb://${JSON_TESTFILE} out.txt \
#     | jq -r '.LogResult' | base64 -d

# --qualifier prod