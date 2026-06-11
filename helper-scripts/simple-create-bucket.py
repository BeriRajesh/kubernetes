import sys
import boto3
from botocore.exceptions import ProfileNotFound

# simple
#choose profile helper-script
profile_name = 'helper-script'
while True:
    try:
        boto3_session = boto3.session.Session(profile_name=profile_name)
        print("Using session `"+profile_name+"`")
        print(boto3_session)
        break;
    except ProfileNotFound as e:
        profile_name = input('The profile `'+profile_name+'` could not be found. Please input the name of a profile to use [default]: ')
        if profile_name == "":
            profile_name = 'default'

s3 = boto3_session.client('s3')
s3.create_bucket(Bucket='an-an')