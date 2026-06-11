#!/usr/bin/env python3

"""Script to export resources from AWS"""

import argparse
import sys
import boto3
import time
import boto3
from botocore.exceptions import ProfileNotFound
from botocore.exceptions import ClientError
import datetime
import threading
from pprint import pprint

import re
import sys
import os
sys.path.append(os.path.dirname(__file__) + '/../lib/')
import helper_functions as hf

os.chdir(os.path.dirname(__file__))


class AmazonHelper:
    boto3_session = None
    region_name = ""

    # def __init__(self, **kwargs):
    #     self.boto3_session = boto3.session.Session(**kwargs)

    def session(self, **kwargs):
        self.boto3_session = boto3.session.Session(**kwargs)
        return self.boto3_session

    def get_rows_full_tags(self, resources_tags):
        # get list of all tags
        all_tags = []
        for b in resources_tags:
            all_tags += [t for t in b["tags"]]
        unique_ordered_tags = list(set(all_tags))
        unique_ordered_tags.sort()

        header = [['Type', 'Region', 'Name'] +
                  ['Tag: ' + t for t in unique_ordered_tags]]

        print("header:")
        print(header)
        print("uot")
        print(unique_ordered_tags)

        rows = []
        for b in resources_tags:
            row = [
                b["type"],
                b["region"],
                b['name']
            ]

            for t in unique_ordered_tags:
                if t in b["tags"]:
                    row += [b["tags"][t]]
                else:
                    row += [""]

            rows.append(row)

        return header, rows

    def get_s3_bucket_info(self):
        """Return a formatted list with a header of the buckets in the account"""

        # boto3_session = boto3.session.Session()
        s3_res = self.boto3_session.resource('s3')
        s3 = self.boto3_session.client('s3')

        rows = []
        resources_tags = []
        # headers of file
        header = [['Type', 'Region', 'Name', 'Tag: Environment', 'Tag: Application', 'Tag: Agency', 'Tag: Client',
                   'Tag: Project', 'Creation Date', 'size', 'Creation Date']]
        # Call S3 to list current buckets
        buckets = s3_res.buckets.all()
        i = 0
        hf.debug('\nS3 - Counting buckets...: ', end='')

        for bucket in list(buckets):
            i += 1
            hf.debug(str(i), end=" ", flush=True)
            # b = s3_res.Bucket(bucket.name)
            name = bucket.name
            creation_date = bucket.creation_date
            environment = ""
            application = ""
            agency = ""
            client = ""
            project = ""
            size = self.get_bucket_size(name)
            self.region_name = "-"
            restype = "s3"
            # print(bucket)

            # print(name)

            # look for Project tag
            try:
                tagging = s3.get_bucket_tagging(Bucket=name)
            except ClientError:
                tagging = []

            if 'TagSet' in tagging:
                tags = tagging['TagSet']
            else:
                tags = []

            for tag in tags:
                if tag['Key'] == 'Environment':
                    environment = tag['Value']
                if tag['Key'] == 'Application':
                    application = tag['Value']
                if tag['Key'] == 'Agency':
                    agency = tag['Value']
                if tag['Key'] == 'Client':
                    client = tag['Value']
                if tag['Key'] == 'Project':
                    project = tag['Value']

            resources_tags.append({
                'name': name,
                'tags': {t["Key"]: t["Value"] for t in tags},
                'type': restype,
                'region': self.region_name,
            })

            rows.append([
                restype,
                '-',
                name,
                environment,
                application,
                agency,
                client,
                project,
                str(bucket.creation_date),
                size,
                creation_date
            ])

            # if i > 10:
            #     break

        if args.all_tags:
            header, rows = self.get_rows_full_tags(resources_tags)

        return header, rows

    def get_bucket_size(self, bucket_name):
        """
        returns formatted string with size in bytes

        modified from: https://www.slsmk.com/getting-the-size-of-an-s3-bucket-using-boto3-for-aws/
        """

        cw = self.boto3_session.client('cloudwatch')

        now = datetime.datetime.now()

        # For each bucket item, look up the corresponding metrics from CloudWatch
        response = cw.get_metric_statistics(
            Namespace='AWS/S3',
            MetricName='BucketSizeBytes',
            Dimensions=[
                {'Name': 'BucketName', 'Value': bucket_name},
                {'Name': 'StorageType', 'Value': 'StandardStorage'}
            ],
            Statistics=['Average'],
            Period=3600,
            StartTime=(now - datetime.timedelta(days=1)).isoformat(),
            EndTime=now.isoformat()
        )

        for item in response["Datapoints"]:
            return str("{:,}".format(int(item["Average"])))

    def get_ec2_info(self):
        header = [['Type', 'Region', 'Name', 'Tag: Environment', 'Tag: Application', 'Tag: Layer', 'Tag: Agency',
                   'Tag: Client', 'Tag: Project']]
        rows = []
        resources_tags = []
        ec2 = self.boto3_session.client('ec2')
        ec2s = ec2.describe_instances()

        i = 0
        hf.debug('\nEC2 - Counting EC2s...: ', end='')
        for reservation in ec2s['Reservations']:
            i += 1
            hf.debug(str(i), end=" ", flush=True)
            for row in reservation['Instances']:
                # pprint(row)
                # sys.exit()
                # print(row)
                name = ""
                environment = ""
                application = ""
                agency = ""
                client = ""
                project = ""
                layer = ""
                restype = "ec2"

                if 'Tags' not in row:
                    continue

                for tag in row['Tags']:
                    if tag['Key'] == 'Name':
                        name = tag['Value']
                    if tag['Key'] == 'Environment':
                        environment = tag['Value']
                    if tag['Key'] == 'Application':
                        application = tag['Value']
                    if tag['Key'] == 'Agency':
                        agency = tag['Value']
                    if tag['Key'] == 'Client':
                        client = tag['Value']
                    if tag['Key'] == 'Project':
                        project = tag['Value']
                    if tag['Key'] == 'Layer':
                        layer = tag['Value']

                resources_tags.append({
                    'name': name,
                    'tags': {t["Key"]: t["Value"] for t in row['Tags']},
                    'type': restype,
                    'region': self.region_name,
                })

                rows.append([
                    restype,
                    self.region_name,
                    name,
                    environment,
                    application,
                    layer,
                    agency,
                    client,
                    project
                ])

                # if i > 10:
                #     break

        if args.all_tags:
            header, rows = self.get_rows_full_tags(resources_tags)

        return header, rows

    def get_elb_info(self):
        rows = []
        resources_tags = []
        header = [['Type', 'Region', 'Name', 'Tag: Environment', 'Tag: Application', 'Tag: Agency', 'Tag: Client',
                   'Tag: Project']]
        elb = self.boto3_session.client('elb')
        elbs = elb.describe_load_balancers()
        i = 0
        hf.debug('\nELB - Counting ELBs...: ', end='')
        for loadbal in elbs['LoadBalancerDescriptions']:
            i += 1
            hf.debug(str(i), end=" ", flush=True)
            # print(row)
            name = loadbal['LoadBalancerName']
            environment = ""
            application = ""
            agency = ""
            client = ""
            project = ""
            restype = "elb"

            tags = elb.describe_tags(LoadBalancerNames=[name])[
                'TagDescriptions'][0]['Tags']
            for tag in tags:
                if tag['Key'] == 'Environment':
                    environment = tag['Value']
                if tag['Key'] == 'Application':
                    application = tag['Value']
                if tag['Key'] == 'Agency':
                    agency = tag['Value']
                if tag['Key'] == 'Client':
                    client = tag['Value']
                if tag['Key'] == 'Project':
                    project = tag['Value']

            resources_tags.append({
                'name': name,
                'tags': {t["Key"]: t["Value"] for t in tags},
                'type': restype,
                'region': self.region_name,
            })

            rows.append([
                restype,
                self.region_name,
                name,
                environment,
                application,
                agency,
                client,
                project
            ])

        if args.all_tags:
            header, rows = self.get_rows_full_tags(resources_tags)

        return header, rows

    def get_resource(self, name, **kwargs):
        return self.boto3_session.resource(name, **kwargs)

    def get_client(self, name, **kwargs):
        return self.boto3_session.client(name, **kwargs)

    def get_rds_instances(self):
        rds = self.get_client('rds')
        return rds.describe_db_instances()

    def get_rds_tags(self, **kwargs):
        rds = self.get_client('rds')
        return rds.list_tags_for_resource(**kwargs)

    def get_rds_info(self):
        rows = []
        resources_tags = []
        header = [['Type', 'Region', 'Name', 'Instance_class', 'Tag: Environment', 'Tag: Application', 'Tag: Agency',
                   'Tag: Client', 'Tag: Project']]

        rds_instances = self.get_rds_instances()
        i = 0
        hf.debug('\nRDS - Counting instances...: ', end='')
        for dbi in rds_instances['DBInstances']:
            i += 1
            hf.debug(str(i), end=" ", flush=True)
            # print(row)
            name = dbi['DBInstanceIdentifier']
            db_arn = dbi['DBInstanceArn']
            instance_class = dbi['DBInstanceClass']
            environment = ""
            application = ""
            agency = ""
            client = ""
            project = ""
            restype = "rds"

            tags = self.get_rds_tags(ResourceName=db_arn)['TagList']
            for tag in tags:
                if tag['Key'] == 'Environment':
                    environment = tag['Value']
                if tag['Key'] == 'Application':
                    application = tag['Value']
                if tag['Key'] == 'Agency':
                    agency = tag['Value']
                if tag['Key'] == 'Client':
                    client = tag['Value']
                if tag['Key'] == 'Project':
                    project = tag['Value']

            resources_tags.append({
                'name': name,
                'tags': {t["Key"]: t["Value"] for t in tags},
                'type': restype,
                'region': self.region_name,
            })

            rows.append([
                restype,
                self.region_name,
                name,
                instance_class,
                environment,
                application,
                agency,
                client,
                project
            ])

        if args.all_tags:
            header, rows = self.get_rows_full_tags(resources_tags)

        return header, rows

    def get_redshift_info(self):
        rows = []
        resources_tags = []
        header = [['Type', 'Region', 'Name', 'Tag: Environment', 'Tag: Application', 'Tag: Agency', 'Tag: Client',
                   'Tag: Project']]
        redshift = self.boto3_session.client('redshift')
        rsclusters = redshift.describe_clusters()
        i = 0
        hf.debug('\nRedshift - Counting clusters...: ', end='')
        for rscluster in rsclusters['Clusters']:
            i += 1
            hf.debug(str(i), end=" ", flush=True)
            # print(row)
            name = rscluster['ClusterIdentifier']
            environment = ""
            application = ""
            agency = ""
            client = ""
            project = ""
            restype = "redshift"

            tags = rscluster['Tags']
            for tag in tags:
                if tag['Key'] == 'Environment':
                    environment = tag['Value']
                if tag['Key'] == 'Application':
                    application = tag['Value']
                if tag['Key'] == 'Agency':
                    agency = tag['Value']
                if tag['Key'] == 'Client':
                    client = tag['Value']
                if tag['Key'] == 'Project':
                    project = tag['Value']

            resources_tags.append({
                'name': name,
                'tags': {t["Key"]: t["Value"] for t in tags},
                'type': restype,
                'region': self.region_name,
            })

            rows.append([
                restype,
                self.region_name,
                name,
                environment,
                application,
                agency,
                client,
                project
            ])

        if args.all_tags:
            header, rows = self.get_rows_full_tags(resources_tags)

        return header, rows

parser = argparse.ArgumentParser(description='Export resources from AWS')
parser.add_argument("action", choices=['all', 's3', 'ec2', 'elb', 'rds', 'redshift'], nargs='?', default='all',
                    help="Action to perform (defaults to all)")
parser.add_argument("-v", "--verbose", default=0, help="Increase output verbosity", action='count')
parser.add_argument("-p", "--profile", default='', help="AWS profile to use. Defaults to 'default'")
parser.add_argument("-f", "--folder", default='tmp/', help="path to folder to put output files. MUST end with `/`")
parser.add_argument("-i", "--interactive", default='', help="Presents a prompt before executing copying commands to"
                                                            "source files", action='store_true')
parser.add_argument("-A", "--all-tags", action="store_true", help="Export all tags for the resources")
parser.add_argument("-r", "--region",
                    help="Filter to this region name")

args = parser.parse_args()

if args.all_tags and args.region == None:
    sys.exit('Error: all-tags requires to specify a region')

# needed as list
args.region = [args.region]

output_path = args.folder
if output_path[-1:] != '/':
    sys.exit('Output path {} has to end with `/`'.format(output_path))

# initializing variables to be filled
header_ec2 = []
header_elb = []
header_rds = []
header_redshift = []
lines_ec2 = []
lines_elb = []
lines_rds = []
lines_redshift = []

hf.verbose = 1

AmazonHelper = AmazonHelper()

# profile_name = args.profile
boto3_session = AmazonHelper.session()

if args.action == 's3' or args.action == 'all':
    # get buckets as list
    header_s3, lines_s3 = AmazonHelper.get_s3_bucket_info()

# get regions
ec2 = boto3_session.client('ec2')
regions = ec2.describe_regions()['Regions']
for region in regions:
    region_name = region['RegionName']
    if args.region == "":
        args.region = ['us-east-1', 'us-west-1']
    if region_name not in args.region:
        print(' {}: skipping...'.format(region_name))
        continue
    hf.debug("\n" + region_name, end=" ")
    AmazonHelper.session(region_name=region_name)
    AmazonHelper.region_name = region_name

    if args.action == 'ec2' or args.action == 'all':
        # get EC2's as list
        header_ec2, newlines = AmazonHelper.get_ec2_info()
        lines_ec2 += newlines

    if args.action == 'elb' or args.action == 'all':
        header_elb, newlines = AmazonHelper.get_elb_info()
        lines_elb += newlines

    if args.action == 'rds' or args.action == 'all':
        header_rds, newlines = AmazonHelper.get_rds_info()
        lines_rds += newlines

    if args.action == 'redshift' or args.action == 'all':
        header_redshift, newlines = AmazonHelper.get_redshift_info()
        lines_redshift += newlines


if args.action == 's3' or args.action == 'all':
    # write csv
    path = output_path + 'resources-S3.csv'
    hf.write_csv(path, header_s3 + lines_s3)


if args.action == 'ec2' or args.action == 'all':
    lines_ec2 = header_ec2 + lines_ec2
    path = output_path + 'resources-EC2.csv'
    hf.write_csv(path, lines_ec2)

if args.action == 'elb' or args.action == 'all':
    lines_elb = header_elb + lines_elb
    path = output_path + 'resources-ELB.csv'
    hf.write_csv(path, lines_elb)

if args.action == 'rds' or args.action == 'all':
    lines_rds = header_rds + lines_rds
    path = output_path + 'resources-RDS.csv'
    hf.write_csv(path, lines_rds)

if args.action == 'redshift' or args.action == 'all':
    lines_redshift = header_redshift + lines_redshift
    path = output_path + 'resources-Redshift.csv'
    hf.write_csv(path, lines_redshift)
