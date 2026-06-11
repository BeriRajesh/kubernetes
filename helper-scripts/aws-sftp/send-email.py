import argparse
import os

import boto3

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

def get_args():
    parser = argparse.ArgumentParser(description='Script to send emails via AWS SES')

    parser.add_argument("-s", "--subject", default=None,
                    help="Email's subject")

    parser.add_argument("-f", "--fromx", default=None,
                    help="From: address")

    parser.add_argument("-t", "--to", default=None,
                    help="To: addresses. Ex: --to email1@email.com,email2@email.com")

    parser.add_argument("-a", "--attachment", default=[], action="append",
                    help="Attachments to add to email. Ex: -a file1.txt -a path/to/file2.txt")

    parser.add_argument("-b", "--body", default=None,
                    help="Text body of email.")

    parser.add_argument("-c", "--content", default=None,
                    help="Text body of email specified as a file name.")

    parser.add_argument("-d", "--debug", default=None,
                help="Attachments to add to email")

    args = parser.parse_args()

    if args.debug:
        print(args)
        sys.exit()

    return args

args = get_args()

message = MIMEMultipart()
message['Subject'] = args.subject
message['From'] = args.fromx
message['To'] = args.to

# message body
# part = MIMEText(args.body, "plain")
# message.attach(part)
if args.content and os.path.isfile(args.content):
    part = MIMEText(open(str(args.content)).read().replace("\n", "<br />"), "html")
    message.attach(part)
elif args.body:
    part = MIMEText(args.body.replace("\\n", "<br />").replace("\n", "<br />"), "html")
    message.attach(part)

# attachment
attachment_string = None
for attachment in args.attachment:
    if attachment_string:   # if bytestring available
        # unimplemented
        part = MIMEApplication(str.encode('attachment_string'))
    else:    # if file provided
        part = MIMEApplication(open(attachment, 'rb').read())
    part.add_header('Content-Disposition', 'attachment', filename=attachment.split("/")[-1])
    message.attach(part)

ses = boto3.client('ses', region_name='us-east-1')

response = ses.send_raw_email(
    Source=message['From'],
    Destinations=message['To'].split(","),
    RawMessage={
        'Data': message.as_string()
    }
)
