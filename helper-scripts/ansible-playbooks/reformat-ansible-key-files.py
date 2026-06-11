"""
This Script was written to format the output of the AWS Keys search when using ansible, as described in the key_rotation_guide.md

The guide suggests to execute:

```
for env in Dev QA MGMT Prod; do ./select_hosts.py -e $env --become --command 'find /home -type f -size -100k -not -path "*.ansible*" -exec grep -HT -E "\b[A-Z][A-Z0-9]{19}\b" {} \;' | sed -E 's/([^:]*)(.*)\b([A-Z][A-Z0-9]{19})\b(.*)/\3\t\1/g' | tee -a keys-ansible; done
```

The above command generates an Ansible formatted output file `keys-ansible`.

With this script that file can be further processes into a csv with columns
ip, key, location

Usage:
```
$ python3 reformat-ansible-key-files.py -f keys-ansible
````

That command generated a file named `keys-ansible-processes.csv` which can be opened in Excel.


"""

import pandas as pd

import argparse
import boto3
import sys
import json
import re
from pprint import pprint

def get_args():
    parser = argparse.ArgumentParser(description='Description')

    parser.add_argument("-f", "--file", default=None,
                    help="Ansible's output file to process")

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
    """ process ansible's output into columns """

    fh = open(args.file)

    serverip = None
    newlines = []
    print("Processing file... might take a short while...")
    for line in fh:
        print(line)
        match = re.match('^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*', line.strip())
        if not match and serverip is None:
            continue

        if match:
            serverip = match.groups(1)[0]
            continue

        if serverip:
            matchkey = re.match('(.*\.us-east-1\.rds\.amazonaws\.com)\t(.*)', line)
            if matchkey:
                key = matchkey.groups(1)[0]
                location = matchkey.groups(1)[1]
                newlines.append(
                    [serverip, key, location]
                )
                stop = 1
            else:
                pass
                # newlines.append(
                #     [serverip, line]
                # )
            # pprint(newlines)

    df = pd.DataFrame(newlines, columns=['server ip', 'aws key', 'location'])
    df.to_csv(f'{args.file}-processed.csv', index=False)

if __name__ == "__main__":
    args = get_args()

    main()
