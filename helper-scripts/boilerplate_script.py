""" Description of what the script does

    You can include some usage instructions or examples
"""
import argparse
import sys

# try:
#     from tqdm import tqdm
#     import pandas as pd
# except:
#     print('Please install tqdm: pip3 install tqdm pandas')
#     sys.exit(1)
#import boto3
#import json
#from pprint import pprint
#import re

def get_args():
    parser = argparse.ArgumentParser(description='Description')

    parser.add_argument("-n", "--name", default=None,
                    help="Name of ...")

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
    """ put your code here """
    pass

if __name__ == "__main__":
    args = get_args()

    main()