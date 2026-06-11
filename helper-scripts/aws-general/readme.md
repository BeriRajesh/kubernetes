# Helper Scripts - AWS-GENERAL
(newest info reading the readme.md docs in the repository/folder)

# Preface

This document provides documentation for the scripts

1) export_resources.py

# 1) Create Bucket (export_resources.py)

This script creates CSV files with information of resources from our AWS environment.

Namely it currently  exports `s3,ec2,elb,rds or redshift` or all of them. 

## Getting Started

To see the options provided by the script, run

```bash
$ ./export_resources.py -h
usage: export_resources.py [-h] [-v] [-p PROFILE] [-f FOLDER] [-i]
                           [{all,s3,ec2,elb,rds,redshift}]

Export resources from AWS

positional arguments:
  {all,s3,ec2,elb,rds,redshift}
                        Action to perform (defaults to all)

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Increase output verbosity
  -p PROFILE, --profile PROFILE
                        AWS profile to use. Defaults to 'default'
  -f FOLDER, --folder FOLDER
                        path to folder to put output files. MUST end with `/`
  -i, --interactive     Presents a prompt before executing copying commands
                        tosource files
```

### Prerequisites

The script is made for Python 3.

The script make use of the `boto3` library. You can install this library with
 
```bash
$ pip3 install boto3
```

Add your credentials in ~/.aws/credentials or have an AWS IAM Role configured for your computer.

### Installing

As of the moment, this script depends on cloning the `https://anmichelr@bitbucket.org/annalect/devops.git` repository
and executing from the `helper-scripts/aws` folder.

To clone and execute:

```bash
$ git clone https://anmichelr@bitbucket.org/annalect/devops.git
$ cd devops/helper-scripts/aws-general
$ ./export_resources.py
```

## Running the tests

No tests available when writing this doc.

## Built With

* Python3
* Boto3

## Contributing

The helper scripts are meant to be used and updated to help automate repetitive DevOps activities.

Feel free to make your branch of the project and contribute improvements. 

## Authors

* **An Michel Rodriguez** (anmichel.rodriguez@annalect.com / anmichel.rodriguez@gmail.com)


## Acknowledgments

* Shashikant Kuwar for initial inspiration for this script.
