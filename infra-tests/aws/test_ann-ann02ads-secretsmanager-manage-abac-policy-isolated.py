"""
test policy ann-ann02ads-secretsmanager-manage-abac-policy
this scripts tests in an isolated manner:
    1. creates a temporary test role
    2. attaches the policy
    3. tests the condition of policy
"""


import json
import sys
import unittest
# from: https://stackoverflow.com/questions/48160728/resourcewarning-unclosed-socket-in-python-3-unit-test
from pprint import pprint

try:
    import botostubs
except:
    pass

import helper_functions
from helper_functions import get_client, random_string_generator

PROFILE_TO_TEST = None #= "ann02-nonprod-ads-facebook-spi-na"

ADMIN_ROLE = "arn:aws:iam::732327056170:role/admin/ann02-nonprod-ads-admin"
POLICY_NAME_TO_TEST = "ann-ann02ads-secretsmanager-manage-abac-policy"
POLICY_ARN_TO_TEST = f"arn:aws:iam::732327056170:policy/{POLICY_NAME_TO_TEST}"
DEFAULT_REGION = 'us-east-1'

class TestPolicySecretManager(helper_functions.IsolatedIamPolicyTestCaseBaseClass):

    # class variables
    PROFILE_TO_TEST = PROFILE_TO_TEST
    PROFILE_TO_TEST_TAGS = [
        {
            'Key': 'access-project',
            'Value': 'facebook-spi-na'
        },
        {
            'Key': 'access-team',
            'Value': 'datateam'
        }
    ]


    POLICY_NAME_TO_TEST = POLICY_NAME_TO_TEST
    POLICY_ARN_TO_TEST = POLICY_ARN_TO_TEST
    ADMIN_ROLE = ADMIN_ROLE

    secrets = None
    admin_secrets = None

    def setUp(self):
        """This is run before every test"""

        self.secrets = get_client(profile_name="default", assume_role_arn=self.PROFILE_TO_TEST_ARN, client_type='secretsmanager') # type: botostubs.SecretsManager
        self.admin_secrets = get_client(profile_name="default", assume_role_arn=self.ADMIN_ROLE, client_type="secretsmanager") # type: botostubs.SecretsManager

    def test_create_without_tags(self):
        random_string = random_string_generator()

        try:
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
        except Exception as error:
            self.assertEqual(error.response['Error']['Code'], 'AccessDeniedException')
        finally:
            try:
                self.admin_secrets.delete_secret(
                    SecretId=random_string,
                    ForceDeleteWithoutRecovery=True
                )
            except Exception as error:
                if error.response['Error']['Code'] == 'ResourceNotFoundException':
                    pass

    def test_create_not_all_tags(self):
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
                        'Key': 'Project',
                        'Value': 'any'
                    }
                ]
            )
        except Exception as error:
            self.assertEqual(error.response['Error']['Code'], 'AccessDeniedException')
        finally:
            try:
                self.admin_secrets.delete_secret(
                    SecretId=random_string,
                    ForceDeleteWithoutRecovery=True
                )
            except Exception as error:
                if error.response['Error']['Code'] == 'ResourceNotFoundException':
                    pass

    def test_create_with_appropriate_tags_values(self):
        random_string = random_string_generator()
        try:
            result = self.secrets.create_secret(
            # result = self.admin_secrets.create_secret(
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
                        'Key': 'Project',
                        'Value': 'any'
                    }
                ]
            )
        finally:
            result = self.admin_secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )

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
                        'Key': 'Project',
                        'Value': 'any'
                    },
                    {
                        'Key': random_string,
                        'Value': random_string
                    },
                ]
            )
        except Exception as error:
            self.assertEqual(error.response['Error']['Code'], 'AccessDeniedException')
        finally:
            try:
                self.admin_secrets.delete_secret(
                    SecretId=random_string,
                    ForceDeleteWithoutRecovery=True
                )
            except Exception as error:
                if error.response['Error']['Code'] == 'ResourceNotFoundException':
                    pass

    def test_create_with_appropriate_tags_wrong_values(self):
        random_string = random_string_generator()
        try:
            result = self.secrets.create_secret(
                Name=random_string,
                SecretString=random_string,
                Tags=[
                    {
                        'Key': 'access-project',
                        'Value': 'wrong-value'
                    },
                    {
                        'Key': 'access-team',
                        'Value': 'datateam'
                    },
                    {
                        'Key': 'Project',
                        'Value': 'any'
                    },
                ]
            )
        except Exception as error:
            self.assertEqual(error.response['Error']['Code'], 'AccessDeniedException')
        finally:
            try:
                self.admin_secrets.delete_secret(
                    SecretId=random_string,
                    ForceDeleteWithoutRecovery=True
                )
            except Exception as error:
                if error.response['Error']['Code'] == 'ResourceNotFoundException':
                    pass

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
                    {
                        'Key': 'Project',
                        'Value': 'any'
                    },
                ]
            )

            response = self.secrets.list_secrets(
                Filters=[
                    {
                        'Key': 'tag-key',
                        'Values': [
                            'access-team',
                        ]
                    },
                    {
                        'Key': 'tag-value',
                        'Values': [
                            'datateam',
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
                    {
                        'Key': 'Project',
                        'Value': 'any'
                    },
                ]
            )
            response = self.secrets.get_secret_value(
                SecretId=random_string,
                VersionStage='AWSCURRENT'
            )
        finally:
            self.admin_secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )

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
        except Exception as error:
            self.assertEqual(error.response['Error']['Code'], 'AccessDeniedException')
        finally:
            try:
                self.admin_secrets.delete_secret(
                    SecretId=random_string,
                    ForceDeleteWithoutRecovery=True
                )
            except Exception as error:
                if error.response['Error']['Code'] == 'ResourceNotFoundException':
                    pass

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
                    {
                        'Key': 'Project',
                        'Value': 'any'
                    },
                ]
            )
            response = self.secrets.tag_resource(
                SecretId=random_string,
                Tags=[
                    {
                        'Key': 'Name',
                        'Value': random_string
                    },
                ]
            )
        finally:
            self.admin_secrets.delete_secret(
                SecretId=random_string,
                ForceDeleteWithoutRecovery=True
            )

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
                        'Key': 'Name',
                        'Value': random_string
                    },
                ]
            )
        except Exception as error:
            self.assertEqual(error.response['Error']['Code'], 'AccessDeniedException')
        finally:
            try:
                self.admin_secrets.delete_secret(
                    SecretId=random_string,
                    ForceDeleteWithoutRecovery=True
                )
            except Exception as error:
                if error.response['Error']['Code'] == 'ResourceNotFoundException':
                    pass

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
                    'access-project',
                ]
            )
        except Exception as error:
            self.assertEqual(error.response['Error']['Code'], 'AccessDeniedException')
        finally:
            try:
                self.admin_secrets.delete_secret(
                    SecretId=random_string,
                    ForceDeleteWithoutRecovery=True
                )
            except Exception as error:
                if error.response['Error']['Code'] == 'ResourceNotFoundException':
                    pass

if __name__ == '__main__':
    # run tests
    unittest.main()
