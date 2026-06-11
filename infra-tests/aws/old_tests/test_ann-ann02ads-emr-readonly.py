""" test boundary policy ann-ann02ads-emr-readonly """


import json
import os
import random
import string
import sys
import unittest

from pprint import pprint

# from: https://stackoverflow.com/questions/48160728/resourcewarning-unclosed-socket-in-python-3-unit-test
import warnings
# warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)
###

import boto3

PROFILE_TO_TEST = "ann02-nonprod-ads-facebook-spi-na"
ADMIN_ROLE = "arn:aws:iam::732327056170:role/admin/ann02-nonprod-ads-admin"
DEFAULT_REGION = 'us-east-1'
POLICY_NAME_TO_TEST = "ann-ann02ads-emr-readonly"
POLICY_ARN_TO_TEST = f"arn:aws:iam::732327056170:policy/{POLICY_NAME_TO_TEST}"

def random_string_generator(str_size=7, allowed_chars=string.ascii_letters):
    return "infratest_" + ''.join(random.choice(allowed_chars) for x in range(str_size))

def get_client(assume_role_arn='', profile_name='default', client_type='secretsmanager', name=random_string_generator(), region=DEFAULT_REGION):
    """ returns an instance of boto3 with default profile, assuming admin role """

    if assume_role_arn:
        boto_sts = boto3.client('sts')
        stsresponse = boto_sts.assume_role(
            RoleArn=assume_role_arn,
            # RoleArn="arn:aws:iam::732327056170:role/admins",
            RoleSessionName='ads-admin'
        )

        newsession_id = stsresponse["Credentials"]["AccessKeyId"]
        newsession_key = stsresponse["Credentials"]["SecretAccessKey"]
        newsession_token = stsresponse["Credentials"]["SessionToken"]

        admin_client = boto3.client(client_type,
            aws_access_key_id=newsession_id,
            aws_secret_access_key=newsession_key,
            aws_session_token=newsession_token,
            region_name=region
        )
    elif profile_name:
        session = boto3.session.Session(profile_name=profile_name, region_name=region)
        admin_client = session.client(client_type)

    return admin_client

class TestPolicySecretManager(unittest.TestCase):

    emr = None

    @classmethod
    def setUpClass(cls):

        ## feell free to comment the next line, it is there only to hide a harmless warning
        warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)
        ###

        # create clients for secret manager
        # one client for PROFILE_TO_TEST, and another helper client that assumes Admin in ADS account
        try:
            cls.emr = get_client(profile_name=PROFILE_TO_TEST, client_type='emr')

        except:
            print(f"Error using profile '{PROFILE_TO_TEST}'")
            sys.exit()

    @unittest.skip
    def test_compare_policies(self):
        """ download policy and compare with saved one in policies directory """

        # get iam admin client
        admin_iam = get_client(profile_name="default", assume_role_arn=ADMIN_ROLE, client_type="iam")

        policy = admin_iam.get_policy(
            PolicyArn=POLICY_ARN_TO_TEST
        )

        policy_version = admin_iam.get_policy_version(
            PolicyArn=POLICY_ARN_TO_TEST,
            VersionId=policy.get('Policy')["DefaultVersionId"]
        )

        policy_document_json = json.dumps(policy_version['PolicyVersion']['Document'], indent=0, default=str)

        saved_policy = json.dumps(json.load(open(f'policies/{POLICY_NAME_TO_TEST}.json')), indent=0, default=str)

        self.assertEqual(policy_document_json, saved_policy)

    def test_list_clusters(self):
        result = self.emr.list_clusters()


if __name__ == '__main__':
    # run tests
    unittest.main()
