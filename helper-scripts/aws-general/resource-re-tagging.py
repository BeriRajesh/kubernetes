#!/usr/bin/env python3

"""update tags on AWS resource based on name of resource"""

import argparse
import os
import sys

sys.path.append('../')
import lib.helper_functions as hf
import lib.amazon_helper as ah

hf.verbose = 1


parser = argparse.ArgumentParser(description='Export resources from AWS', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("file", help="File to process for retagging. "
                                 "\nMust be in CSV readable format."
                                 "\nHeader should be the first rows, comprising the columns:"
                                 "\n  type,region,name,Tag: xxxx,Tag: yyyyy"
                                 "\nFirst column must have the resource type,"
                                 "\nSecond column the resource name (identifier) "
                                 "\nThe next columns should have the heading `Tag: tagname`, with the value of the tag "
                                 "\n  in the corresponding cell/row."
                                 "\n"
                                 "\nExample contents of file.csv:"
                                 "\n  type,region,name,Tag: Project, Tag: Client"
                                 "\n  s3,,ADW-Backup,Infrastructure,annalect-annalect-inscape"
                                 "\n  ec2,eu-west-1,EU-WWW-ANNALECT-DEV,Infrastructure,annalect-annalect-inscape"
                                 "\n"
                                 "\nNotes:"
                                 "\n - Remember S3 Buckets have no region (leave field empty, as in the example)"
                                 "\n - If region is not specified it defaults to `us-east-1` and then `eu-west-1`, "
                                 "\n   then fails"
                                 "\n - *values will be trimmed for spaces"
                                 "")
parser.add_argument("-v", "--verbose", default=0, help="Increase output verbosity", action='count')
# parser.add_argument("-p", "--profile", default='', help="AWS profile to use. Defaults to 'default'")
# parser.add_argument("-i", "--interactive", default='', help="Presents a prompt before executing copying commands to"
#                                                             "source files", action='store_true')
args = parser.parse_args()

hf.verbose = args.verbose

AmazonHelper = ah.AmazonHelper()
boto3_session = AmazonHelper.session()

AmazonHelper.retag(path=args.file)

