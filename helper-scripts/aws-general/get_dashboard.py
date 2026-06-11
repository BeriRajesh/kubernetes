#!/usr/bin/env python3

"""writes the json of a dashboard to dashboards/<dashboard name>.json"""

import argparse
import os
import json
import sys

sys.path.append('../')
import lib.helper_functions as hf
import lib.amazon_helper as ah

AmazonHelper = ah.AmazonHelper()
boto3_session = AmazonHelper.session()

parser = argparse.ArgumentParser(
    description='Get the JSON of a dashboard identified by its name')
parser.add_argument("action", choices=['get', 'update'], help="action to perform (default sync)")
parser.add_argument("dashboard_name", help="name of the dashboard to work with")
parser.add_argument("-v", "--verbose", default=0,
                    help="increase output verbosity", action='count')
parser.add_argument("-p", "--profile", default='',
                    help="aws profile to use")

args = parser.parse_args()

hf.verbose = 1
dashboard_name = args.dashboard_name

output_path = 'dashboards'

dashboard_filename = "/".join([output_path, dashboard_name + '.json'])

if args.action == 'get':
    dashboard = json.loads(AmazonHelper.dashboards_get(dashboard_name)['DashboardBody'])
    with open(dashboard_filename, 'w') as fp:
        json.dump(dashboard, fp, indent=4)
        print('Written dashboard to {}'.format(dashboard_filename))

if args.action == 'update':
    with open(dashboard_filename, 'r') as fp:
        dashboard = fp.read()
        response = AmazonHelper.dashboard_update(dashboard_name, dashboard)
        print(response)
