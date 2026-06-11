""" script to check Account-Compliance-Attestation """

from dataclasses import dataclass, field
import datetime
from doctest import REPORT_CDIFF
import os
import sys
import time
import boto3
import json
from typing import Union
import botocore
import configparser
import pandas as pd

# s3 = boto3.client('s3')
# s3res = boto3.resource('s3')
sts = boto3.client('sts')

scan_regions = [
    "me-south-1",
    "us-east-1",
    "eu-west-1",
]


@dataclass
class AssumableRole:
    """Class to handle assuming roles in an account
    Creates files to store temporary credentials.
    Handles MFA authentication.
    """

    account_id: str
    role_name: str
    mfa_code: str = "999999"
    session: boto3.session = object  # type: ignore
    account_alias: Union[None, str] = None
    profiles: configparser.ConfigParser = configparser.ConfigParser()
    config_profile_fname: str = '~/.aws/config'
    mfa_device_arn: str = 'arn:aws:iam::661095214357:mfa/anmichel.rodriguez@annalect.com'
    max_duration: int = 12*60*60
    region: Union[None, str] = None
    profile_name: Union[None, str] = None

    def __post_init__(self):
        """1. expands ~ to absolute home path"""
        self.config_profile_fname = os.path.expanduser(self.config_profile_fname)

    def build_role_arn(self) -> str:
        return f"arn:aws:iam::{self.account_id}:role/{self.role_name}"

    def get_mfa_code(self) -> str:
        """Get mfa code from user"""

        self.mfa_code = input("Please input your MFA code:")

        return self.mfa_code

    def load_profiles_config(self) -> object:
        """Returns AWS profiles config as ini file"""

        if not self.profiles.sections():
            # self.profiles = configparser.ConfigParser()

            if os.path.isfile(os.path.realpath(self.config_profile_fname)):
                self.profiles.read(self.config_profile_fname)

        return self.profiles

    def get_boto3_session(self, force_new_credentials=False) -> object:
        """Returns boto3 session for the assummed self.role_name from self.account_id"""

        self.load_profiles_config()

        expired_token = False
        if force_new_credentials:
            expired_token = True

        role_name = f"{self.account_id}-{self.role_name}"
        self.profile_name = profile_name = f'profile {role_name}'
        profile_name = self.profile_name

        role_arn = self.build_role_arn()

        while True:
            try:
                # need to put False since re-using the credentials fails
                if False and profile_name in self.profiles and expired_token == False:
                    self.aws_access_key_id = self.profiles[profile_name]['aws_access_key_id']
                    self.aws_secret_access_key = self.profiles[profile_name]['aws_secret_access_key']
                    self.aws_session_token = self.profiles[profile_name]['aws_session_token']
                else:
                    params = dict(
                        RoleArn=role_arn,
                        RoleSessionName="compliance-check",
                        # SerialNumber=self.mfa_device_arn,
                        # TokenCode=self.mfa_code,
                        # DurationSeconds=self.max_duration,
                    )
                    # printj(params)
                    response = sts.assume_role(**params)
                    self.aws_access_key_id = response['Credentials']['AccessKeyId']
                    self.aws_secret_access_key = response['Credentials']['SecretAccessKey']
                    self.aws_session_token = response['Credentials']['SessionToken']

                    # if profile_name not in self.profiles:
                        # self.profiles[profile_name] = {}

                    # self.profiles[profile_name]['aws_access_key_id'] = self.aws_access_key_id
                    # self.profiles[profile_name]['aws_secret_access_key'] = self.aws_secret_access_key
                    # self.profiles[profile_name]['aws_session_token'] = self.aws_session_token

                    self.profiles[profile_name] = {}
                    self.profiles[profile_name]['source_profile'] = 'default'
                    self.profiles[profile_name]['role_arn'] = role_arn


                params = dict(
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    aws_session_token=self.aws_session_token,
                )
                if self.region:
                    params['region_name'] = self.region

                session = boto3.session.Session(**params)  # type: ignore

                account_aliases = session.client('iam').list_account_aliases()[
                    'AccountAliases']
                if account_aliases:
                    self.account_alias = account_aliases[0]
                else:
                    self.account_alias = f"{self.account_id}-NoAlias"

                # try:
                #     self.account_alias = session.client('iam').list_account_aliases()['AccountAliases'][0]
                # except Exception as error:
                #     self.account_alias = f'Could not fetch: {error}'

                self.session = session

                break

            except botocore.exceptions.ParamValidationError as error:  # type: ignore
                print(error)
                input('?')
            except botocore.exceptions.ClientError as error:  # type: ignore
                print(f"{error.response['Error']['Code']=}")
                print(f'{self.account_id=}')
                print(f'{self.role_name=}')
                print(f'{self.mfa_code=}')
                if error.response['Error']['Code'] == 'AccessDenied':
                    print("Access denied, let's try a new mfa_code")
                    self.get_mfa_code()
                elif error.response['Error']['Code'] == 'ExpiredToken':
                    print('ERROR: Cached session expired')
                    expired_token = True
                    self.get_mfa_code()
                    continue
                elif error.response['Error']['Code'] == 'InvalidClientTokenId':
                    print(f'ERROR: {error}')
                    expired_token = True
                    self.get_mfa_code()
                    continue
                else:
                    raise error
            except Exception as error:
                printj(error)
                raise

        with open(self.config_profile_fname, 'w') as configfile:
            self.profiles.write(configfile)

        return self.session


assumable_roles = [
    # ad-hoc accounts
    # accuen, aws-omc-omg-ann-non-prod-accuen
    AssumableRole(role_name="admins",
                  account_id="348194362585",),
    # emea-live, aws-omc-omg-ann-prod-emea-live
    AssumableRole(role_name="Admin",
                  account_id="257841078254",),
    AssumableRole(role_name="Admin",
                  account_id="005533607590",),  # emea-root,
    # emea-dev, aws-omc-omg-ann-non-prod-emea-dev
    AssumableRole(role_name="Admin",
                  account_id="340659147180",),
    # elde, accuentds, aws-omc-omg-ann23-non-prod-elde
    AssumableRole(role_name="ny-admins",
                  account_id="345951534139",),

    AssumableRole(role_name="admin/ann01-tioprod-admin",
                  account_id="661095214357",),
    AssumableRole(role_name="admin/ann02-nonprod-ads-admin",
                  account_id="732327056170",),
    AssumableRole(role_name="admin/ann03-nonprod-assets-admin",
                  account_id="952850296487",),
    AssumableRole(role_name="admin/ann04-sandbox-admin",
                  account_id="091021251638",),
    AssumableRole(role_name="admin/ann05-nonprod-aadl-admin",
                  account_id="571875174059",),
    AssumableRole(role_name="admin/ann06-prod-healthcaredata-admin",
                  account_id="431361936815",),
    AssumableRole(role_name="admin/ann07-prod-commerce-graph-admin",
                  account_id="914006819694",),
    AssumableRole(role_name="admin/ann08-dev-admin",
                  account_id="408764662748",),
    AssumableRole(role_name="admin/ann09-prod-fbcapig-admin",
                  account_id="153175995455",),
    AssumableRole(role_name="admin/ann10-prod-private-admin",
                  account_id="288489547540",),
    AssumableRole(role_name="admin/ann25-prod-fsd-admin",
                  account_id="895757120061",),
    AssumableRole(role_name="admin/ann27-prod-amd-admin",
                  account_id="175813369871",),
    AssumableRole(role_name="admin/ann28-prod-invgrf-admin",
                  account_id="366146577560",),
]


@dataclass
class AccountAttestation:
    """Performs account attestation checks"""

    assume_role: AssumableRole
    buckets_encryption: list = field(default_factory=list)
    rds_encryption: list = field(default_factory=list)
    redshift_encryption: list = field(default_factory=list)
    account_id: Union[str, None] = None
    account_alias: Union[str, None] = None
    region: Union[str, None] = None
    encrypt_buckets: bool = False
    ignore_exceptions: list = field(default_factory=list)

    def __post_init__(self):
        """Start session for assume_role"""
        if self.region:
            self.assume_role.region = self.region

        self.assume_role.get_boto3_session()
        self.account_alias = self.assume_role.account_alias
        self.account_id = self.assume_role.account_id

    def log_action(self, value: dict, log_type: str = "action_log") -> None:
        """Logs value to file"""

        value['timestamp'] = str(datetime.datetime.now())
        with open(f'{log_type}.log', 'a') as fp:
            json.dump(value, fp=fp, sort_keys=True, default=str)
            print(file=fp)

        print(value)

    def check_s3_encryption(self, show_progress=True) -> None:
        """Checks bucket encryption for all assumable roles"""

        assumed_role = self.assume_role

        s3res = assumed_role.session.resource('s3')  # type: ignore
        s3 = assumed_role.session.client('s3')  # type: ignore

        buckets = []
        try:
            buckets_client = s3.list_buckets()
            buckets = s3res.buckets.all()
        except botocore.exceptions.ClientError as error:  # type: ignore
            error_code = error.response['Error']['Code']
            if error_code == 'InvalidToken':
                self.log_action(
                    {
                        'action': 's3.list_buckets',
                        'resource_type': 'S3',
                        'identifier': 'S3',
                        'error': error_code,
                        'account_id': self.account_id,
                        'region': self.region,
                    },
                    log_type="warnings"
                )
                return

        for bucket in buckets:
            # if bucket.name not in [
            #     'ann01-tioprod-ams1-s3inventory',
            #     'ann01-tioprod-ams1-s3analytics',
            #     'ann01-tioprod-ams1-loadbalancer-logs',
            #     'annalect-mena-orchestrateplatform',
            #     'annalect-mena-devorchestrateplatform',
            #     'ann01-tioprod-ams1-s3access-logs',
            # ]:
            #     continue
            try:
                encryption = self.check_bucket_encryption(bucket=bucket.name)
            except botocore.exceptions.ClientError as error:  # type: ignore
                error_code = encryption = error.response['Error']['Code']

                if encryption in self.ignore_exceptions:
                    msg = f'WARNING: Ignoring exception {encryption} for bucket {bucket.name}'
                    self.log_action(
                        {
                            'action': 'ignored-bucket',
                            'resource_type': 'S3',
                            'identifier': bucket.name,
                            'error': error_code,
                            'account_id': self.account_id,
                            'region': self.region,
                        },
                        log_type="warnings"
                    )
                    print(msg)
                    continue

                if encryption == 'ServerSideEncryptionConfigurationNotFoundError':
                    if self.encrypt_buckets:
                        sse_algorithm = 'AES256'
                        s3.put_bucket_encryption(
                            Bucket=bucket.name,
                            # ContentMD5='string',
                            # ChecksumAlgorithm='CRC32'|'CRC32C'|'SHA1'|'SHA256',
                            ServerSideEncryptionConfiguration={
                                'Rules': [
                                    {
                                        'ApplyServerSideEncryptionByDefault': {
                                            'SSEAlgorithm': sse_algorithm,
                                        },
                                        # 'BucketKeyEnabled': True|False
                                    },
                                ]
                            },
                            # ExpectedBucketOwner='string'
                        )
                        self.log_action(
                            {
                                'action': 'encrypted-bucket',
                                'bucket_name': bucket.name,
                                'sse_algorithm': sse_algorithm,
                                'account_id': self.account_id,
                                'region': self.region,
                            }
                        )
                        try:
                            encryption = self.check_bucket_encryption(
                                bucket=bucket.name)
                        except botocore.exceptions.ClientError as error: # type: ignore
                            encryption = error.response['Error']['Code']

            row = {
                'encryption': encryption,
                'account_id': assumed_role.account_id,
                'account_alias': assumed_role.account_alias,
                'bucket_name': bucket.name,
                'region': self.region,
            }

            self.buckets_encryption.append(row)

            if show_progress:
                print(row)

    def check_bucket_encryption(self, bucket: str) -> Union[str, bool]:
        """ check if bucket is encrypted by default """

        s3 = self.assume_role.session.client('s3')
        bucket_encryption = s3.get_bucket_encryption(
            Bucket=bucket,
        )

        for rule in bucket_encryption['ServerSideEncryptionConfiguration']['Rules']:
            algo = rule['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
            if algo:
                return algo

        return False

    def check_rds_encryption(self, show_progress=True) -> None:
        """Checks rds encryption for all assumable roles"""

        assumed_role = self.assume_role

        # awsres = assumed_role.session.resource('rds')
        client = assumed_role.session.client('rds')

        resources = []
        try:
            resources = client.describe_db_clusters(
                MaxRecords=100
            )
        except botocore.exceptions.ClientError as error: # type: ignore
            error_code = error.response['Error']['Code']
            if error_code == 'InvalidClientTokenId':
                self.log_action(
                    {
                        'action': 'describe_db_clusters',
                        'resource_type': 'RDS',
                        'identifier': 'RDS',
                        'error': error_code,
                        'account_id': self.account_id,
                        'region': self.region,
                    },
                    log_type="warnings"
                )
                return
            else:
                row = {
                    'encryption': error_code,
                    'account_id': assumed_role.account_id,
                    'account_alias': assumed_role.account_alias,
                    'cluster_identifier': 'describe_db_clusters',
                    'region': self.region,
                }

                self.rds_encryption.append(row)

                if show_progress:
                    print(row)
                return

        if resources.get('Marker'):
            input('This account has many clusters!')

        for resource in resources['DBClusters']:
            try:
                encryption = resource.get('StorageEncrypted')
            except botocore.exceptions.ClientError as error: # type: ignore
                encryption = error.response['Error']['Code']

            identifier = resource.get('DBClusterIdentifier')

            row = {
                'encryption': encryption,
                'account_id': assumed_role.account_id,
                'account_alias': assumed_role.account_alias,
                'cluster_identifier': identifier,
                'region': self.region,
            }

            self.rds_encryption.append(row)

            if show_progress:
                print(row)

    def check_redshift_encryption(self, show_progress=True) -> None:
        """Checks rds encryption for all assumable roles"""

        assumed_role = self.assume_role

        # awsres = assumed_role.session.resource('rds')
        client = assumed_role.session.client('redshift')

        try:
            resources = client.describe_clusters(
                MaxRecords=100
            )
        except botocore.exceptions.ClientError as error: # type: ignore
            error_code = error.response['Error']['Code']
            if error_code == 'InvalidClientTokenId':
                self.log_action(
                    {
                        'action': 'describe_clusters',
                        'resource_type': 'redshift',
                        'identifier': 'redshift',
                        'error': error_code,
                        'account_id': self.account_id,
                        'region': self.region,
                    },
                    log_type="warnings"
                )
                return
            else:
                row = {
                    'encryption': error_code,
                    'account_id': assumed_role.account_id,
                    'account_alias': assumed_role.account_alias,
                    'cluster_identifier': 'describe_clusters',
                    'region': self.region,
                }

                self.redshift_encryption.append(row)

                if show_progress:
                    print(row)
                return

        if resources.get('Marker'):
            input('This account has many clusters!')

        for resource in resources['Clusters']:
            try:
                encryption = resource.get('Encrypted')
            except botocore.exceptions.ClientError as error: # type: ignore
                encryption = error.response['Error']['Code']

            identifier = resource.get('ClusterIdentifier')

            row = {
                'encryption': encryption,
                'account_id': assumed_role.account_id,
                'account_alias': assumed_role.account_alias,
                'cluster_identifier': identifier,
                'region': self.region,
            }

            self.redshift_encryption.append(row)

            if show_progress:
                print(row)

    def generate_s3_encryption_report(self, overwrite=False):
        """Create csv file with s3_encryption_report """

        report_fname = f'csv/{self.account_alias}-{self.account_id}-{self.region}-s3-encryption-report.csv'
        if os.path.isfile(report_fname) and not overwrite:
            print('**********************')
            print()
            print(f'{report_fname=} already exists and {overwrite=}')
            print()
            print('**********************')
            return
        # self.check_s3_encryption()
        self.check_s3_encryption()

        if self.buckets_encryption:
            df = pd.DataFrame(self.buckets_encryption)
            df.sort_values(by="encryption", inplace=True)
            df.to_csv(report_fname, index=False)

    def generate_rds_encryption_report(self, overwrite=False):
        """Create csv file with rds_encryption_report """

        report_fname = f'csv/{self.account_alias}-{self.account_id}-{self.region}-rds-encryption-report.csv'
        if os.path.isfile(report_fname) and not overwrite:
            print('**********************')
            print()
            print(f'{report_fname=} already exists and {overwrite=}')
            print()
            print('**********************')
            return

        self.check_rds_encryption()

        if self.rds_encryption:
            df = pd.DataFrame(self.rds_encryption)
            df.sort_values(by="encryption", inplace=True)
            df.to_csv(report_fname, index=False)

    def generate_redshift_encryption_report(self, overwrite=False):
        """Create csv file with redshift_encryption_report """

        report_fname = f'csv/{self.account_alias}-{self.account_id}-{self.region}-redshift-encryption-report.csv'
        if os.path.isfile(report_fname) and not overwrite:
            print('**********************')
            print()
            print(f'{report_fname=} already exists and {overwrite=}')
            print()
            print('**********************')
            return

        self.check_redshift_encryption()

        if self.redshift_encryption:
            df = pd.DataFrame(self.redshift_encryption)
            df.sort_values(by="encryption", inplace=True)
            df.to_csv(report_fname, index=False)


def main():

    # rerun accounts
    # ann02-nonprod-ads, 732327056170

    overwrite = False
    only_accounts = []
    skip_accounts = []

    # only_accounts = ["661095214357", "732327056170", ]
    # skip_accounts = ["732327056170", "661095214357", ]

    for i, role in enumerate(assumable_roles):
        if only_accounts and not role.account_id in only_accounts:
            continue

        if role.account_id in skip_accounts:
            continue

        # accounts_attestation = AccountAttestation(
        #     assume_role=role,
        #     encrypt_buckets=True
        # )
        # accounts_attestation.generate_s3_encryption_report(overwrite=overwrite)

        for region in scan_regions:
            accounts_attestation = AccountAttestation(
                assume_role=role,
                region=region,
                encrypt_buckets=True,
                ignore_exceptions=['IllegalLocationConstraintException']
            )
            accounts_attestation.generate_rds_encryption_report(
                overwrite=overwrite)
            accounts_attestation.generate_redshift_encryption_report(
                overwrite=overwrite)
            accounts_attestation.generate_s3_encryption_report(
                overwrite=overwrite)


def printj(jsonstr: Union[str, object]) -> None:
    """ prints indented json string """

    print(json.dumps(jsonstr, indent=4, default=str))


if __name__ == '__main__':
    print(f'\n\n\nrunning {sys.argv[0]} ??\n\n')
    # main()
