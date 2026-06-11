# Helper Scripts - AWS-S3
(newest info reading the readme.md docs in the repository/folder)

# Preface

This document provides documentation for the scripts

1) create-bucket.py
2) create-policies.py

# 1) Create Bucket (create-bucket.py)

This script creates the S3 Bucket, readOnly and readWrite access policies and groups with the corresponding policies attached.

## Getting Started

The buckets are created following the agency-client-project convention.

### Prerequisites

The script is made for Python 3.

The script make use of the `boto3` library. You can install this library with
 
```bash
$ pip3 install boto3
```

Add your credentials in ~/.aws/credentials or have an AWS IAM Role configured for your computer.

You need to know the 3 parts of the bucket name.

A bucket name can be named, for example,

```
omg-agencies-shared-alteryx
```

### Installing

As of the moment, this script depends on cloning the `https://anmichelr@bitbucket.org/annalect/devops.git` repository
and executing from the `helper-scripts/aws` folder.



To clone and execute:

```bash
$ git clone https://anmichelr@bitbucket.org/annalect/devops.git
$ cd devops/helper-scripts/aws
$ ./create-bucket.py
```

The script will ask you the information needed. Just follow instructions...

```
Enter agency name (no spaces or special chars. allowed): omd
Enter client name (no spaces or special chars. allowed): shared
Enter project name (no spaces or special chars. allowed): alteryx

Review:
Bucket name: omd-shared-alteryx

Should I proceed to creation of bucket and policies? [y/N] (press P to review policies):
```


## Running the tests

No tests available when writing this doc.

## Built With

* Python3
* Boto3

## Contributing

The helper script are meant to be used and updated to help automate repetitive DevOps activities.

Feel free to make your branch of the project and contribute improvements. 

## Authors

* **An Michel Rodriguez** (anmichel.rodriguez@annalect.com / anmichel.rodriguez@gmail.com)


## Acknowledgments

* Shashikant Kuwar for initial inspiration for this script.


# 2) Create Policies (create-policies.py)

You want to use this script if the bucket already exists, but access has to be granted to a path inside the bucket.


### Prerequisites

The script is made for Python 3.

The script make use of the `boto3` library. You can install this library with
 
```bash
$ pip3 install boto3
```

Add your credentials in ~/.aws/credentials or have an AWS IAM Role configured for your computer.

You need to know the bucket name and the path inside the bucket where access is needed.

A path name can be named, for example,

```
PHD/Honda/activity_modified
```

which is in the bucket named `omg-agencies`

### Installing

As of the moment, this script depends on cloning the `https://anmichelr@bitbucket.org/annalect/devops.git` repository
and executing from the `helper-scripts/aws-s3` folder.

To clone and execute:

```bash
$ git clone https://anmichelr@bitbucket.org/annalect/devops.git
$ cd devops/helper-scripts/aws-s3
$ ./create-policies.py
```

The script will ask you the information needed. Just follow instructions...

```
Enter "bucket_name" (no spaces or special chars. allowed): omg-agencies
Enter "directory" (path/to/folder) (no spaces or special chars. allowed): PHD/Honda/activity_modified
```

## Running the tests

No tests available when writing this doc.

## Built With

* Python3
* Boto3

## Contributing

The helper script are meant to be used and updated to help automate repetitive DevOps activities.

Feel free to make your branch of the project and contribute improvements. 

## Authors

* **An Michel Rodriguez** (anmichel.rodriguez@annalect.com / anmichel.rodriguez@gmail.com)


## Acknowledgments

* Shashikant Kuwar for initial inspiration for this script.


