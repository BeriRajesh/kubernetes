# Helper Scripts - Datadog
(newest info reading the readme.md docs in the repository/folder)

# Preface

This document provides documentation for the scripts

1) create_monitors.py

# 1) Create monitors (create_monitors.py)

This script uses the Datadog API to create the monitors in Datadog. 

It is useful as it creates/updates/deletes the monitors from a source controlled script, as opposed to doing changes in Datadog's GUI.

It also allows the creation of the same alarm contents for different environments or processes.

All alarms created by the script have the 'adt-script' tag, so to differentiate them from monitors created by a human person in the GUI

The monitor created monitors that includes but is not limited to
	
	* RDS CPU Utilization
	* EC2 CPU Utilization
	* Space free
	* Memory free
	* Process monitoring (this goes hand-in-hand with the playbook that install the process monitoring based on the AWS ServiceGroup tag)

## Getting Started

This script was first developed to automate the creation of monitors for our AWS infrastructure, using the Datadog API.

### Prerequisites

* The script is made for Python 3.
* Install dependencies (Datadog python module)
* The script takes the Datadog API Key from a system's environment variable. For that purpose, it is convenient to have a file like `setenv` with contents similar to, which can be `sourced` to set necessary environment variables

A `setenv` file contents: 

```setenv
export DD_API_KEY="849a0e8a2xxxxxxxxxxxx12095359415b"
export DD_APP_KEY="13e629facxxxxxxxxx9dcf88420377dff98"
```

can be used

```
$ source setenv
```



IMPORTANT: ** THIS FILE SHOULD ***NOT*** BE SOURCE-CONTROLLED IN GIT, AS IT CONTAINS PASSWORDS **


This file should be renamed from `redshift_conf.sample.py` to `redshift_conf.py`. This file is imported by this redshift helper and is used to 


### Installing

As of the moment, this script depends on cloning the `https://anmichelr@bitbucket.org/annalect/devops.git` repository
and executing from the `helper-scripts/aws` folder.


To clone and execute:

```bash
$ git clone https://anmichelr@bitbucket.org/annalect/devops.git
$ cd devops/helper-scripts/datadog
$ ./create_monitors.py
```

## Usage

```
$ source setenv
$ ./create_monitors.py
```

## Running the tests

No tests available when writing this doc.

## Built With

* Python3
* Datadog API python module

## Contributing

The helper script are meant to be used and updated to help automate repetitive DevOps activities.

Feel free to make your branch of the project and contribute improvements. 

## Authors

* **An Michel Rodriguez** (anmichel.rodriguez@annalect.com / anmichel.rodriguez@gmail.com)


## Acknowledgments

* Shashikant Kuwar for initial inspiration for this script.

