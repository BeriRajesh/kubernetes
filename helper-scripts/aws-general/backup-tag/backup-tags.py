import boto3
import pandas as pd

# Function to list EBS volumes and filter based on tags
def list_ebs_volumes(client, backup_tag_key, backup_tag_value, patchup_tag_key):
    volumes = client.describe_volumes()['Volumes']
    filtered_volumes = []
    for volume in volumes:
        tags = {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
        if patchup_tag_key in tags and backup_tag_key not in tags:
            volume_id = volume['VolumeId']
            volume_name = tags.get('Name', 'N/A')
            filtered_volumes.append((volume_id, volume_name))
    return filtered_volumes

# Function to list EFS file systems and filter based on tag
def list_efs_filesystems(client, tag_key, tag_value):
    filesystems = client.describe_file_systems()['FileSystems']
    filtered_filesystems = [(fs['FileSystemId']) for fs in filesystems if not any(tag['Key'] == tag_key and tag['Value'] == tag_value for tag in fs.get('Tags', []))]
    return filtered_filesystems

# Function to list FSX file systems and filter based on tag
def list_fsx_filesystems(client, tag_key, tag_value):
    filesystems = client.describe_file_systems()['FileSystems']
    filtered_filesystems = []
    for fs in filesystems:
        tags = {tag['Key']: tag['Value'] for tag in fs.get('Tags', [])}
        if tag_key not in tags or tags[tag_key] != tag_value:
            fs_id = fs['FileSystemId']
            fs_name = tags.get('Name', 'N/A')
            filtered_filesystems.append((fs_id, fs_name))
    return filtered_filesystems

# Function to list RDS instances and filter based on tag
def list_rds_instances(client, tag_key, tag_value):
    instances = client.describe_db_instances()['DBInstances']
    filtered_instances = [(instance['DBInstanceIdentifier']) for instance in instances if not any(tag['Key'] == tag_key and tag['Value'] == tag_value for tag in instance.get('TagList', []))]
    return filtered_instances

# Function to list DynamoDB tables and filter based on tag
def list_dynamodb_tables(client, tag_key, tag_value, exclude_table):
    tables = client.list_tables()['TableNames']
    filtered_tables = []

    for table in tables:
        if table == exclude_table:
            continue
        
        # Get the table ARN
        table_arn = client.describe_table(TableName=table)['Table']['TableArn']

        # List the tags of the table
        tags = client.list_tags_of_resource(ResourceArn=table_arn).get('Tags', [])

        # Check if the table has the specified tag
        if not any(tag['Key'] == tag_key and tag['Value'] == tag_value for tag in tags):
            filtered_tables.append(table)
    
    return filtered_tables

# Main function
def main():
    resource_types = ['ebs', 'efs', 'fsx', 'rds', 'dynamodb']
    backup_tag_key = 'backup'
    backup_tag_value = 'true'
    patchup_tag_key = 'Patch Group'  # Assuming this is the tag key for patch group
    output_file = 'backup_false_resource.xlsx'
    exclude_table = 'terraform-lock'

    profile_name = select_aws_profile()

    session = boto3.Session(profile_name=profile_name)
    excel_data = {}

    for resource_type in resource_types:
        client = session.client('ec2') if resource_type == 'ebs' else session.client(resource_type)
        resources = []
        if resource_type == 'ebs':
            resources = list_ebs_volumes(client, backup_tag_key, backup_tag_value, patchup_tag_key)
        elif resource_type == 'efs':
            resources = list_efs_filesystems(client, backup_tag_key, backup_tag_value)
        elif resource_type == 'fsx':
            resources = list_fsx_filesystems(client, backup_tag_key, backup_tag_value)
        elif resource_type == 'rds':
            resources = list_rds_instances(client, backup_tag_key, backup_tag_value)
        elif resource_type == 'dynamodb':
            resources = list_dynamodb_tables(client, backup_tag_key, backup_tag_value, exclude_table)

        print(f"Number of {resource_type} resources without backup tag: {len(resources)}")  # Debugging message
        excel_data[resource_type] = resources

    output_file = f"{profile_name}_{output_file}"
    export_to_excel(excel_data, output_file)
    print("Filtered resources exported to", output_file)

# Prompt user to select AWS profile
def select_aws_profile():
    print("Select AWS profile:")
    profile = input()
    return profile

# Export results to Excel
def export_to_excel(data, output_file):
    with pd.ExcelWriter(output_file) as writer:
        for resource_type, resources in data.items():
            if resource_type == 'ebs':
                df = pd.DataFrame(resources, columns=['VolumeID', 'VolumeName'])
            elif resource_type == 'fsx':
                df = pd.DataFrame(resources, columns=['FileSystemID', 'FileSystemName'])
            elif resource_type == 'rds':
                df = pd.DataFrame(resources, columns=['DBInstanceIdentifier'])
            elif resource_type == 'dynamodb':
                df = pd.DataFrame(resources, columns=['TableName'])
            else:
                df = pd.DataFrame(resources, columns=[f'{resource_type.upper()}ID'])
            df.to_excel(writer, sheet_name=resource_type, index=False)

if __name__ == "__main__":
    main()
