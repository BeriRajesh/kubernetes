""" tag service accounts
script based on "keys-last-used"script
"""
import argparse
import sys
import botocore
from botocore.exceptions import ClientError

import pandas as pd
import boto3
import json
from pprint import pprint
#import re
from io import StringIO


keys = StringIO("""old_aws_key	new_aws_key
AKIAZT3CYNUK3V4IMEVL	AKIAZT3CYNUKZM66KJUU
AKIAZT3CYNUK3J2KTAX4	AKIAZT3CYNUK72BNPGH7
AKIAIIH5HTPYP7LQXR7Q	AKIAZT3CYNUK63FBALKD
AKIAJEISDLGIYWRHM6KA	AKIAZT3CYNUK5PWOME7B
AKIAJRWHIOCJLWKAVFBA	none
AKIAJRWHIOCJLWKAVFBA	AKIAZT3CYNUKYHZWY5GH
AKIAIT5RYWN2UIGLK3RA	AKIAZT3CYNUKUL2Y2LCJ
AKIAZT3CYNUKUKLJ2UU2	AKIAZT3CYNUK23SBUHTG
AKIAI2TTXMFWBSNDHJAA	AKIAZT3CYNUK7R435R5T
AKIAIT5RYWN2UIGLK3RA	AKIAZT3CYNUKW5WP7FGC
AKIAZT3CYNUKQEVQNAEA	AKIAZT3CYNUK7U3OM56E
AKIAINSZ3WCXQGN7SBUA	AKIAZT3CYNUKU45JDVFM
AKIAIUWLMYTUCEL7AYMA	AKIAZT3CYNUKSOFYMBU2
AKIAJNZUPURYTE3E6GJQ	AKIAZT3CYNUK3XOJ33HA
AKIAINSZ3WCXQGN7SBUA	AKIAZT3CYNUKRMHSI2PP
AKIAIUWLMYTUCEL7AYMA	AKIAZT3CYNUK7W4WWENW
AKIAJ3BIREIBICYBH2RA	AKIAZT3CYNUKR54JGNCD
AKIAINSZ3WCXQGN7SBUA	AKIAZT3CYNUKSMS4555C
AKIAIUWLMYTUCEL7AYMA	AKIAZT3CYNUKYO32I5L2
AKIAINSZ3WCXQGN7SBUA	AKIAZT3CYNUKSLTOWXUY
AKIAIUWLMYTUCEL7AYMA	AKIAZT3CYNUK2OXNWOVM
AKIAJ3BIREIBICYBH2RA	AKIAZT3CYNUKUHTPUS4L
AKIAINE4MJA4LCECLY3Q	AKIAZT3CYNUK6ZJUF4KY
AKIAINSZ3WCXQGN7SBUA	AKIAZT3CYNUKUL2YISD6
AKIAINSZ3WCXQGN7SBUA	AKIAZT3CYNUKU6VDRFI2
AKIAINSZ3WCXQGN7SBUA	AKIAZT3CYNUKZI7NHAWZ
AKIAIBZEC6LIKGRNS3IQ	AKIAZT3CYNUK3YLUBW4A
AKIAIBZEC6LIKGRNS3IQ	AKIAZT3CYNUKXADKNYKX
AKIAIBZEC6LIKGRNS3IQ	AKIAZT3CYNUKVRKKOP7T
AKIAIBZEC6LIKGRNS3IQ	AKIAZT3CYNUK6KZFR3JF
AKIAIBZEC6LIKGRNS3IQ	AKIAZT3CYNUKRNPSVYPZ
AKIAIIF4NROLFL6ALG2Q	AKIAZT3CYNUKY5N6K3GL
AKIAIIF4NROLFL6ALG2Q	AKIAZT3CYNUKWCXVUDOQ
AKIAINE4MJA4LCECLY3Q	AKIAZT3CYNUK5VUYAIHX
AKIAINSZ3WCXQGN7SBUA	AKIAZT3CYNUKWZEVPXYY
AKIAINSZ3WCXQGN7SBUA	AKIAZT3CYNUKQCORNNU6
AKIAIUWLMYTUCEL7AYMA	AKIAZT3CYNUKZHDLZI6V
AKIAIVAQ5USPTKFN4U7Q	none
AKIAJ3BIREIBICYBH2RA	AKIAZT3CYNUK56ZQ64WZ
AKIAJ6P4K2RT5PA6WJHQ	AKIAZT3CYNUKT2EB7GXC
AKIAJOWAIX4X25SLFC2Q	AKIAZT3CYNUKTWNEN4WO
AKIAJVCLEV2I4AYO53OA	AKIAZT3CYNUKTEEK377U
AKIAZT3CYNUKQEVQNAEA	AKIAZT3CYNUKTOIZI56W
""")

def get_args():
    parser = argparse.ArgumentParser(description='Description')

    # parser.add_argument("-f", "--file", default=None,
    #                 help="Filename to process")

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
    """ process the file """
    # fname = args.file
    df = pd.read_csv(keys, sep="\t")

    iam = boto3.client('iam')
    iam_res = boto3.resource('iam')

    for i, row in df.iterrows():
        old_key = row['old_aws_key']
        new_key = row['new_aws_key']

        try:
            val = new_key
            response_old = iam.get_access_key_last_used(
                AccessKeyId=val
            )
            val = old_key
            response_new = iam.get_access_key_last_used(
                AccessKeyId=val
            )

            val = response_new['UserName']
            response = iam.tag_user(
                UserName=response_new['UserName'],
                Tags=[
                    {
                        'Key': 'user-type',
                        'Value': 'service'
                    },
                ]
            )

            # df.loc[df['aws key'] == key, "key status"] = access_key["status"]
        except ClientError as e:
            print(e)
            print(f"Could not tag account {val}")
            # df.loc[df['aws key'] == key, 'username'] = 'not found'
            continue
        except Exception as error:
            print(error)
            continue

if __name__ == "__main__":
    args = get_args()

    main()