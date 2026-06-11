import argparse
import json
import os
import re
import string
import uuid
from random import choice, randint
from textwrap import dedent

import boto3
from cryptography.hazmat.backends import \
    default_backend as crypto_default_backend
from cryptography.hazmat.primitives import \
    serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa

require_password=False
uuid = uuid.uuid1()
characters = string.ascii_letters + string.digits
user_name=''
s3_bucket=''
s3_path=''
password =  "".join(choice(characters) for x in range(randint(16, 18)))
passphrase =  "".join(choice(characters) for x in range(randint(32, 64)))
user_pub_key=''
role_arn=''
role_name=''
home_directory=''
perm_type = 'readWrite'

# regex to validate bucket names
valid_chars_regex = re.compile(r"[a-zA-Z0-9\-]+")  # regex to validate bucket names
valid_chars_directory_regex = re.compile(r"[a-zA-Z0-9\-/]+")

def get_args():
    parser = argparse.ArgumentParser(description='Description')

    parser.add_argument("-w", "--with-password", default=0,
        help="Whether to use password. Default False.")
    parser.add_argument("-u", "--username",
        help="sFTP username.")
    parser.add_argument("-b", "--bucket",
        help="S3 bucket to receive files via sFTP.")
    parser.add_argument("-p", "--prefix",
        help="S3 prefix for the files.")
    parser.add_argument("-r", "--remove", default=None,
        help="SFTP username to delete.")

    parser.add_argument("-d", "--debug_options", action='store_true',
        help="Debug options passed and exit")

    args = parser.parse_args()

    # if not any(vars(args).values()):
    #     parser.parse_args(['--help'])
    #     # parser.error('No arguments provided.')

    if args.debug_options:
        print(args)
        sys.exit()

    return args

def main():
    global require_password
    print("Welcome to new Sftp Account creation process\n")
    require_password = args.with_password != "0"
    # require_password=yes_or_no('Do you want the New SFTP Account with Username/Password Authentication ')

    if args.remove:
        remove_account()
    elif require_password is True:
        print("\nCreating Account with UserName and Password Authentication")
        common_actions()
        create_secrets()
    elif require_password is False:
        print("\nCreating Account with Public / Private Key Authentication and with Passphrase. Specify option -w to use password.")
        common_actions()
        generate_keys()
        create_secrets()

def remove_account():
    """ Removes account from IAM roles and from Secrets Manager """

    iam = boto3.client('iam')
    secrets = boto3.client('secretsmanager')

    try:
        secret_id = f"SFTP/{args.remove}"
        secrets.delete_secret(
            SecretId=secret_id
        )
        print(f"Secret {secret_id} was removed")
    except Exception as error:
        print(f"Error while removing secret {secret_id}.")
        print(error)

    try:
        roleName = f"sftp-{args.remove}"
        policies = iam.list_role_policies(
            RoleName=roleName
        )

        for policy in policies['PolicyNames']:
            try:
                iam.delete_role_policy(
                    RoleName=roleName,
                    PolicyName=policy
                )
                print(f'Deleted inline policy {policy} from role {roleName}')
            except Exception as error:
                print(f'Error while deleting inline policy {policy} from role {roleName}')
                print(error)

        iam.delete_role(
            RoleName=roleName
        )
        print(f"Role {roleName} was removed")
    except Exception as error:
        print(f"Error while removing role {roleName}.")
        print(error)


def generate_keys():
    global passphrase
    global user_name
    global user_pub_key
    user_public_file="./keys/"+user_name+".pub"
    user_private_file="./keys/"+user_name+".pem"

    # taken from: https://stackoverflow.com/a/39126754
    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=2048
    )
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption())
    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH
    )
    user_pub_key = public_key.decode()
    with open(user_private_file, "wb") as f:
        f.write(private_key)

    with open(user_public_file, "wb") as f:
        f.write(public_key)


def common_actions():
    get_user_inputs()
    policy_name=get_policy_name()
    policy=get_policy_folder_readWrite()
    create_role()
    attach_inline_policy_to_role(role_name, policy_name, policy)
    file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'welcome')
    upload_file_name  = s3_path + '/welcome'
    print(file_name)
    upload_file(file_name, s3_bucket, upload_file_name)


def attach_inline_policy_to_role(role_name, policy_name, policy):
    iam = boto3.client('iam')

    try:
        response = iam.put_role_policy(
            RoleName=role_name,
            PolicyDocument=json.dumps(policy),
            PolicyName=policy_name
        )
        print(f'Successfully Attached the Policy: {policy_name} to Role: {role_name}')
        return(response)
    except Exception as e:
        print(e)

def create_secrets():
    global user_name
    global home_directory
    global password
    global user_pub_key
    global role_arn
    secrets = boto3.client('secretsmanager')

    if require_password is True:
        try:
            secrets.create_secret(
                Name='SFTP/'+user_name,
                Description='Sftp Access to '+ user_name,
                SecretString=json.dumps({
                    "Password": password,
                    "Role": role_arn,
                    "home_directory": home_directory
                }),
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'annalect-tech-' + user_name
                    },
                    {
                        'Key': 'purpose',
                        'Value': 'sftp'
                    },
                ]
            )

            msg = dedent(f"""\
                    Username: {user_name}
                    Password: {password}

                    You can connect to Sftp using the following command :

                        sftp {user_name}@sftp.annalect.com
                            > Enter the password to connect
                    """)
            print(msg)
            with open(f'keys/credentials-{user_name}.txt', 'w') as fh:
                fh.write(msg)
            print('Operation completed!')

        except Exception as e:
            print(e)
    elif require_password is False:
        try:
            secrets.create_secret(
                Name = 'SFTP/'+user_name,
                Description = 'Sftp Access to '+ user_name,
                SecretString = json.dumps({
                    "PublicKey": user_pub_key,
                    "Role": role_arn,
                    "HomeDirectory": home_directory
                }),
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'annalect-tech-' + user_name
                    },
                    {
                        'Key': 'purpose',
                        'Value': 'sftp'
                    },
                ]
            )
            print(dedent(
                f"""\
                Successfully Created Sftp Account. Please see below the details:

                    UserName : {user_name}
                    Private Keyfile Location/Name : "./keys/{user_name}.pem"

                    You can connect to Sftp using the following command:

                        sftp -i ./keys/{user_name}.pem {user_name}@sftp.annalect.com

                Operation Completed"""))
        except Exception as e:
            print(e)

        # upload credentials to S3
        #bucket = 'annalect-annalect-devops'
        #path = "keys"
        #files = [f"{user_name}.pem", f"{user_name}.pub"]
        #for file in files:
        #    upload_file(os.path.join(path, file), bucket, object_name=file)

def get_policy_name():
    global s3_path
    global s3_bucket
    if s3_path == "":
        policy_name = "sftp-"+s3_bucket+"-readWrite"
    else:
        policy_name = "sftp-"+s3_bucket+"/"+s3_bucket+"-readWrite"
    policy_name = policy_name.replace(" ", "_")
    policy_name = policy_name.replace("/", "_")
    return(policy_name)

def create_role():
    # Create IAM client
    iam = boto3.client('iam')
    global user_name
    global role_arn
    global role_name
    path='/'
    role_name='sftp-'+ user_name
    description='Allow AWS Transfer to call AWS services for the Sftp User' + user_name
    trust_policy={
    "Version": "2012-10-17",
    "Statement": [
        {
        "Sid": "",
        "Effect": "Allow",
        "Principal": {
            "Service": "transfer.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
        }
    ]
    }

    tags=[
        {
            'Key': 'Project',
            'Value': 'sftp-tech-'+user_name
        }
    ]

    try:
        response = iam.create_role(
            Path=path,
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=description,
            MaxSessionDuration=3600,
            Tags=tags
        )
        print('Successfully Created new Role : ' + role_name )
        role_arn = response['Role']['Arn']
        role_name = response['Role']['RoleName']
    except Exception as error:
        print(f"Role name '{role_name}' already exists. Ignoring.")
        raise()
        # return(e)

def get_policy_folder_readWrite():
    global s3_path
    global s3_bucket
    s3_path = re.sub('[/]+$', '', s3_path)
    s3_path = re.sub('^[/]+', '', s3_path)

    policy_readWrite={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket",
                    "s3:GetBucketLocation",
                    "s3:ListBucketMultipartUploads"
                ],
                "Resource": "arn:aws:s3:::"+s3_bucket,
                "Condition": {
                    "StringLike": {
                        "s3:prefix": [
                            s3_path+"/*",
                            s3_path
                        ]
                    }
                }
            },
            {
                "Effect": "Allow",
                "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObjectVersion",
                "s3:DeleteObject",
                "s3:GetObjectVersion",
                "s3:GetObjectACL",
                "s3:PutObjectACL"
                ],
                "Resource": [
                    "arn:aws:s3:::"+s3_bucket+"/"+s3_path+"/*"
                ],
                "Condition": {}
            }
        ]
    }
    return(policy_readWrite)

def get_user_inputs():
    global user_name
    global home_directory
    global s3_bucket
    global s3_path

    user_name = args.username
    if not args.username:
        while user_name is "":
            user_name = input('Enter "user_name" (no spaces or special chars. allowed): ')

    if re.search('[. ]', user_name):
        raise ValueError('Invalid username')

    s3_bucket = args.bucket
    if not s3_path:
        while s3_bucket is "" or not valid_chars_regex.match(s3_bucket):
            s3_bucket = input('Enter "bucket_name" (no spaces or special chars. allowed): ')

    s3_path = args.prefix
    if not s3_path:
        while s3_path is "" or not valid_chars_directory_regex.match(s3_path):
            s3_path = input('Enter "directory" (path/to/folder) (Not including the bucket name and no spaces or special chars. allowed): ')

    home_directory='/'+s3_bucket+'/'+s3_path+'/'

def upload_file(file_name, bucket, object_name=None):

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except Exception as e:
        raise e
        # return False
    return True


def yes_or_no(question):
    reply = str(input(question+' Enter (y/n): ')).lower().strip()
    if reply == 'y':
        return True
    if reply == 'n':
        return False
    else:
        return yes_or_no("Uhhhh... please enter ")

if __name__ == "__main__":
    # execute only if run as a script
    args = get_args()
    main()
