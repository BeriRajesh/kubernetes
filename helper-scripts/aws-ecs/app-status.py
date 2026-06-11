"""
scan status of applications
"""

import os
import sys
import argparse
import subprocess
import json
from pprint import pprint
import re
import requests
import getpass

import boto3
import pandas as pd

try:
    from tqdm import tqdm
except:
    print('Please install tqdm: pip3 install tqdm pandas')
    sys.exit(1)

ENVIRONMENTS = ['dev','qa','stg', 'prod', 'mgmt']

def get_args():
    parser = argparse.ArgumentParser(description='Description')

    # parser.add_argument("-n", "--name", default=None,
    #                 help="Name of ...")

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

def get_ecs_apps():
    apps = []
    valid_envs = ENVIRONMENTS
    SECRETS_BUCKET_NAME="annalect-cloud-vault"

    client = boto3.client('s3')
    response = client.list_objects_v2(
        Bucket=SECRETS_BUCKET_NAME,
    )

    for appobj in response['Contents']:
        key = appobj['Key']
        appobj_split = key.split("/")
        # pprint(appobj_split)
        try:
            is_container_secrets = appobj_split[0] == "container-secrets"
            env = appobj_split[1]
            app_name = appobj_split[2]
            valid_app = (
                is_container_secrets
                and
                env in valid_envs
            )
            if valid_app:
                apps.append(app_name)
        except Exception as error:
            # print(f'Could not determine app or env name for {key}: {error}')
            continue

    return list(set(apps))

def choose(lst, msg = None):
    lst.sort()
    for i, item in enumerate(lst):
        print(f'{i}. {item}')

    if msg:
        print(msg)
    option = input('Please input the number corresponding to your selection: ')
    if option != "":
        option = int(option)
        return lst[option]

    return None



def check_ecs(environment, app):
    ecs = boto3.client('ecs')
    clusters = ecs.list_clusters()

    print('# ECS')

    for clusterarn in clusters['clusterArns']:
        services = ecs.list_services(
            cluster=clusterarn
        )

        servicearns = services['serviceArns']
        app_env = f'{app}-{environment}'
        for servicearn in servicearns:
            if app_env in servicearn:
                service = ecs.describe_services(
                    cluster=clusterarn,
                    services=[
                        servicearn,
                    ]
                )

                events = service['services'][0]['events']
                deployments = service['services'][0]['deployments']


                # pprint(events)
                # pprint(deployments)
                if deployments:
                    print('\n## DEPLOYMENTS')
                    print(f'{app_env} has been deployed in the following dates:')
                    for i, deployment in enumerate(deployments):
                        taskDefinition = deployment['taskDefinition']
                        newTaskDefinition = ""
                        if i > 0:
                            if taskDefinition != deployments[i - 1]['taskDefinition']:
                                newTaskDefinition = "<---- NEW TASK DEFINITION"
                        print(f"- {deployment['createdAt']:%Y-%m-%d %H:%M} - Task Definition: {taskDefinition} {newTaskDefinition}")

                if events:
                    print('\n## EVENTS (< last 24h)')
                    for i, event in enumerate(events):
                        createdAt = event['createdAt']
                        tzname = createdAt.tzname()
                        yesterday = pd.Timestamp.now().tz_localize(tz=tzname) - pd.Timedelta(days=1)
                        if createdAt > yesterday:
                            print(f"- {createdAt:%Y-%m-%d %H:%M} - {event['message']}")

def get_override(environment, app):
    override_fname = 'serveroverride.cfg'
    print(f"## Downloading override: {override_fname} for {app}-{environment}")

    download_script = "download_docker_secrets.sh"
    if not os.path.exists(download_script):
        print(f"Script {download_script} not found in current path. Can't download {override_fname}.")
        return False

    subprocess.check_output(f'./download_docker_secrets.sh --file={override_fname} --QUIET=" " --force=true --env={environment} --app={app}', shell=True, stderr=subprocess.STDOUT)

    return override_fname

def get_domains_from_override(environment, app):
    # download override file
    override_fname = get_override(environment=environment, app=app)
    domains = []
    with open(override_fname) as fh:
        for line in fh:
            line = line.strip()
            # matches = valid_domain_regex.findall(line)
            if re.findall('\.([a-z]{2,4})', line):
                line_parts = line.split('=')
                # domain = line_parts[1].strip()
                domains.append(line)

    return domains

def check_domains(environment, app):
    domains = get_domains_from_override(environment, app)
    while True:
        domain_name = choose(domains, "Please select a domain to do a nslookup or leave empty to continue.")
        if not domain_name:
            print("You didn't choose a domain name. Continue!")
            break

        clean_domain = domain_name.split("=")[1].strip()
        clean_domain = re.sub("^https?://", "", clean_domain)
        clean_domain = clean_domain.split("/")[0]

        exit_code = subprocess.call(f"nslookup {clean_domain}", shell=True)
        print(f"Exit code was {exit_code}.")

def check_sso():
    """ check a good response from SSO """
    print("# SSO")

    url = f"https://apps.annalect.com"
    print(f"Checking {url}")
    r = requests.get(url)
    status_code = r.status_code
    if status_code == 200:
        print(f'Domain is available with code {status_code}.')
    else:
        print(f'Request to domain return status_code: {status_code}.')


    username = input("Input a username to test PROD SSO:")
    password = getpass.getpass()

    if not username or not password:
        print('Not checking SSO because Username or Password left empty.')
        return None

    url = f"https://access.annalect.com/am/amapi/user/login/{username}?p={password}"

    r = requests.post(url)
    r_json = r.json()

    status_code = r.status_code
    sid = r.json
    if status_code == 200:
        print('Request to SSO was successful.')
    else:
        print(f'Request to SSO return status_code: {status_code}.')

    if r_json['sid'] != "":
        print(f'SID is not empty: {r_json["sid"]}')
    else:
        print(f'SID empty')


def main():
    """ Perform tests """

    check_sso()

    environments = ENVIRONMENTS
    app_name = choose(get_ecs_apps(), "Select application:")
    environment_name = choose(environments, "Select environment:")

    if not environment_name or not app_name:
        print(f'Not checking ECS because environment or application was not specified.')
        print(f'Not checking domains because environment or application was not specified.')
    else:
        check_ecs(environment=environment_name, app=app_name)
        check_domains(environment=environment_name, app=app_name)


if __name__ == "__main__":
    args = get_args()

    main()