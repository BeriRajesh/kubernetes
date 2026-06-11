"""
test policy POLICY_NAME
this scripts tests in an isolated manner:
    1. creates a temporary test role
    2. attaches the policy
    3. tests the condition of policy
"""


import json
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
POLICY_NAME_TO_TEST = "ann02ads-fbspina-secretsmanager-rbac-readonly"
POLICY_ARN_TO_TEST = f"arn:aws:iam::732327056170:policy/{POLICY_NAME_TO_TEST}"

class TestPolicySecretManager(helper_functions.IsolatedIamPolicyTestCaseBaseClass):

    # class variables
    PROFILE_TO_TEST = PROFILE_TO_TEST
    POLICY_NAME_TO_TEST = POLICY_NAME_TO_TEST
    POLICY_ARN_TO_TEST = POLICY_ARN_TO_TEST
    ADMIN_ROLE = ADMIN_ROLE

    secrets = None
    admin_secrets = None

    def setUp(self):
        """This is run before every test. Set up necessary objects that are needed for all tests."""

        pass

        ## example
        # self.secrets = get_client(profile_name="default", assume_role_arn=self.PROFILE_TO_TEST_ARN, client_type='secretsmanager') # type: botostubs.SecretsManager
        # self.admin_secrets = get_client(profile_name="default", assume_role_arn=self.ADMIN_ROLE, client_type="secretsmanager") # type: botostubs.SecretsManager

    def test_name(self):
        """ testing some xxxx action """
        pass
        ## example:
        ##
        ## 1. notice the try..except..finally
        ## 2. finally is important to clean whatever might have been created in the try

        # random_string = random_string_generator()
        # try:
        #     result = self.admin_secrets.create_secret(
        #         Name=random_string,
        #         SecretString=random_string,
        #         Tags=[
        #             {
        #                 'Key': 'access-project',
        #                 'Value': 'facebook-spi-na'
        #             },
        #             {
        #                 'Key': 'access-team',
        #                 'Value': 'datateam'
        #             }
        #         ]
        #     )
        #     result = self.secrets.get_secret_value(
        #         SecretId=random_string,
        #     )
        #     a=1
        # except Exception as error:
        #     self.assertTrue(error.response['Error']['Code']=='AccessDeniedException')
        # finally:
        #     result = self.admin_secrets.delete_secret(
        #         SecretId=random_string,
        #         ForceDeleteWithoutRecovery=True
        #     )

    # @unittest.skip
    def test_name2(self):
        """ testing some other yyyy action """
        pass



if __name__ == '__main__':
    # run tests
    unittest.main()
