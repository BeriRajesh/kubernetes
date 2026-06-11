""" test boundary policy ann-ann02ads-secretsmanager-manage-abac-policy """


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
POLICY_NAME_TO_TEST = "ann-ann02ads-secretsmanager-manage-abac-policy"
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

        admin_secrets_client = boto3.client(client_type,
            aws_access_key_id=newsession_id,
            aws_secret_access_key=newsession_key,
            aws_session_token=newsession_token,
            region_name=region
        )
    elif profile_name:
        session = boto3.session.Session(profile_name=profile_name, region_name=region)
        admin_secrets_client = session.client(client_type)
    else:
        print("Specify assume_role_arn or profile_name")
        sys.exit()

    return admin_secrets_client

class TestPolicySecretManager(unittest.TestCase):

    secrets = None
    admin_secrets = None

    @classmethod
    def setUpClass(cls):

        ## feell free to comment the next line, it is there only to hide a harmless warning
        warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)
        ###

        # create clients for secret manager
        # one client for PROFILE_TO_TEST, and another helper client that assumes Admin in ADS account
        try:
            cls.secrets = get_client(profile_name=PROFILE_TO_TEST, client_type='secretsmanager')
            cls.admin_secrets = get_client(profile_name="default", assume_role_arn=ADMIN_ROLE, client_type="secretsmanager")
        except:
            print(f"Error assuming role '{ADMIN_ROLE}' or using profile '{PROFILE_TO_TEST}'")
            sys.exit()

    # @unittest.skip
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

        policy_document_json = json.dumps(policy_version['PolicyVersion']['Document'], indent=4, default=str)
        saved_policy = json.dumps(json.load(open(f'policies/{POLICY_NAME_TO_TEST}.json')), indent=4, default=str)

        self.assertEqual(policy_document_json, saved_policy)

    @unittest.expectedFailure
    def test_create_without_tags(self):
        random_string = random_string_generator()

        result = self.secrets.create_secret(
            Name=random_string,
            SecretString=random_string,
            # Tags=[
            #     {
            #         'Key': 'string',
            #         'Value': 'string'
            #     },
            # ]
        )

    @unittest.expectedFailure
    def test_create_not_all_tags(self):
        random_string = random_string_generator()
        result = self.secrets.create_secret(
            Name=random_string,
            SecretString=random_string,
            Tags=[
                {
                    'Key': 'access-project',
                    'Value': 'facebook-spi-na'
                },
            ]
        )


    def test_create_with_appropriate_tags_values(self):
        random_string = random_string_generator()
        try:
            result = self.secrets.create_secret(
            # result = self.admin_secrets.create_secret(
                Name=random_string,
                SecretString=random_string,
                Tags=[
                    # {
                    #     'Key': 'access-project',
                    #     'Value': 'access-project'
                    # },
                    {
                        'Key': 'access-project',
                        'Value': 'facebook-spi-na'
                    },
                    # {
                    #     'Key': 'access-project',
                    #     'Value': 'facebook-spi-na'
                    # },
                    {
                        'Key': 'access-team',
                        'Value': 'datateam'
                    }
                ]
            )
        finally:
            result = self.admin_secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )

    @unittest.expectedFailure
    def test_create_with_appropriate_tags_values_and_extra_tag(self):
        random_string = random_string_generator()
        try:
            result = self.secrets.create_secret(
                Name=random_string,
                SecretString=random_string,
                Tags=[
                    {
                        'Key': 'access-project',
                        'Value': 'facebook-spi-na'
                    },
                    {
                        'Key': 'access-team',
                        'Value': 'datateam'
                    },
                    {
                        'Key': random_string,
                        'Value': random_string
                    },
                ]
            )
        finally:
            result = self.admin_secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )

    @unittest.expectedFailure
    def test_create_with_appropriate_tags_wrong_values(self):
        random_string = random_string_generator()
        try:
            result = self.secrets.create_secret(
                Name=random_string,
                SecretString=random_string,
                Tags=[
                    {
                        'Key': 'access-project',
                        'Value': 'facebook-spi-nax'
                    },
                    {
                        'Key': 'access-team',
                        'Value': 'datateam'
                    },
                ]
            )
        finally:
            result = self.secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )

    @unittest.expectedFailure
    def test_create_with_appropriate_tags_values_wrong_region(self):
        random_string = random_string_generator()
        client_wrong_region = get_client(profile_name=PROFILE_TO_TEST, client_type='secretsmanager', region="us-west-1")
        result = client_wrong_region.secrets.create_secret(
            Name=random_string,
            SecretString=random_string,
            Tags=[
                {
                    'Key': 'access-project',
                    'Value': 'facebook-spi-na'
                },
                {
                    'Key': 'access-team',
                    'Value': 'datateam'
                },
            ]
        )
        print(result)

    def test_put_secret_with_good_tags_good_region(self):
        try:
            random_string = random_string_generator()
            self.admin_secrets.create_secret(
                Name=random_string,
                SecretString=random_string,
                Tags=[
                    {
                        'Key': 'access-project',
                        'Value': 'facebook-spi-na'
                    },
                    {
                        'Key': 'access-team',
                        'Value': 'datateam'
                    },
                ]
            )

            response = self.secrets.put_secret_value(
                SecretId=random_string,
                SecretString=random_string,
            )
        finally:
            self.admin_secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )

    @unittest.expectedFailure
    def test_put_secret_with_missing_tags_good_region(self):
        try:
            random_string = random_string_generator()
            self.admin_secrets.create_secret(
                Name=random_string,
                SecretString=random_string,
                Tags=[
                    {
                        'Key': 'access-project',
                        'Value': 'facebook-spi-na'
                    }
                ]
            )

            response = self.secrets.put_secret_value(
                SecretId=random_string,
                SecretString=random_string,
            )
        finally:
            self.admin_secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )

    def test_get_random_password(self):
        response = self.secrets.get_random_password(
            PasswordLength=123
        )

    def test_list_all_secrets_with_good_tags(self):
        try:
            random_string = random_string_generator()
            self.admin_secrets.create_secret(
                Name=random_string,
                SecretString=random_string,
                Tags=[
                    {
                        'Key': 'access-project',
                        'Value': 'facebook-spi-na'
                    },
                    {
                        'Key': 'access-team',
                        'Value': 'datateam'
                    },
                ]
            )

            response = self.secrets.list_secrets(
                Filters=[
                    {
                        'Key': 'tag-key',
                        'Values': [
                            'access-project',
                        ]
                    },
                    {
                        'Key': 'tag-value',
                        'Values': [
                            'facebook-spi-na',
                        ]
                    },
                ],
            )
        finally:
            self.admin_secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )

    def test_list_all_secrets(self):
        try:
            random_string = random_string_generator()
            self.admin_secrets.create_secret(
                Name=random_string,
                SecretString=random_string,
            )
            response = self.secrets.list_secrets()
        finally:
            self.admin_secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )


    def test_get_secret_good_tags(self):
        try:
            random_string = random_string_generator()
            self.admin_secrets.create_secret(
                Name=random_string,
                SecretString=random_string,
                Tags=[
                    {
                        'Key': 'access-project',
                        'Value': 'facebook-spi-na'
                    },
                    {
                        'Key': 'access-team',
                        'Value': 'datateam'
                    },
                ]
            )
            response = self.secrets.get_secret_value(
                SecretId=random_string,
            )
        finally:
            self.admin_secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )


    @unittest.expectedFailure
    def test_get_secret_wrong_tags(self):
        try:
            random_string = random_string_generator()
            self.admin_secrets.create_secret(
                Name=random_string,
                SecretString=random_string,
            )
            response = self.secrets.get_secret_value(
                SecretId=random_string,
            )
        finally:
            self.admin_secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )

    # @unittest.expectedFailure
    def test_tag_resource_good_tags(self):
        try:
            random_string = random_string_generator()
            self.admin_secrets.create_secret(
                Name=random_string,
                SecretString=random_string,
                Tags=[
                    {
                        'Key': 'access-project',
                        'Value': 'facebook-spi-na'
                    },
                    {
                        'Key': 'access-team',
                        'Value': 'datateam'
                    },
                ]
            )
            response = self.secrets.tag_resource(
                SecretId=random_string,
                Tags=[
                    {
                        'Key': 'Environment',
                        'Value': "prod"
                    },
                ]
            )
        finally:
            self.admin_secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )

    @unittest.expectedFailure
    def test_tag_resource_missing_tags(self):
        try:
            random_string = random_string_generator()
            self.admin_secrets.create_secret(
                Name=random_string,
                SecretString=random_string,
            )
            response = self.secrets.tag_resource(
                SecretId=random_string,
                Tags=[
                    {
                        'Key': random_string,
                        'Value': random_string
                    },
                ]
            )
        finally:
            self.admin_secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )

    def test_untag_resource(self):
        try:
            random_string = random_string_generator()
            self.admin_secrets.create_secret(
                Name=random_string,
                SecretString=random_string,
                Tags=[
                    {
                        'Key': 'access-project',
                        'Value': 'facebook-spi-na'
                    },
                    {
                        'Key': 'access-team',
                        'Value': 'datateam'
                    },
                    {
                        'Key': 'Environment',
                        'Value': 'dev'
                    },
                ]
            )
            response = self.secrets.untag_resource(
                SecretId=random_string,
                TagKeys=[
                    'Environment',
                ]
            )
        finally:
            self.admin_secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )

    @unittest.expectedFailure
    def test_untag_resource_wrongtag(self):
        try:
            random_string = random_string_generator()
            self.admin_secrets.create_secret(
                Name=random_string,
                SecretString=random_string,
                Tags=[
                    {
                        'Key': 'access-project',
                        'Value': 'facebook-spi-na'
                    },
                    {
                        'Key': 'access-team',
                        'Value': 'datateam'
                    },
                    {
                        'Key': 'Environment',
                        'Value': 'dev'
                    },
                ]
            )
            response = self.secrets.untag_resource(
                SecretId=random_string,
                TagKeys=[
                    'access-team',
                ]
            )
        finally:
            self.admin_secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )

    @unittest.expectedFailure
    def test_untag_resource_missing_tags(self):
        try:
            random_string = random_string_generator()
            self.admin_secrets.create_secret(
                Name=random_string,
                SecretString=random_string,
                Tags=[
                    {
                        'Key': 'access-project',
                        'Value': 'facebook-spi-na'
                    },
                    {
                        'Key': random_string,
                        'Value': random_string
                    },
                ]
            )
            response = self.secrets.untag_resource(
                SecretId=random_string,
                TagKeys=[
                    random_string,
                ]
            )
        finally:
            self.admin_secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )





if __name__ == '__main__':


    # run tests
    unittest.main()
