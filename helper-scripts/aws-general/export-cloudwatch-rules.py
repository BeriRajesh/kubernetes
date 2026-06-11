""" donwload cloudwatch triggers """

import boto3
from collections import OrderedDict
from pprint import pprint
import json
import sys
from tabulate import tabulate
import argparse
import re
import os

awsevents = boto3.client('events')

def get_args():
    parser = argparse.ArgumentParser(description='Helper to export cloudwatch rules, tests or cron expressions')

    parser.add_argument("-w", "--what", choices=['all', 'cron', 'tests'], default='all',
                    help="What to do")

    parser.add_argument("-o", "--output", default='.',
                    help="Output path")

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

def main():
    paginator = awsevents.get_paginator("list_rules")
    rules = {}
    raw_rules = []
    for rule_block in paginator.paginate():
        # print(json.dumps(rule_block, indent=4))
        for rule in rule_block["Rules"]:
            # print(json.dumps(rule, indent=4))
            targets = awsevents.list_targets_by_rule(
                Rule=rule["Name"],
            )
            rules[rule["Name"]] = {}
            rules[rule["Name"]]['targets'] = []
            for target in targets["Targets"]:
                # print(json.dumps(target, indent=4))

                description = rule['Description'] if 'Description' in rule else '-'
                scheduleExpr = rule['ScheduleExpression'] if 'ScheduleExpression' in rule else '-'
                targetinput = target['Input'] if 'Input' in target else '-'
                targetarn = target['Arn'] if 'Arn' in target else '-'
                rules[rule["Name"]]['targets'].append([
                        ['Description', description],
                        ['ARN', targetarn],
                        ['State', rule['State']],
                        ['Schedule Expr.', scheduleExpr],
                        ['Input', targetinput],
                    ])

                if args.what == 'tests' and len(targets["Targets"]) == 1:
                    output_path = args.output
                    content = {
                        "targetarn": targetarn,
                        "input": targetinput
                    }
                    name = f'test{rule["Name"]}.json'.replace(" ","_")
                    output_file = os.path.join(output_path, name)
                    json.dump(obj=content, fp=open(output_file, mode='w'))

            raw_rules.append(rule)
    if args.what == 'all':
        return rules
    elif args.what == 'cron':
        return raw_rules
if __name__ == "__main__":
    args = get_args()
    rules = main()

if args.what == 'all':
    print(f'{len(rules.items())} rules found.')

    # print(rules.items())
    for ir, rulename in enumerate(rules.keys()):
        print(f'<h2>Rule {ir + 1}: {rulename}</h2>')
        for it, target in enumerate(rules[rulename]['targets']):
            print(f'<h3>Target: {it+1}</h3>')
            print(tabulate(target, tablefmt='html'))
            print()

elif args.what == 'cron':
    for rule in rules:
        scheduleExpr = rule['ScheduleExpression'] if 'ScheduleExpression' in rule else None

        if scheduleExpr is None:
            continue

        cron_content = re.search(r"cron\((.*)\)", scheduleExpr)
        if cron_content is None:
            continue
        cron_content = cron_content.group(1)


        description = rule['Description'] if 'Description' in rule else rule["Name"]
        print(f"{cron_content} {description}")




