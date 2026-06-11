"""Encrypt objects in a bucket by copying each object onto itself"""

import datetime
import json
import subprocess
import sys
import os
from typing import Any
import boto3
import botocore

import compliance_checks
from compliance_checks import AssumableRole

# only encrypt buckets on these account
only_accounts_dict = {}

only_accounts = ['257841078254']

# ignore this account from process
ignore_accounts = []

ignore_buckets = [
    'airflow-logs-257841078254-eu-west-1-emea-live',
    'annalect-emea-athena-dev',
]

bucket_object_owners: dict[str, set] = {}

assumable_roles = [ AssumableRole(role_name="Admin", account_id="257841078254")]

abroot_profile_name = 'ab-root'
abroot: object = boto3.session.Session(profile_name=abroot_profile_name)
abroot_res_s3: object = abroot.resource('s3')

abroot_profile_name = 'shashi-live'
shashilive: object = boto3.session.Session(profile_name=abroot_profile_name)
shashilive_res_s3: object = shashilive.resource('s3')
shashilive_client_s3: object = shashilive.client('s3')

resource_map = {'shashi-live': shashilive_res_s3, 'ab-root': abroot_res_s3}
resource_map_keys = resource_map.keys()

def load_log(fname: str) -> list[dict]:
    """Returns contents of fname as a list of dict"""

    with open(fname) as fp:
        lines = fp.read().split('\n')

    return [json.loads(line) for line in lines if line]


def log_action(value: dict[str, Any], log_type: str = "action_log") -> None:
    """Logs value to file"""

    value['timestamp'] = str(datetime.datetime.now())
    with open(f'{log_type}.log', 'a') as fp:
        json.dump(value, fp=fp, sort_keys=True, default=str)
        print(file=fp)

    print(value)

def encrypt_objects(object_list: list[dict], bucket_name: str, role: AssumableRole|None=None) -> None:
    """Encrypt a list of s3 objects"""

    # s3: object = role.session.client('s3')
    # manager = TransferManager(s3)
    # s3res: object = role.session.resource('s3')

    num_objects = len(object_list)
    print(
        f'Encrypting num_objects={num_objects} from {bucket_name=}', flush=True)


    res = None
    resname: str = ''

    for i, s3object in enumerate(object_list):
        object_key = s3object['Key']
        owner_name = None

        # tries all known resources per object key
        if resname:
            remaining_resources = {resname}.union(set(resource_map_keys)) - {resname}
        else:
            remaining_resources = set(resource_map_keys)
        while True:

            if not res and remaining_resources:
                resname = remaining_resources.pop()
                res = resource_map[resname]

            try:
                object_acl = res.ObjectAcl(bucket_name, object_key)
                owner_name = object_acl.owner['DisplayName']
                break
            except botocore.exceptions.ClientError as error:
                error_code = error.response['Error']['Code']
                if error_code == 'AccessDenied':
                    if len(remaining_resources) == 0:
                        log_action({
                            'log_type': 'object_owners',
                            'action': f'used all available resources {list(sorted(resource_map.keys()))}',
                            'bucket_name': bucket_name,
                            'key': object_key,
                            'account_id': 'emea-live',
                        })
                        break

                    resname = remaining_resources.pop()
                    res = resource_map[resname]

        if owner_name is None:
            bucket_object_owners[bucket_name].add('unknown')
            continue

        if bucket_name not in bucket_object_owners:
            bucket_object_owners[bucket_name] = set()
            bucket_object_owners[bucket_name].add(owner_name)
            print(f'{bucket_name=} {[o for o in bucket_object_owners[bucket_name]]}')

        # if owner_name in bucket_object_owners[bucket_name]:
        #     if i%100 == 0:
        #         print('. ', end='')
        #     continue
            # break


        # continue
        # object_info = s3res.Object(bucket_name, key)
        # e1 = object_info.server_side_encryption
        # print(object_acl)
        # if e1:
        #     #     # print("x ", end="")
        #     continue

        # manager.copy(bucket=bucket_name, key=key,
        #  copy_source={"Bucket": bucket_name, "Key": key}).result()

        #################################
        if ((owner_name == 'aws-omc-omg-ann-non-prod-emea-root'
            and len(object_acl.grants) == 1
            and object_acl.grants[0]['Grantee']['DisplayName'] == owner_name)

            or

            (owner_name == 'aws-omc-omg-ann-prod-emea-live'
            and len(object_acl.grants) == 1
            and object_acl.grants[0]['Grantee']['DisplayName'] == owner_name)):

            if owner_name == 'aws-omc-omg-ann-non-prod-emea-root':
                use_profile = 'ab-root'
            if owner_name == 'aws-omc-omg-ann-prod-emea-live':
                use_profile = 'shashi-live'

            cmd = f'aws s3 --no-progress --profile {use_profile} cp s3://{bucket_name}/{object_key} s3://{bucket_name}/{object_key} --sse'
            print(f'{owner_name=} {use_profile=} executing {cmd=}', flush=True)
            output = subprocess.run(cmd, shell=True, capture_output=True)

            print(output.stdout)
        else:
            print(f'Inspect object: aws s3api --profile ab-root get-object-acl --bucket {bucket_name} --key {object_key}')
            a=1
        #################################

        # object_info = s3res.Object(bucket_name, key)
        # e2 = object_info.server_side_encryption

        # message = f'Encrypted {bucket_name}/{key}, {e1} -> {e2}'
        # log_action({'bucket_name': bucket_name, 'account_id': role.account_id,
        # 'action': 'encrypted-object', 'message': message})
        # print('. ', end="")
        # if i % 1000 == 0:
        #     print(f'{i}/{num_objects} ', end="")
        # print(message)

        A = 2
        # print(result)

def encrypt_bucket_contents(bucket_name: str, role: AssumableRole|None=None) -> None:
    """Returns a list of awscli 'copy object onto itself' commands"""

    encryption_commands = []

    s3 = shashilive_client_s3 # role.session.client('s3')

    print(f'Encrypting object from emea live {bucket_name=} ')

    marker = ""
    object_list = []
    while marker is not None:
        params = dict(
            Bucket=bucket_name,
            # Marker='string',
            MaxKeys=1000,
        )

        if marker:
            params['ContinuationToken'] = marker

        response = s3.list_objects_v2(**params)

        encrypt_objects(response['Contents'],
                        role=role, bucket_name=bucket_name)
        marker = response.get('NextContinuationToken')
        a = 1

    a = 1

def get_encrypt_buckets(
    actions_taken: list[dict],
    only_accounts: list[str] | None = None,
    only_accounts_dict: dict[str, list[str]] | None = None,
    ignore_accounts: list[str] | None = None,
    ignore_buckets: list[str] | None = None) -> dict:
    """Return dictionary of type account_id: list of buckets whose contents need to be encrypted, only for accounts in only_accounts"""

    if not only_accounts:
        only_accounts = []
    if not ignore_accounts:
        ignore_accounts = []
    if not ignore_buckets:
        ignore_buckets = []
    if not only_accounts_dict:
        only_accounts_dict = {}

    encrypt_buckets: dict[str, list[str]] = {}
    for action in actions_taken:
        account_id = action['account_id']

        if only_accounts_dict:
            if os.path.isfile('whoami'):
                whoami = open('whoami').read()
                only_accounts = only_accounts_dict[whoami]

        if only_accounts and account_id not in only_accounts:
            continue

        if account_id in ignore_accounts:
            continue

        bucket_name = action['bucket_name']
        if ignore_buckets and bucket_name in ignore_buckets:
            continue

        action_performed = action['action']
        if action_performed != 'encrypted-bucket':
            continue

        if account_id not in encrypt_buckets:
            encrypt_buckets[account_id] = []

        encrypt_buckets[account_id].append(bucket_name)  # type: ignore

    return encrypt_buckets

def main() -> None:
    """Encrypt object in EMEA-Live's buckets with the same owner"""

    actions_taken = load_log(fname='action_log.log')

    encrypt_buckets = get_encrypt_buckets(
        actions_taken=actions_taken,
        only_accounts=only_accounts,
        only_accounts_dict=only_accounts_dict,
        ignore_accounts=ignore_accounts,
        ignore_buckets=ignore_buckets,
    )

    # for role in assumable_roles:
    #     role.get_boto3_session()

    #     if role.account_id not in encrypt_buckets:
    #         continue

    for bucket_name in encrypt_buckets['257841078254']:
        encrypt_bucket_contents(bucket_name=bucket_name)


if __name__ == "__main__":
    main()

    a=1
