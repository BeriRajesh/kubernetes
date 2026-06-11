#!/usr/bin/env python3

"""update tags on AWS resource based on name of resource"""

import argparse
import sys

sys.path.append('../')
import lib.helper_functions as hf
import lib.amazon_helper as ah


parser = argparse.ArgumentParser(description='Export resources from AWS')
parser.add_argument("type", choices=['all', 'rds'], nargs='?', default='all',
                    help="Action to perform (defaults to all)")
parser.add_argument("-v", "--verbose", default=0, help="Increase output verbosity", action='count')
parser.add_argument("-p", "--profile", default='', help="AWS profile to use. Defaults to 'default'")
parser.add_argument("-i", "--interactive", default='', help="Presents a prompt before executing copying commands to"
                                                            "source files", action='store_true')
args = parser.parse_args()

hf.verbose = args.verbose

AmazonHelper = ah.AmazonHelper()
boto3_session = AmazonHelper.session()

if args.type == 'rds' or args.type == 'all':
    AmazonHelper.update_tags_rds()