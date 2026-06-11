#!/usr/bin/env python3

"""Get or Update datadog screenboards"""

import argparse
from datadog_helper import DatadogHelper
import json
import os
import sys

os.chdir(os.path.realpath(os.path.dirname(__file__)))
sys.path.append('../')
import lib.helper_functions as hf

datadogh = DatadogHelper()

parser = argparse.ArgumentParser(
    description='Get the JSON of a dashboard identified by its name')
parser.add_argument("action", choices=['get', 'update'], help="action to perform (default sync)")
parser.add_argument("screenboard_id", help="name of the dashboard to work with")
parser.add_argument("-v", "--verbose", default=0,
                    help="increase output verbosity", action='count')
parser.add_argument("-p", "--profile", default='',
                    help="aws profile to use")
parser.add_argument("-u", "--update-id", action="store_true",
                    help="Updates the `id` on the file")
args = parser.parse_args()

hf.verbose = 1

output_path = 'screenboards'

screenboard_id = args.screenboard_id

screenboard_filename = "/".join([output_path, screenboard_id + '.json'])

if args.action == 'get':
    screenboard = datadogh.get_screenboard(int(screenboard_id))
    with open(screenboard_filename, 'w') as fp:
        json.dump(screenboard, fp, indent=4)
        print('Written dashboard to {}'.format(screenboard_filename))

if args.action == 'update':
    boardtype = None
    try:
        screenboard_id = int(screenboard_id)
    except (ValueError, TypeError):
        # hf.dd(screenboard_filename, 1)
        with open(screenboard_filename, 'r') as fp:
            print('Non integer specified. Looking for file in `{}/`'.format(output_path))
            screenboard = json.loads(fp.read())
            if "board_title" in screenboard:
                boardtype = "screenboard"
                screenboard_title = screenboard["board_title"]
                screenboards = datadogh.datadog.api.Screenboard.get_all()
                for sb in screenboards['screenboards']:
                    if sb['title'] == screenboard_title:
                        screenboard_id = int(sb['id'])
                        break
                else:
                    screenboard_id = None
            elif "dash" in screenboard:
                boardtype = "timeboard"
                screenboard_title = screenboard["dash"]["title"]
                screenboards = datadogh.datadog.api.Timeboard.get_all()
                for sb in screenboards['dashes']:
                    if sb['title'] == screenboard_title:
                        screenboard_id = int(sb['id'])
                        break
                else:
                    screenboard_id = None
            else:
                sys.error("Type not recognized (not dashboard or screenboard")

    with open(screenboard_filename, 'r') as fp:
        dashboard = json.loads(fp.read())
        if boardtype == "screenboard":
            response = datadogh.update_screenboard(screenboard_id, dashboard)
            if "errors" in response:
                sys.exit(print(response))
            if "id" in response:
                dashboard["id"] = response["id"]
                if args.update_id:
                    with open(screenboard_filename, 'w') as fp:
                        fp.write(json.dumps(dashboard, indent=2))
        elif boardtype == "timeboard":
            response = datadogh.update_timeboard(screenboard_id, dashboard)
            if "errors" in response:
                sys.exit(print(response))

            if "id" in response["dash"]:
                dashboard["dash"]["id"] = response["dash"]["id"]
                if args.update_id:
                    with open(screenboard_filename, 'w') as fp:
                        fp.write(json.dumps(dashboard, indent=2))

    hf.debug(response, 1)


