""" AWS helper functions """

import boto3
from botocore.exceptions import ProfileNotFound
from botocore.exceptions import ClientError
import datetime
import threading
from pprint import pprint

import re
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '../'))
import lib.helper_functions as hf


class ProgressPercentage(object):
    def __init__(self):
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        print(bytes_amount)

class AmazonHelper:
    boto3_session = None
    region_name = ""

    # def __init__(self, **kwargs):
    #     self.boto3_session = boto3.session.Session(**kwargs)

    def session(self, **kwargs):
        self.boto3_session = boto3.session.Session(**kwargs)
        return self.boto3_session

    def get_s3_bucket_info(self):
        """Return a formatted list with a header of the buckets in the account"""

        # boto3_session = boto3.session.Session()
        s3_res = self.boto3_session.resource('s3')
        s3 = self.boto3_session.client('s3')

        rows = []
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

            rows.append([
                's3',
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

            # if i>3: break;

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

                rows.append([
                    'ec2',
                    self.region_name,
                    name,
                    environment,
                    application,
                    layer,
                    agency,
                    client,
                    project
                ])

        return header, rows

    def get_elb_info(self):
        rows = []
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
            for tag in elb.describe_tags(LoadBalancerNames=[name])['TagDescriptions'][0]['Tags']:
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

            rows.append([
                'elb',
                self.region_name,
                name,
                environment,
                application,
                agency,
                client,
                project
            ])

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
            for tag in self.get_rds_tags(ResourceName=db_arn)['TagList']:
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

            rows.append([
                'rds',
                self.region_name,
                name,
                instance_class,
                environment,
                application,
                agency,
                client,
                project
            ])

        return header, rows

    def get_redshift_info(self):
        rows = []
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
            for tag in rscluster['Tags']:
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

            rows.append([
                'redshift',
                self.region_name,
                name,
                environment,
                application,
                agency,
                client,
                project
            ])

        return header, rows

    def update_tags_rds(self):
        """update tags on RDS instances based on name of resource"""

        rds_instances = self.get_rds_instances()
        hf.debug('Processing instances...', end="")
        for dbi in rds_instances['DBInstances']:
            hf.debug('. ', end="")
            name = dbi['DBInstanceIdentifier']
            db_arn = dbi['DBInstanceArn']
            tags = self.get_rds_tags(ResourceName=db_arn)['TagList']
            for tag in tags:
                if tag['Key'] == 'Environment':
                    for environment in ['Dev', 'QA', 'Prod', 'MGMT']:
                        if re.search(environment, name, re.IGNORECASE):
                            if tag['Value'] == environment:
                                # print(tag)
                                break
                    else:
                        hf.debug('\nInstance name `{}` does not imply any known environment, but ENVIRONMENT={}'.format(name, tag['Value']))
                        break
                    break
            else:
                # if instance doesn't have an Environment tag then try to tag it according to it's name
                for environment in ['Dev', 'QA', 'Prod', 'MGMT']:
                    if re.search(environment, name, re.IGNORECASE):
                        response = self.get_client('rds').add_tags_to_resource(
                            ResourceName=db_arn,
                            Tags=[{
                                'Key': 'Environment',
                                'Value': environment
                            }]
                        )
                        hf.debug(response)
                        print('tagged `{}` with Environment:{}'.format(name, environment))
                else:
                    print("Instance's name `{}` doesn't suggest any Environment".format(name))

    def retag(self, path):
        if not os.path.exists(path):
            sys.exit('ERROR: File `{}` could be found'.format(path))

        resources_rows = hf.read_csv(path)
        header = []
        lineno = 0
        for resource_row in resources_rows:
            lineno += 1
            if not header:
                header = resource_row
                tags_names = self.retag_get_tags_from_header(header)
                continue

            resource_type, region, name, tags_values = self.retag_tokenize_row(resource_row)

            recognized_types = ['s3', 'ec2', 'elb', 'rds', 'redshift']
            if resource_type not in recognized_types:
                sys.exit('ERROR (line #{}): resource type `{}` not one of recognized types `{}`'
                         .format(lineno, resource_type, recognized_types))

            if resource_type == 's3':
                self.tag_s3(name, dict(zip(tags_names, tags_values)))
            elif resource_type == 'ec2':
                self.tag_ec2(name, region, dict(zip(tags_names, tags_values)))
            else:
                raise exception('Unrecognized type')

    def retag_get_tags_from_header(self, header):

        a = self.boto3_session
        if not (re.match('type', header[0], re.IGNORECASE) and
                re.match('region', header[1], re.IGNORECASE) and
                re.match('name', header[2], re.IGNORECASE)):
            sys.exit('ERROR: first three columns should have a header type,region,name')

        tags_names = []
        for i in range(3,len(header)):
            if not re.match("Tag:[ ]?[^ ]+$", header[i], re.IGNORECASE):
                sys.exit('ERROR: Invalid tagged columns detected {}. Tag Columns should have the format "Tag: tag_name"'
                         .format(header[3:]))

            tag = re.match("Tag:[ ]?([^ ]+)$", header[i], re.IGNORECASE)
            tags_names.append(tag[1])

        if len(tags_names) != len(header)-3:
            sys.exit('ERROR: wrong number of Tag Columns. Got header: `{}`'.format(header))

        return tags_names

    def retag_tokenize_row(self, line):
        """ """
        return line[0], line[1], line[2], line[3:]

    def tag_s3(self, bucket_name, tags):
        """tags a bucket_name with tags.

        Args:
            bucket_name (str): Name of the bucket to tag
            tags (list(dict)): List of dictionaries of tags in the format [{'Key': 'KeyName', 'Value': 'value_for_key'}]

        Returns:
            object response from AWS API

        """
        if type(tags) is not list:
            tags = [tags]

        for tag in tags:
            if type(tag) is not dict:
                raise Exception('`{}` is not a dictionary'.format(tag))
            key, value = tuple(tag.items())[0]

            if value == "":
                print('Refusing to tag with empty value')
                continue

            hf.debug('Tagging `{}` with tags `{}`'.format(bucket_name, tags))
            bucket_tagging = self.get_resource('s3').BucketTagging(bucket_name)
            response = bucket_tagging.put(Tagging={
                'TagSet': [{
                    'Key': key,
                    'Value': value
                }]
            })

    def tag_ec2(self, name, region_name, tags):
        """tags an ec2 instance.

        Args:
            name (str): the value of the tag Name of the instance. Has to return only one instance.
            region_name (str): name of region where EC2 is located. If empty defaults to 'us-east-1'
            tags (dict): List of dictionaries of tags in the format [{'Key': 'KeyName', 'Value': 'value_for_key'}]

        Returns:
            object response from AWS API

        """
        if type(tags) is not list:
            tags = [tags]

        # print(name)
        # print(tags)
        ec2 = self.get_client('ec2', region_name=region_name)

        ec2_filter = {
            'Name': 'tag:Name',
            'Values': [name]
        }

        query = ec2.describe_instances(
            Filters=[ec2_filter]
        )

        if len(query['Reservations']) > 1:
            # pprint(query['Reservations'])
            hf.debug('Filter {} returns more than one Reservation'.format(ec2_filter), 0)
            return

        query_instances = query['Reservations'][0]['Instances']

        if len(query_instances) > 1:
            # pprint(query_instance)
            hf.debug('Filter {} returns more than one EC2'.format(ec2_filter), 0)
            return

        query_instance = query_instances[0]

        instance_id = query_instance['InstanceId']

        for tag in tags:
            hf.debug('Tagging `{}` with tags `{}`'.format(name, tags), 0)
            if type(tag) is not dict:
                raise Exception('`{}` is not a dictionary'.format(tag))
            key, value = tuple(tag.items())[0]

            if value == "":
                print('Refusing to tag with empty value')
                continue

            response = ec2.create_tags(
                Resources=[instance_id],
                Tags=[{
                    'Key': key,
                    'Value': value
                }]
            )

    def dashboards_get_list(self):
        cw = self.get_client('cloudwatch')
        dashboards = cw.list_dashboards()

        return dashboards

    def dashboards_get(self, dashboard_name):
        cw = self.get_client('cloudwatch')
        dashboard = cw.get_dashboard(DashboardName=dashboard_name)
        return dashboard

    def dashboard_update(self, dashboard_name, body):
        cw = self.get_client('cloudwatch')

        return cw.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=body
        )

    def s3_get_size(self, bucket, path):
        s3 = self.get_client('s3')
        head = s3.head_object(
            Bucket=bucket,
            Key=path
        )
        return head['ContentLength']

    def s3_get_file(self, bucket, path, destination, callback=None):
        s3 = self.get_client('s3')
        with open(destination, 'wb') as fh:
            s3.download_fileobj(bucket, path, fh, Callback=callback)
