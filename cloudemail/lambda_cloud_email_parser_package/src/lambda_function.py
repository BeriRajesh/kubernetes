""" Lambda function to process cloudemails

********
IMPORTANT: Remember to keep this repository updated with the latest version of the function.
********


# Deployment instruction (Linux):

    This function is available on the devops repository:
        path of this file:
            devops/helper-scripts/service-scripts/lambda_cloud_email_parser_package/src/lambda_function.py

        # Before deploying, you need a virtual environment to isolate the requirements the function
            $ cd devops/helper-scripts/service-scripts/lambda_cloud_email_parser_package
            $ python3 -v venv venv
            $ . venv/bin/activate
            $ pip3 install -r requirements.txt

        # If you need to install new packages:
            $ . venv/bin/activate
            $ pip3 install my_very_much_needed_package
            $ pip3 freeze > requirements.txt
            $ git commit -m "new requirements" requirements.txt

        $ cd path/to/devops/helper-scripts/service-scripts/lambda_cloud_email_parser_package
        $ ./deploy_function.sh

        This generates a file `lambda_cloud_email_parser_package.zip` that can be uploaded to AWS Lambda

"""

import ast
import cgi
import email
from email.utils import getaddresses
import json
import os
import re
import sys
import time
import traceback
import urllib
import logging

import boto3
import botocore
from bs4 import BeautifulSoup
from get_urls_from_body import get_urls_from_plain_part

# showing INFO log lines
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler_error_manager(event, context):
    """always returns true to avoid lambda retries"""

    try:
        lambda_handler(event, context)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print('ERROR: An error occured')
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)

    return True


def lambda_handler(event, context):
    """
    Lambda function that gets raw email from s3.
    """
    # print("Event:")
    # print(json.dumps(event, indent=4, default=str))

    # print("Context:")
    # print(context)

    s3 = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    cloudemails_table = dynamodb.Table('cloudemails')

    sns_message = ast.literal_eval(event['Records'][0]['Sns']['Message'])
    source_bucket = str(sns_message['Records'][0]['s3']['bucket']['name'])
    key = str(urllib.parse.unquote_plus(
        sns_message['Records'][0]['s3']['object']['key']))

    # .decode('utf8'))

    LOCAL_PATH = '/tmp/' + str(key.split("/")[-1])
    print("source_bucket: " + source_bucket)
    print("source_key: " + key)

    try:
        s3.download_file(source_bucket, key, LOCAL_PATH)
        pass
    except botocore.exceptions.ClientError as excep:
        print("ERROR: Error trying to fetch from bucket: `{source_bucket}`, key: `{key}`".format_map({
            "source_bucket": source_bucket,
            "key": key
        }))
        print("Are you running locally and using an outdated example variable?")
        return False

    # , mode = 'r', buffering = -1))
    with open(LOCAL_PATH, 'r') as fh:
        msg = email.message_from_file(fh)

    email_id = None

    # if msg.get('To') is not None:
    #     email_reobj = re.search('(tclna)\+?([^@]*)@', msg.get('To'))
    #     if hasattr(email_reobj, 'group') and len(email_reobj.groups()) > 0:
    #         email_id = email_reobj.groups()

    tos = msg.get_all('to', [])
    ccs = msg.get_all('cc', [])
    resent_tos = msg.get_all('resent-to', [])
    resent_ccs = msg.get_all('resent-cc', [])
    all_recipients = getaddresses(tos + ccs + resent_tos + resent_ccs)

    print(all_recipients)
    for name, e in all_recipients:
        email_id = None
        # email_reobj = re.search('(tclna)\+?([^@]*)@', e)
        # if hasattr(email_reobj, 'group') and len(email_reobj.groups()) > 0:
        #     email_id = email_reobj.groups()[1]
        # else:

        # complete regular expression for a valid address of any kind
        # re.search('[a-zA-Z0-9_\-\.+]+@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([a-zA-Z0-9\-]+\.)+))([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)', e)

        valid_domains = [
            "annalect.cloud",
            "heartscience.cloud"
        ]

        for domain in valid_domains:
            matches = re.search(f'[a-zA-Z0-9_\-\.+]+@{domain}', e)
            if matches is not None:
                email_id = matches[0]

        if email_id is None:
            print(f"`{e}` is not a valid cloudemail address")
            continue

        try:
            response = json.loads(
                cloudemails_table.get_item(
                    Key={
                        'id': email_id
                    }
                )["Item"]["value"]
            )
            time.sleep(1)
        except Exception as excep:
            print(f"ERROR: Error retrieving clientId=`{email_id}` from DynamoDB. Does it exists in "
                  f"cloudmails DynamoDB Table? Is the format valid?")
            print(excep)
            continue
            # return False

        # print(response["Item"]["value"])
        # msg.get('destbucket')

        saveBody = "saveBody" in response and response["saveBody"] == "1"
        # if saveBody:
        #     emailBody = msg.get_body(preferencelist=('plain','html'))

        destbucket = response["destination_bucket"]
        # msg.get('destbucketprefix')
        destbucketprefix = response["prefix"]

        print("destbucket: " + destbucket)
        print("destbucketprefix: " + destbucketprefix)
        print("email_id: " + email_id)

        ls = []
        url_ls = []

        if msg.is_multipart():
            for payload in msg.get_payload():
                ls.extend(check_mulitpart(payload))
        else:
            ls.extend([msg])

        att_filename = ""
        textContent = b""
        for payload in ls:
            # print(f"Raw payload is {payload}")
            print("Payload is {}".format(payload.get('Content-Disposition')))
            # filters out any image attachments
            content = payload.get_payload(decode=True)
            if payload.get('Content-Disposition') and payload.get_content_type().split('/')[0] != 'image':
                try:
                    payload_filename = payload.get_filename()
                    print(f"Filename: {payload_filename}")
                except:
                    print("ERROR: could not get filename from payload")
                    continue

                if payload_filename is None:
                    print("ERROR: payload_filename is None")
                    continue

                att_filename = ''.join(payload_filename.splitlines())


                if check_file_valid(att_filename):
                    destbucketprefix_temp, att_filename = add_prefix(
                        destbucketprefix, att_filename)

                    print("Attachment to be uploaded: %s" % att_filename)

                    upload_to_s3(
                        content,
                        att_filename,
                        s3,
                        destbucket,
                        destbucketprefix_temp
                    )

                    # if saveBody:
                    #     upload_to_s3(
                    #         emailBody,
                    #         att_filename+'.txt',
                    #         s3, destbucket, destbucketprefix_temp)

                    # deleting original mail
                    # print("deleting from {}/{}".format(source_bucket, key))
                    # response = s3.delete_object(
                    #     Bucket=source_bucket,
                    #     Key=key
                    # )
                else:
                    print("ERROR: File `{}` does not have a valid extension. Valid extension are {}".format(att_filename, os.environ['valid_file_ext']))

            elif payload.get_content_type() == 'text/html':
                textContent += content
                # https://pythonspot.com/en/extract-links-from-webpage-beautifulsoup/

                soup = BeautifulSoup(content)

                for link in soup.findAll('a', attrs={'href': re.compile("^http|https://")}):
                    url_ls.append(link.get('href'))

            elif payload.get_content_type() == 'text/plain':
                textContent += content
                url_ls.extend(get_urls_from_plain_part(content))

        # def upload_to_s3(content, filename, s3, destbucket, destbucketprefix):
        if saveBody and textContent and att_filename:
            upload_to_s3(
                content=textContent,
                filename=f"{att_filename}.txt",
                s3=s3,
                destbucket=destbucket,
                destbucketprefix=destbucketprefix_temp,
                content_type='t'
            )

        # uploading email to archive
        archive_prefix = str(
            "/".join(key.split("/")[:-1])) + "-archive" + "/" + email_id + "/" + str(key.split("/")[-1])
        print("uploading mail from bucket {}, from prefix {} to prefix {}".format(
            source_bucket, key, archive_prefix))
        transfer = boto3.s3.transfer.S3Transfer(client=s3)
        transfer.upload_file(
            LOCAL_PATH,
            source_bucket,
            archive_prefix,
            extra_args={'ServerSideEncryption': "AES256"}
        )

        transfer.upload_file(
            LOCAL_PATH,
            source_bucket,
            archive_prefix,
            extra_args={'ServerSideEncryption': "AES256"}
        )

        check_url_repeats = []

        print(f"urls: {url_ls}")
        for url in list(set(url_ls)):
            content = ""
            try:
                response = urllib.request.urlopen(url)

                if url not in check_url_repeats:
                    url = response.geturl()
                    check_url_repeats.append(response.geturl())

                    _, params = cgi.parse_header(
                        response.headers.get('Content-Disposition', ''))
                    content_type, _ = cgi.parse_header(
                        response.headers.get('Content-Type', ''))

                    try:
                        if params['filename']:
                            filename = params['filename']
                    except KeyError:
                        split_path = urllib.parse.urlsplit(url)
                        filename = urllib.parse.unquote(split_path.path.split(
                            "/")[-1])  # .encode('string-escape')

                    if check_file_valid(filename) and content_type.split('/')[0] != 'image':
                        content = response.read()

                        print('Filename: %s' % filename)
                        print('downloaded from URL: %s' % url)
            except:
                print("ERROR: Failed to download file from URL: %s" % url)
                # traceback.print_exc()
            else:
                # uploading to client bucket
                print("uploading file to destination")
                if content == "":
                    print("ERROR: No content to upload")
                else:
                    destbucketprefix_temp, filename = add_prefix(
                        destbucketprefix, filename)
                    upload_to_s3(content, filename, s3,
                                destbucket, destbucketprefix_temp)
                    print(f"Content uploaded to {destbucket}/{filename}")



def check_file_valid(filename):
    valid_file_ext = ast.literal_eval(os.environ['valid_file_ext'].lower())
    return filename.split('.')[-1].lower() in valid_file_ext


def upload_to_s3(content, filename, s3, destbucket, destbucketprefix, content_type='b'):
    """
    Uploads files to s3

    Args:
        ....
        content_type: 'b' for binary, 't' for text
    """

    try:
        logger.info(f"content_type: {content_type}")
        logger.info(f"type of content: {type(content)}")
        if content_type == 't':
            print('original:')
            print(content)
            print('decoded:')
            print(content.decode())

        if type(content) == bytes and content_type == 't':
            print('Decoding content...')
            content = content.decode()

        open('/tmp/' + filename, f'w{content_type}').write(content)
        print("Copying file \"%s\" into S3 bucket..." % filename)

        # 18-06-14 added to upload using Server Side Encryption
        transfer = boto3.s3.transfer.S3Transfer(client=s3)

        if destbucketprefix == "":
            prefix = filename
        else:
            prefix = destbucketprefix + '/' + filename

        transfer.upload_file(
            '/tmp/' + filename,
            destbucket,
            prefix,
            extra_args={'ServerSideEncryption': "AES256"}
        )

        # original
        # s3.upload_file('/tmp/' + filename, destbucket, destbucketprefix + '/' + filename)

        print("Successfully uploaded \"%s\" into s3://%s/%s" %
              (filename, destbucket, destbucketprefix))
    except:
        print("ERROR: Failed to upload \"%s\" into s3://%s/%s!" %
              (filename, destbucket, destbucketprefix))
        traceback.print_exc()


def check_mulitpart(payload):
    """
    Recursive function that checks if a payload
    is multipart, until it is not.
    """
    if payload.is_multipart():
        for pay in payload.get_payload():
            return check_mulitpart(pay)
    else:
        return [payload]


def add_prefix(destbucketprefix, filename, separator="@@"):
    "Uses the filename prefix to copy data in s3"
    if separator in filename:
        fn_sep = filename.split(separator)

        dir_name = fn_sep[0].strip()
        filename = separator.join(fn_sep[1:]).strip()

        destbucketprefix += '/' + dir_name
    return destbucketprefix, filename


if __name__ == '__main__':
    # some test values to work locally
    os.environ["valid_file_ext"] = "['zip', 'csv', 'tsv', 'gz', 'txt', 'pptx', 'xlsx', 'xls', 'pdf']"
    event = {
        "Records": [
            {
                "EventSource": "aws:sns",
                "EventVersion": "1.0",
                "EventSubscriptionArn": "arn:aws:sns:us-east-1:661095214357:Tester:a31c6ad4-9dc3-40c5-95e3-258d8febdbd7",
                "Sns": {
                    "Type": "Notification",
                    "MessageId": "11bf478c-d61b-5224-9696-14246628dfb3",
                    "TopicArn": "arn:aws:sns:us-east-1:661095214357:Tester",
                    "Subject": "Amazon S3 Notification",
                    "Message": "{\"Records\":[{\"eventVersion\":\"2.0\",\"eventSource\":\"aws:s3\",\"awsRegion\":\"us-east-1\",\"eventTime\":\"2018-06-23T20:30:43.103Z\",\"eventName\":\"ObjectCreated:Put\",\"userIdentity\":{\"principalId\":\"AWS:AIDAIE26RTG3F45XIHQFI\"},\"requestParameters\":{\"sourceIPAddress\":\"10.90.28.0\"},\"responseElements\":{\"x-amz-request-id\":\"FE240658BA23BADF\",\"x-amz-id-2\":\"AJ6nuHlkL23Vcj0ORIbJ1vHEgWSaBnAWqm6tJG1q4NkcLQtJMrnj67QFPCH8lOxbIwR/AUAVT5g=\"},\"s3\":{\"s3SchemaVersion\":\"1.0\",\"configurationId\":\"shashik@annalect.cloud\",\"bucket\":{\"name\":\"annalectcloudmail\",\"ownerIdentity\":{\"principalId\":\"A1W3E13ANB6UFL\"},\"arn\":\"arn:aws:s3:::annalectcloudmail\"},\"object\":{\"key\":\"mail/45cr939n6hnovpfrs2d3eovfn5c0189tavt6glg1\",\"size\":11303,\"eTag\":\"043f6af805cf7db5dc5f9ae5c4f47305\",\"sequencer\":\"005B2EADF30DDB325E\"}}}]}",
                    "Timestamp": "2018-06-23T20:30:43.221Z",
                    "SignatureVersion": "1",
                    "Signature": "xicGfyfwFS0FcZ636oWKZTaURyKb4uhz4AUi8ImT5e6Q9326PWKy7Wm1t805vRu9xcWhB5E0WCMY+jVDcs8hp3Cay1fNp6AYc9o6wNO+hiKogvOU6iJX+UXnQqtGe1a6vUQY+9QZvul1L8edX7pjvXW0xw0c7Nc7HXe5WDDcSbM7GCmQvvvXKQuZaPY5OIJCwq3HbMQx4UJydXvQN4+yyBT8+cUfDA1wFo3tXjnqmvVlwU9YnQyLZQFxumrx3nPGSx/plC9+O7xH8QG+cW+d4EKOWMu5S+hcr4Ng7CDybRsvwE0LuH7wiypvbEew/UEresItKdQ9xWP9oEc4YkGPGQ==",
                    "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-eaea6120e66ea12e88dcd8bcbddca752.pem",
                    "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:661095214357:Tester:a31c6ad4-9dc3-40c5-95e3-258d8febdbd7",
                    "MessageAttributes": {}
                }
            }
        ]
    }
    context = None
    # print(event)
    # sys.exit()
    lambda_handler_error_manager(event, context)
