import boto3

try:
    import botostubs
except:
    pass
import json
import random
import string
import time
import warnings
import unittest

DEFAULT_REGION = 'us-east-1'

class IsolatedIamPolicyTestCaseBaseClass(unittest.TestCase):
    # used by SetUpClass method to abort testing
    ABORT = False
    PROFILE_TO_TEST = None
    PROFILE_TO_TEST_ARN = None
    PROFILE_TO_TEST_TAGS = []

    def setUp(self):
        if self.ABORT:
            self.skipTest("ABORT flag is raised.")

    @classmethod
    def setUpClass(cls):
        """ setUpClass function for test suite
        creates test role, attaches trust policy and the policy to be tested
        """

        ## feel free to comment the next line, it is there only to hide a harmless warning
        warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)
        ###

        # we test with the temporary role name
        cls.PROFILE_TO_TEST = random_string_generator(prefix="testrole_")


        # we attach to the role
        #   - a trust_policy that allows our DEFAULT profile to assume that role
        #   - the policy we want to test
        # to be able to set everything up, our DEFAULT profile has to be able to assume an admin role in the test account

        admin_iam = get_client(profile_name="default", assume_role_arn=cls.ADMIN_ROLE, client_type='iam') # type: botostubs.IAM
        cls.admin_iam = admin_iam

        sts_client = get_client(profile_name="default", client_type='sts') # type: botostubs.STS
        whoami = sts_client.get_caller_identity()
        user_arn = whoami['Arn']

        print()
        print(f"Creating temporary role {cls.PROFILE_TO_TEST}... Allowing '{user_arn}' to assume this role.")
        results = cls.admin_iam.create_role(
            RoleName=cls.PROFILE_TO_TEST,
            AssumeRolePolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": user_arn
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }),
            Tags=cls.PROFILE_TO_TEST_TAGS
        )

        cls.PROFILE_TO_TEST_ARN = results['Role']['Arn']

        print()

        # create clients for secret manager
        # one client PROFILE_TO_TEST, and another helper client that assumes Admin in ADS account

        remaining_attempts = 5
        wait_seconds = 2
        while remaining_attempts >= 1:
            try:
                print(f'Attaching policy {cls.POLICY_NAME_TO_TEST} to temporary role {cls.PROFILE_TO_TEST}...')
                cls.admin_iam.attach_role_policy(PolicyArn=cls.POLICY_ARN_TO_TEST, RoleName=cls.PROFILE_TO_TEST)

                cls.admin_iam.get_role(RoleName=cls.PROFILE_TO_TEST)
                secrets = get_client(profile_name="default", assume_role_arn=cls.PROFILE_TO_TEST_ARN, client_type='secretsmanager') # type: botostubs.SecretsManager
                admin_secrets = get_client(profile_name="default", assume_role_arn=cls.ADMIN_ROLE, client_type="secretsmanager")  # type: botostubs.SecretsManager

                cls.secrets = secrets
                cls.admin_secrets = admin_secrets
                print('Success!!')
                break
            except:
                print(f"Waiting for roles {cls.PROFILE_TO_TEST} to be ready to assume... sleeping {wait_seconds}s")

            time.sleep(wait_seconds)
            remaining_attempts-=1
        else:
            print()
            print()
            print('There was a problem in assuming role loop. Please verify roles and trust relationship policy.')
            print('Setting ABORT flag to True.')
            cls.ABORT = True

        print()
        print()

    @classmethod
    def tearDownClass(cls):
        print()
        print()
        print(f'Removing policy {cls.POLICY_NAME_TO_TEST} from temporary role {cls.PROFILE_TO_TEST}...')
        cls.admin_iam.detach_role_policy(
            RoleName=cls.PROFILE_TO_TEST,
            PolicyArn=cls.POLICY_ARN_TO_TEST
        )
        print(f'Deleting temporary role {cls.PROFILE_TO_TEST}...')
        cls.admin_iam.delete_role(RoleName=cls.PROFILE_TO_TEST)

    # @unittest.skip
    def test_compare_policies(self):
        """ download policy and compare with saved one in policies directory """

        # get iam admin client
        admin_iam = get_client(profile_name="default", assume_role_arn=self.ADMIN_ROLE, client_type="iam") # type: botostubs.IAM

        policy = admin_iam.get_policy(
            PolicyArn=self.POLICY_ARN_TO_TEST
        )

        policy_version = admin_iam.get_policy_version(
            PolicyArn=self.POLICY_ARN_TO_TEST,
            VersionId=policy.get('Policy')["DefaultVersionId"]
        )

        policy_document_json = json.dumps(policy_version['PolicyVersion']['Document'], indent=0, default=str)

        saved_policy = json.dumps(json.load(open(f'policies/{self.POLICY_NAME_TO_TEST}.json')), indent=0, default=str)

        self.assertEqual(policy_document_json, saved_policy)

def random_string_generator(str_size=7, allowed_chars=string.ascii_letters, prefix="infratest_"):
    """generated a random string optionally with a custom prefix"""

    return prefix + ''.join(random.choice(allowed_chars) for x in range(str_size))

def get_client(assume_role_arn='', profile_name='default', client_type='secretsmanager', name=random_string_generator(), region=DEFAULT_REGION):
    """ returns an instance of boto3 with default profile, assuming admin role """

    if assume_role_arn:
        boto_sts = boto3.client('sts')
        stsresponse = boto_sts.assume_role(
            RoleArn=assume_role_arn,
            # RoleArn="arn:aws:iam::732327056170:role/admins",
            RoleSessionName=f'assume_role-session_name-{profile_name}'
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
        print("Not possible to create client", f"{assume_role_arn=}", f"{profile_name=}")

    return admin_secrets_client
