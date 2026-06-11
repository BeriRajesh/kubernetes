#!/usr/bin/env python3

import sys
import base64
import os
import psycopg2
import pandas.io.sql as pdsql

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

import boto3
from botocore.exceptions import ProfileNotFound
from botocore.exceptions import ClientError

from pandas import *

###email imports
# Import smtplib for the actual sending function
import smtplib
# Here are the email package modules we'll need
from email.message import EmailMessage


from pprint import pprint


#importing configuration: reports, etc...
import configuration
from configuration import reports

# global_error_list
global_error_list = []


#### Configuration
db_host = 'comscore-procdata-dw2.clf6bikxcquu.us-east-1.redshift.amazonaws.com'
db_name = 'comscore'
db_user = 'cocadmin'
aws_iam_role_arn = 'arn:aws:iam::661095214357:role/lambda_analytic_dataflow'
enc_password = 'AQECAHhC/TasQRjb5eF2cXRe50MayRQ/POmCWSEGdyIjD8ifiwAAAHMwcQYJKoZIhvcNAQcGoGQwYgIBADBdBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDBchcSWtwPB0ETRSlQIBEIAwjS/2gvip8H4ya1+nlkxtuFJhUdTmEoF77ozWFDPXCToO86rT58X2neoeIkwwLGdv'
#Decrypt password
# try:
#         kms = boto3.client('kms', region_name='us-east-1')
#         db_pw = kms.decrypt(CiphertextBlob=base64.b64decode(enc_password))['Plaintext']
# except:
#         print('KMS access failed: exception %s' % sys.exc_info()[1])
db_pw = "***REMOVED***"


def connect():
        conn = psycopg2.connect(
                "dbname='{dbname}' host='{dbhost}' port='5439' user='{username}' \
                password='{password}'".format(dbname=db_name, dbhost=db_host, username=db_user,password=db_pw)
        )
        conn.set_session(autocommit=True)
        cur = conn.cursor()

        return conn, cur


def fetch_data(sql_string, parameters: None):
    cur.execute(sql_string, parameters)
    colnames = tuple([desc[0] for desc in cur.description])
    data = list(cur)

    return list(data), colnames

def validate_report(data, report):
    error_messages = []


    if 'validations' in report:
        for validation in report['validations']:
            #validation should only have one key:value pair
            validation_name = list(validation.keys())[0]
            expected_value = list(validation.values())[0]

            # checking if validation exist as a function in module configuration
            if validation_name in dir(configuration):
                # calling validation function on the report
                validation_message = getattr(configuration, validation_name)(data, expected_value)
                if validation_message is not "":
                    error_messages.append({
                        'validation': validation_name,
                        'message': validation_message
                    })
            else:
                # should maybe return an error instead
                print("Validation function `{}` couldn't be found".format(validation))

    return error_messages

def generate_report_dataframe(report):
    """Returns a pandas Dataframe with the report information and the validation object"""

    # fetching report and columns
    data, column_names = fetch_data(report['sql_string'], report['parameters'])
    df = DataFrame(data, columns=column_names)

    return df

def build_report_html(df, report):
    report = "<h2>{} ({})</h2>".format(report['report_filename'], report['date_string'])
    for error in error_messages:
        report += "<h3>Error `{}`: {}</h2>".format(error['validation'], error['message'])

    report += df.to_html()

    return report

def write_report_file(html, report):
    with open(report['report_filename'], 'w') as fh:
        fh.write(html)

def send_ses_email(report):
    # specify sender and recipient of email
    SENDER = "[Automated Report] <donotreply@annalect.com>"
    RECIPIENT = ["anmichel.rodriguez@annalect.com"]

    # Create a new SES resource and specify a region.
    boto3_session = boto3.session.Session(profile_name='default')
    print(boto3_session)
    client = boto3_session.client('ses')

    # Try to send the email.
    try:
        msg = MIMEMultipart()

        # what a recipient sees if they don't use an email reader
        msg.preamble = 'Reports attached.\n'

        msg['Subject'] = 'comscore_rdf_data_validation'

        # the message body
        part = MIMEText('Please see attached comscore_rdf_data_validation automated reports.', 'plain')
        msg.attach(part)

        part = MIMEApplication(open(report['report_filename'],'rb').read())
        part.add_header('Content-Disposition', 'attachment', filename=report['report_filename'])

        msg.attach(part)

        # send email
        response = client.send_raw_email(
            Source=SENDER,
            Destinations=RECIPIENT,
            RawMessage={'Data': msg.as_string()}
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print("error")
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['ResponseMetadata']['RequestId'])


conn, cur = connect()

# html contents of all reports
all_reports = ""

# for testing purposes
# max_reports = 0
for report in reports:
    if 'enabled' in report and report['enabled'] is False:
        print("report {} is disabled".format(report['report_filename']))
        continue

    print("{} is enabled".format(report['report_filename']))

    try:
        df = generate_report_dataframe(report)
    except:
        print("Error with report {}".format(report['report_filename']))
        continue

    # do report data validations
    error_messages = validate_report(df, report)
    if len(error_messages) > 0:
        global_error_list = global_error_list + [{'report': report['report_filename'], 'messages': error_messages}]

    html = build_report_html(df, report)
    all_reports += html

    # if max_reports >= 1:
    #     break
    # max_reports =+ 1


# making an error summary of all the reports
error_summary_html = ""
if len(global_error_list) > 0:
    error_summary_html = "<h1>Report Error Summary</h1>"
    for error in global_error_list:
        for message in error['messages']:
            error_summary_html += "<h3>Report: `{}`, Error `{}`: {}</h2>".format(
                error['report'], message['validation'], message['message'])
    error_summary_html += "<hr>"

all_reports = "<h1>Reports<h1>" + all_reports

# write reports file to send as attachment
write_report_file(error_summary_html + all_reports, {'report_filename': 'all.html'})

# send email with attachment
send_ses_email({'report_filename': 'all.html'})

conn.close()


