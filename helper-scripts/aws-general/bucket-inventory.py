""" As per ASUP-15610, sets up bucket inventory reports for buckets

    DSDK Archive (Data-DSDK)
    Annalect-neustar-dsdk
    Annalect-tech-audiencebuilder
    Annalect-jumpshot-agileid
    Annalect-tech-aipprod

"""

##
# WARNING: this is working for all buckets
##


# import argparse
import sys

# import pandas as pd
import boto3
#import json
from pprint import pprint
#import re
import botocore


# #20-04-20
# old_bucket_tags = [
#     "dsdk-archive",
#     "annalect-annalect-audiencebuilder",
#     "annalect-annalect-neustarv2",
#     "annalect-lotame-datafeeds",
#     "annalect-annalect-placeiq",
#     "annalect-acxiom-agileid",
#     "annalect-blis-agileid",
#     "annalect-tapad-agileid",
#     "omd-daimler-performancereporting",
#     "annalect-piq-dataplatform",
# ]

# bucket_tags = [
#     # bucket TAGS
#     "data-dsdk",
#     "annalect-annalect-neustarv2",
#     "annalect-tech-audiencebuilder",
#     "annalect-neustar-dsdk",
#     "annalect-tech-aipprod",
#     "annalect-lotame-datafeeds",
#     "omg-multiple-multiple",
#     "annalect-tech-ops",
#     "annalect-annalect-placeiq",
#     "annalect-intelcorp-adobe",
#     "annalect-labs-youtube",
#     "annalect-acxiom-agileid",
#     "heartsscience-att-liveramp",
#     "annalect-blis-agileid",
#     "annalect-tapad-agileid",
#     "omd-daimler-performancereporting",
#     "annalect-piq-dataplatform",

#     # bucket names
#     "Automationscripts",
#     "BMC_Automation_Scripts",
#     "ETLEvac",
#     "Oracle_MYSQL_Backup",
#     "Shared-SQL-Dev-Backup",
#     "Shared-SQL-QA-Backup",
#     "Technical_Infrastructure",
#     "adeprod",
#     "adt-automation",
#     "annalect-acxiom-agileid",
#     "annalect-adt-api",
#     "annalect-adt",
#     "annalect-alienvault-cloudtrail",
#     "annalect-annalect-audiencebuilder",
#     "annalect-annalect-audiencebuilder1",
#     "annalect-annalect-audiencebuilder2",
#     "annalect-annalect-audiencebuilder3",
#     "annalect-annalect-neustarv2",
#     "annalect-annalect-placeiq",
#     "annalect-annalect-youtubemp4",
#     "annalect-audit-logs",
#     "annalect-backups",
#     "annalect-billing",
#     "annalect-blis-agileid",
#     "annalect-cloud-vault",
#     "annalect-cloudfront-logs",
#     "annalect-datapipeline-logs",
#     "annalect-deployment-artifacts",
#     "annalect-deployment",
#     "annalect-emr-logs",
#     "annalect-explorer-test",
#     "annalect-exploreus-pipeline",
#     "annalect-exploreus",
#     "annalect-global-components",
#     "annalect-intelcorp",
#     "annalect-loadbalancer-logs",
#     "annalect-loggly-backup",
#     "annalect-lotame-datafeeds",
#     "annalect-piq-dataplatform",
#     "annalect-prod-elb-access-logs",
#     "annalect-redshift-audit-logs",
#     "annalect-tapad-agileid",
#     "annalect-us-east-1-lambda-deployments",
#     "annalect-us-east-1-loadbalancer-logs",
#     "annalect.bootstrap-bucket",
#     "annalect_data_migraton",
#     "annalectcloudmail-att",
#     "annalectcloudmail-dbm",
#     "annalectcloudmail-ttd",
#     "annalectcloudmail",
#     "annalectcloudtrail",
#     "annalectftp.annalect.com",
#     "annalectus-s3appbucket-1ay4ycmfpd02e",
#     "assets.annalect.com",
#     "athena-query-results-661095214357-us-east-1",
#     "aws-athena-query-results-661095214357-us-east-1",
#     "aws-glue-notebooks-661095214357-us-east-1",
#     "aws-glue-scripts-661095214357-us-east-1",
#     "aws-glue-temporary-661095214357-us-east-1",
#     "aws-logs-661095214357-us-east-1",
#     "basic-pipeline-artifactstorebucket-gfpbues2inix",
#     "cdn.annalect.com",
#     "cf-templates-45754a42j3vi-us-east-1",
#     "codepipeline-us-east-1-465731214603",
#     "cw-syn-results-661095214357-us-east-1",
#     "dsdk-archive",
#     "elasticbeanstalk-us-east-1-661095214357",
#     "elb-logs-identity",
#     "hearts-att-liveramp",
#     "images-annalect",
#     "neustar-annalect",
#     "omd-daimler-performancereporting",
#     "omg-agencies",
#     "rds-auotomated-backup-s3sourcelistbucket-1ettriuijrmu4",
#     "rds-auotomated-backup-s3sourcelistbucket-1u3esxt42p4qi",
#     "serverless-image-handler-demobucket-iinv1jz0hks9",
#     "storagemadeeasy-poc",
# ]

# def get_args():
#     parser = argparse.ArgumentParser(description='Description')

#     parser.add_argument("-n", "--name", default=None,
#                     help="Name of ...")

#     parser.add_argument("-d", "--debug_options", action='store_true',
#                     help="Debug options passed and exit")

#     args = parser.parse_args()

#     if not any(vars(args).values()):
#         parser.parse_args(['--help'])
#         # parser.error('No arguments provided.')

#     if args.debug_options:
#         print(args)
#         sys.exit()

#     return args

def get_buckets():
    """ gets buckets with tags """

    client = boto3.client('s3')
    buckets = client.list_buckets()['Buckets']
    for _bucket in buckets:
        bucket = _bucket['Name']
        yield bucket
        # # print(f'Looking tags of bucket "{bucket}"')
        # try:
        #     response = client.get_bucket_tagging(
        #         Bucket=bucket
        #     )
        # except botocore.exceptions.ClientError as error:
        #     # print(error)
        #     continue
        # tag_list = response.get('TagSet')
        # if not tag_list:
        #     continue

        # for tag in tag_list:
        #     if tag["Value"] in bucket_tags:
        #         yield bucket
        #         break



def set_bucket_inventory():
    """ sets bucket inventory """
    client = boto3.client('s3')

    for bucket in get_buckets():
        try:
            configurations = client.list_bucket_inventory_configurations(
                Bucket=bucket
            )
        except Exception as e:
            if "AccessDenied" in e.args[0]:
                print(f'{bucket}: Access Denied. Continuing.')
            continue

        conf_list = configurations.get('InventoryConfigurationList')

        if type(conf_list) is list and len(conf_list) != 1:
            print(f'Configuration list is not a list or has more than one configuration. Please review "{bucket}"')
            continue

        conf_id = 'inventory'
        # if type(conf_list) is list and len(conf_list) == 1:
        #     # ans = input(f'"{bucket}" already has one inventory configuration. Delete? [y/N]:')
        #     # if ans != 'y':
        #     #     print('Not doing any configuration for this bucket "{bucket}". Continuing with next.')
        #     #     continue

        #     # conf_id = conf_list[0]['Id']
        #     response = client.delete_bucket_inventory_configuration(
        #         Bucket=bucket,
        #         Id=conf_id
        #     )

        print(f'Configuring inventory for bucket "{bucket}"... ', end='')
        response = client.put_bucket_inventory_configuration(
            Bucket=f"{bucket}",
            Id=conf_id,
            InventoryConfiguration={
                'Destination': {
                    'S3BucketDestination': {
                        'Bucket': 'arn:aws:s3:::ann01-tioprod-s3bucket-inventory',
                        'Format': 'Parquet',
                        'Prefix': 's3_inventories',
                        'Encryption': {
                            'SSES3': {}
                        }
                    }
                },
                'IsEnabled': True,
                'Id': conf_id,
                'IncludedObjectVersions': 'All',
                'OptionalFields': [
                    'LastModifiedDate',
                    'Size',
                    'StorageClass',
                    'ETag',
                    'IsMultipartUploaded',
                    'ReplicationStatus',
                    'EncryptionStatus',
                    'IntelligentTieringAccessTier'
                ],
                'Schedule': {
                    'Frequency': 'Daily'
                }
            }
        )



        # pprint(response)
        print(f" OK!")

def set_bucket_analytics():
    """ sets bucket analytics """
    client = boto3.client('s3')

    for bucket in get_buckets():
        conf_id = 'analytics'

        try:
            configurations = client.list_bucket_analytics_configurations(
                Bucket=bucket
            )
        except Exception as e:
            if "AccessDenied" in e.args[0]:
                print(f'{bucket}: Access Denied. Continuing.')
            continue
        conf_list = configurations.get('AnalyticsConfigurationList')
        if type(conf_list) is list and len(conf_list) > 0:
            # print(f'Configuration list is not a list or has more than one configuration. Please review "{bucket}"')
            conf_id = conf_list[0]['Id']

        print(f'Configuring analytics_configuration for bucket "{bucket}"... ', end='')
        response = client.put_bucket_analytics_configuration(
            Bucket=bucket,
            Id=conf_id,
            AnalyticsConfiguration={
                "Id": conf_id,
                'StorageClassAnalysis': {
                    'DataExport': {
                        'OutputSchemaVersion': 'V_1',
                        'Destination': {
                            'S3BucketDestination': {
                                'Format': 'CSV',
                                'BucketAccountId': '661095214357',
                                'Bucket': 'arn:aws:s3:::ann01-tioprod-s3bucket-analytics',
                                'Prefix': f's3_analytics/bucket={bucket}'
                            }
                        }
                    }
                }
            }
        )
        print('OK!')

def create_bucket_policy_statement():
     buckets = get_buckets()
     for bucket in buckets:
         print(f'"arn:aws:s3:::{bucket}",', end="")

if __name__ == "__main__":
    # args = get_args()

    ## uncomment to set up bucket inventory
    # set_bucket_inventory()

    ## uncomment to list buckets for policy statement
    # create_bucket_policy_statement()

    ## uncomment to configure analytics
    set_bucket_analytics()