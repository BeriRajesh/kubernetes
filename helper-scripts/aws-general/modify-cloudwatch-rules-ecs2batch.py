""" donwload cloudwatch triggers """

import boto3
from collections import OrderedDict
from pprint import pprint
import json
import sys
from tabulate import tabulate
import argparse
import traceback




awsevents = boto3.client('events')

paginator = awsevents.get_paginator("list_rules")
rules = {}
for rule_block in paginator.paginate():
    # print(json.dumps(rule_block, indent=4))
    for rule in rule_block["Rules"]:
        # print(json.dumps(rule, indent=4))
        ruleName = rule["Name"]
        targets = awsevents.list_targets_by_rule(
            Rule=ruleName,
        )
        rules[rule["Name"]] = {}
        rules[rule["Name"]]['targets'] = []
        newtargets = {}
        newtargets["Targets"] = targets["Targets"]
        newtargets["Rule"] = ruleName
        for it, target in enumerate(targets["Targets"]):
            # print(json.dumps(target, indent=4))

            description = rule['Description'] if 'Description' in rule else '-'
            scheduleExpr = rule['ScheduleExpression'] if 'ScheduleExpression' in rule else '-'
            targetinput = target['Input'] if 'Input' in target else '-'
            targetarn = target['Arn'] if 'Arn' in target else '-'
            targetid = target["Id"]
            rules[rule["Name"]]['targets'].append([
                    ['Description', description],
                    ['ARN', targetarn],
                    ['State', rule['State']],
                    ['Schedule Expr.', scheduleExpr],
                    ['Input', targetinput],
                ])

            if targetinput != '-':
                targetinput_json = json.loads(targetinput)
                if targetarn == 'arn:aws:lambda:us-east-1:661095214357:function:annalectBatchjobs':
                    # to modify Input of target
                    try:
                        print({
                            'id': targetid,
                            'rulename': ruleName,
                            'taskdefinition': targetinput_json['taskDefinition'] if 'taskDefinition' in targetinput_json else "",
                        })
                        print(json.dumps(targetinput_json, indent=4))
                        print('change to')
                        target_modified = targetinput_json
                        if "command_with_args" in targetinput_json:
                            target_modified["jobCommand"] = targetinput_json["command_with_args"]
                            del targetinput_json["command_with_args"]
                        target_modified["appName"] = "prod_generic"
                        # if len(target_modified["jobCommand"]) > 0:
                        #     del target_modified["jobCommand"][0]
                        if "target_modified" in target_modified:
                            del target_modified["command_with_args"]
                        if "container_name" in target_modified:
                            del target_modified["container_name"]
                        if "Arn" in target_modified:
                            del target_modified["Arn"]
                        if "taskDefinition" in target_modified:
                            del target_modified["taskDefinition"]
                        target_modified["jobDefinition"] = "annalect_batchjobs_nosecretsentrypoint-job"
                        newtargetarn = "arn:aws:lambda:us-east-1:661095214357:function:annalect_job_submit:production"
                        # target_modified["timeout"] = 18000
                        print(json.dumps(target_modified, indent=4))
                        print(f"old target arn {targetarn}")
                        print(f"new target arn {newtargetarn}")
                        ans = input('y/N?')
                        if ans == "y":
                            # newtarget = target
                            newtargets['Targets'][it]["Input"] = json.dumps(targetinput_json)
                            newtargets['Targets'][it]["Arn"] = newtargetarn
                            response = awsevents.put_targets(**newtargets)
                            print(response)
                    except Exception as e:
                        traceback.print_exc()
                        input("xxxx ?")
                        pass
                elif targetarn == 'arn:aws:lambda:us-east-1:661095214357:function:jumpshotDataSync:prod':
                    try:
                        print({
                            'id': targetid,
                            'rulename': ruleName,
                            'taskdefinition': targetinput_json['taskDefinition'] if 'taskDefinition' in targetinput_json else "",
                        })
                        print(json.dumps(targetinput_json, indent=4))
                        print('change to')
                        target_modified = targetinput_json
                        if "command_with_args" in targetinput_json:
                            target_modified["jobCommand"] = targetinput_json["command_with_args"]
                            del targetinput_json["command_with_args"]
                        target_modified["appName"] = "prod_generic"
                        # if len(target_modified["jobCommand"]) > 0:
                        #     del target_modified["jobCommand"][0]
                        if "target_modified" in target_modified:
                            del target_modified["command_with_args"]
                        if "container_name" in target_modified:
                            del target_modified["container_name"]
                        if "Arn" in target_modified:
                            del target_modified["Arn"]
                        if "taskDefinition" in target_modified:
                            del target_modified["taskDefinition"]
                        target_modified["jobDefinition"] = "annalect_batchjobs-job-jumpshot"
                        newtargetarn = "arn:aws:lambda:us-east-1:661095214357:function:annalect_job_submit:production"
                        # target_modified["timeout"] = 18000
                        print(json.dumps(target_modified, indent=4))
                        print(f"old target arn {targetarn}")
                        print(f"new target arn {newtargetarn}")
                        ans = input('y/N?')
                        if ans == "y":
                            # newtarget = target
                            newtargets['Targets'][it]["Input"] = json.dumps(targetinput_json)
                            newtargets['Targets'][it]["Arn"] = newtargetarn
                            response = awsevents.put_targets(**newtargets)
                            print(response)
                    except Exception as e:
                        traceback.print_exc()
                        input("xxxx ?")
                        pass
        # break

# print(f'{len(rules.items())} rules found.')

# # print(rules.items())
# for ir, rulename in enumerate(rules.keys()):
#     print(f'<h2>Rule {ir + 1}: {rulename}</h2>')
#     for it, target in enumerate(rules[rulename]['targets']):
#         print(f'<h3>Target: {it+1}</h3>')
#         print(tabulate(target, tablefmt='html'))
#         print()






