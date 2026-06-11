""" Export suscriptions of log_groups """
import argparse
import sys

import boto3
#import json
from pprint import pprint
#import re
import sys

try:
    from tqdm import tqdm
    import pandas as pd
except:
    print('Please install tqdm: pip3 install tqdm pandas')
    sys.exit(1)

def get_args():
    parser = argparse.ArgumentParser(description='Description')

    # parser.add_argument("-n", "--name", default=None,
    #                 help="Name of ...")

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
    """ Export suscriptions of log_groups """
    fns = []
    fn_list = []


    client = boto3.client('lambda')
    cloudtrail = boto3.client('cloudtrail')
    logs = boto3.client('logs')
    # response = client.list_functions()
    next_marker = None
    params = {}
    while True:
        if next_marker is not None:
            params = {'Marker': next_marker}

        response = client.list_functions(**params)

        fn_list += response['Functions']
        if 'NextMarker' not in response: break
        next_marker = response.get('NextMarker')

    for fn in tqdm(fn_list):
        row = {}
        runtime = fn['Runtime']

        properties = [
            'FunctionName',
            'Runtime',
            'LastModified',
            'Version',
            'Role',
            'Description',
        ]

        for p in properties:
            row[p] = fn[p]

        response = cloudtrail.lookup_events(
            LookupAttributes=[
                {
                    'AttributeKey': 'ResourceName',
                    'AttributeValue': fn['FunctionName']
                },
            ],
            MaxResults=1,
        )

        row['FunctionLastUsed'] = 'N/A'
        if len(response['Events']) > 0:
            row['FunctionLastUsed'] = response['Events'][0]['EventTime'].strftime('%Y-%m-%d')

        fns.append(row)


    df = pd.DataFrame(fns)
    fname = 'LambdaFunctions.xlsx'
    df.to_excel(fname, index=False)
    print(f'{fname} generated in current path.')



    pass

if __name__ == "__main__":
    args = get_args()

    main()