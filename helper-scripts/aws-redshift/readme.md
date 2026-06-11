# Helper Scripts - AWS-REDSHIFT
(newest info reading the readme.md docs in the repository/folder)

# Preface

This document provides documentation for the scripts

1) redshift-helper.py

# 1) Redshift Helper (redshift-helper.py)

This script helps with 
*) Adding users to groups
*) Creating schemas in a database
*) Reset DEFAULT PRIVILEGES for users
*) Execute ad-hoc one time queries 

## Getting Started

This script was first developed to automate repetitive tasks in the above mentioned activities.

Many tickets are created to 'grant access privileges to users', or 'create a new schems', and these are all requests very alike, only changing placeholders like 'username', 'schema name', etc...

It is important to realize that this script is not in any final stage, not it should ever be. It is the DevOps team responsability to keep updating and improving it, to help us automate repetitive activities.

### Prerequisites

* The script is made for Python 3.
* Install dependencies
* You need to have a `configuration file`. A sample format included in the repository. For example:
```
redshift_endpoints = [
    {
        'name': 'jumpshot',
        'host': 'jumpshot-clickstream.clf6bikxcquu.us-east-1.redshift.amazonaws.com',
        'dbname': 'dt',
        'username': 'username',
        'password': 'password'
    }
]
```

IMPORTANT: ** THIS FILE SHOULD ***NOT*** BE SOURCE-CONTROLLED IN GIT, AS IT CONTAINS PASSWORDS **


This file should be renamed from `redshift_conf.sample.py` to `redshift_conf.py`. This file is imported by this redshift helper and is used to 


### Installing

As of the moment, this script depends on cloning the `https://anmichelr@bitbucket.org/annalect/devops.git` repository
and executing from the `helper-scripts/aws` folder.


To clone and execute:

```bash
$ git clone https://anmichelr@bitbucket.org/annalect/devops.git
$ cd devops/helper-scripts/aws-redshift
$ ./redshift_helper.py
```

## Usage
On execution, the helper presents the possible configured connection. This connections are the ones configured in `redshift_conf.py`.

For example:
```bash
$ ./redshift_helper.py
0) jumpshot (jumpshot-clickstream.clf6bikxcquu.us-east-1.redshift.amazonaws.com)
1) dsdk (dsdk-v0p1-annalect.clf6bikxcquu.us-east-1.redshift.amazonaws.com)
2) ade stg pathmatic (adestg.clf6bikxcquu.us-east-1.redshift.amazonaws.com)
3) shared omd (shared-omd.clf6bikxcquu.us-east-1.redshift.amazonaws.com)
4) omd-statefarm-aip (omd-statefarm-aip.clf6bikxcquu.us-east-1.redshift.amazonaws.com)
5) omd-intel-alteryx (omd-intel-alteryx.clf6bikxcquu.us-east-1.redshift.amazonaws.com)
6) statefarmhd1 (statefarmhd1.clf6bikxcquu.us-east-1.redshift.amazonaws.com)
7) rm-aip (annalect-rm-aip.clf6bikxcquu.us-east-1.redshift.amazonaws.com)
8) gatorade (annalect-gatorade-aip.clf6bikxcquu.us-east-1.redshift.amazonaws.com)
9) pg-alteryx (annalect-pg-alteryx.clf6bikxcquu.us-east-1.redshift.amazonaws.com)
what configuration you want to use?
```
The connections are identified with a number, so you input a number and press Enter to continue.

After selecting a connection, a set of options are given:
```bash
what configuration you want to use?0
User complete name,
  enter `q` to input a custom query to the connection
  enter `d` to generate DEFAULT PRIVILEGES queries
  enter `r` to reset privileges in all tables in schema for groups
  enter `s` to CREATE SCHEMA
>
```

We will first explore how to grant access to a schema for a user..

### Granting access to a schema for a user

If we want to grant access to a user named John Briscoe, it is recommended to for example input some letter of the name. Doing this acts like a search to see if a similaly named user already exists.

After typing `jo b` the system presents the users that meet the combinations of those strings. Namely, `jo%`, `jo%b%`, so the user can choose with a number the username to work with.

An example of the usefulness of this is for example a user named Junz Hang. If we input `ju h`, the system presents a list of possible users, namely 
```bash
---------- Names with `j%`------------
0) jakecooper
...
21) jthomson
22) juan_zarco
23) junzhang


---------- Names with `j%z%`------------
24) jason_zhang
25) javier_chavez
26) jing_zhu
27) joy_mckenzie
28) juan_zarco
29) junzhang
``` 

Here you can see that it is not necessary to create junz_hang, because the user 23 or 29 (the correspond to the same username, with the identification number in each list) already exists.

We now have the option to either select a number to pick a user to work with, or to enter a new user name.

For example, if we want to work with Jing Zhu (jing_zhu) we input the number `26` in the prompt. On the other hand, if want to create a new user, we can input here the new user name, for example test_user. Pressing Enter will let us input again a search pattern.

After selecting a number, or input the username, we are presented with a list of groups we can add the user to.

```bash
Choose username (enter to search again): test_user
User `test_user`, id `create new user` selected


---------- All Groups in `jumpshot`------------
0) audience_builder_ro
1) audience_builder_rw
2) data_science_ro
3) data_science_rw
4) environics_ro
5) environics_rw
6) journey_ro
7) journey_rw
8) jumpshot_analytic
9) jumpshot_au_read_only
10) jumpshot_emea_read_only
11) jumpshot_read_only
12) training_read_only
13) training_read_write


---------- User group of `` in `test_user`------------
Choose a group to add user. (you can include many groups separated by `,` i.e. 1,2,6,8:
```

We can select one or more groups. To add a user to training_read_write and journey_rw we type `7`

Now the helper asks if we want to set DEFAULT PRIVILEGES for the user in a schema. Since we selected two read-write groups, we should select `y` in this question.

After choosing `y` we are presented with a list of schemas where to set the default privileges. The schema we choose is related to the group we chose previuosly.

```bash
Choose a schema for the Default Privileges (y/N) (will continue asking if `y`)?y
0) admin
1) audience_builder
2) data_science
3) environics
4) information_schema
5) journey
6) jumpshot_au
7) jumpshot_ca
8) jumpshot_de
9) jumpshot_mx
10) jumpshot_nl
11) jumpshot_nz
12) jumpshot_uk
13) jumpshot_us
14) public
15) spectrum_jumpshot
16) training
17) util
Choose a schema for the Default Privileges:
```

In this case, we choose first `5` to select the `journey` schema.

The helper presents options to select which are the corresponding RO and then RW groups.

```
---------- All Groups in `jumpshot`------------
0) audience_builder_ro
1) audience_builder_rw
2) data_science_ro
3) data_science_rw
4) environics_ro
5) environics_rw
6) journey_ro
7) journey_rw
8) jumpshot_analytic
9) jumpshot_au_read_only
10) jumpshot_emea_read_only
11) jumpshot_read_only
12) training_read_only
13) training_read_write
Please specify RO GROUP for schema `journey`: 6
Using `journey_ro` as RO group


---------- All Groups in `jumpshot`------------
0) audience_builder_ro
1) audience_builder_rw
2) data_science_ro
3) data_science_rw
4) environics_ro
5) environics_rw
6) journey_ro
7) journey_rw
8) jumpshot_analytic
9) jumpshot_au_read_only
10) jumpshot_emea_read_only
11) jumpshot_read_only
12) training_read_only
13) training_read_write
Please specify RW GROUP for schema `journey`: 7
Using `journey_rw` as RW group
``` 

The rest is following on screen instructions.

At the end it shows the queries to be executes:
```
---Queries to execute:
CREATE USER test_user  WITH PASSWORD 'V3CFyHg9ceMX6tQ';
ALTER GROUP journey_rw ADD USER test_user
ALTER DEFAULT PRIVILEGES FOR USER test_user in SCHEMA journey GRANT SELECT ON tables TO GROUP journey_ro;
ALTER DEFAULT PRIVILEGES FOR USER test_user in SCHEMA journey GRANT ALL ON tables TO GROUP journey_rw;
Execute queries? [Y/n]
```

After executing the queries, it presents with TICKET COMMENTS text, that can be copied and used at will.

### Other options

The script also presents the options to create schemas, execute queries or reset privileges. This are straight forwars and easily done following on screen instructions.


## Running the tests

No tests available when writing this doc.

## Built With

* Python3
* psycopg2

This helper uses the library
`devops/helper-scripts/lib/helper_functions`

## Contributing

The helper script are meant to be used and updated to help automate repetitive DevOps activities.

Feel free to make your branch of the project and contribute improvements. 

## Authors

* **An Michel Rodriguez** (anmichel.rodriguez@annalect.com / anmichel.rodriguez@gmail.com)


## Acknowledgments

* Shashikant Kuwar for initial inspiration for this script.

