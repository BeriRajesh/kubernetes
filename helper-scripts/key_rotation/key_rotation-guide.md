# Key Rotation guide

We need to look for AWS IAM keys in
It's best if all color output is disable both in `grep` command and `ansible`.

1. ADE: ade_connection in all environmments
2. AB database in all environmments
3. serveroverride.cfg files
4. serverbase.cfg files
5. search keys in all the develop code
6. search keys in all EC2 server
7. search database hosts

Once the keys have been identified, we can do a manual replacement or create a script to handle the creation of the new keys. The script should output a file with contents: old key -> new key, new secret

The replacement of the keys depends on the location of the keys:

1. Database keys:
   1. These can be replaced with a python script.
2. Serverbase/Override keys
   1. These most likely can be replaced with a python script, since the location of the Key and Secret can be identified.
3. Keys in general python files (majority of keys):
   1. This can be tricky since the secret in general is unknown, and thus it is difficult to identify where is the secret located.

The easiest way is to pressure development teams to use roles whenever possible.ß

## 1. ADE: ade_connection in all environmments

Connect to each host:
anlctdev-e1-mysql-001.c488xyottj77.us-east-1.rds.amazonaws.com
anlctqa-e1-mysql-001.c488xyottj77.us-east-1.rds.amazonaws.com
anlctmgmt-e1-mysql-001.c488xyottj77.us-east-1.rds.amazonaws.com
anlctprod-e1-mysql-001.c488xyottj77.us-east-1.rds.amazonaws.com


Identify the AWS IAM keys by running the query in the corresponding ADE schema:
`select account_name from ade_connection where account_name <> '' and platform = 's3';`

## 2. AB: abdb.ab_connection in all environmments
Connect to each host:
audiencebuilder-dev.cluster-c488xyottj77.us-east-1.rds.amazonaws.com
audiencebuilder-prod.cluster-c488xyottj77.us-east-1.rds.amazonaws.com
audiencebuilder-qa.cluster-c488xyottj77.us-east-1.rds.amazonaws.com
audiencebuilder-stg.cluster-c488xyottj77.us-east-1.rds.amazonaws.com


Identify the AWS IAM keys by running the query in the corresponding ADE schema:
`select account_name from abdb.ab_connection where account_name <> '' and platform = 's3';`

## 3. serveroverride.cfg files
You can download all serveroverride files with by using the script
```
devops/helper-scripts/aws-ecs (release)
$ python3 download-secrets.py
```

The override files get downloaded to the secrets/ directory. There you can perform a regex search:

```
devops/helper-scripts/aws-ecs/secrets (anm-develop)
$ find . -exec grep -H -E "[A-Z0-9]{20}" {} \;

omniui-dev-serveroverride.cfg
12:aws_access_key_id = AKIAIIF4NROLFL6ALG2Q

b2bcontent-dev-serveroverride.cfg
38:token_encryption_key = B7ORUJX3B4OUU79KJS8UOI7CASRMN5YT

omnibrief-dev-serveroverride.cfg
34:aws_access_key_id = AKIAJOWAIX4X25SLFC2Q
...
```

## 4. serverbase.cfg files
This has to be done from Bamboo server.

Scriptname: devops/helper-scripts/key_rotation/checkout-repos.py

From the script's docs:
```
Sample usage:
    1- Log in to Bamboo server
    2- Go to `$ cd /backup/bitbucket-backup`
    3- Verify that the latest version of this script is in that path
    4- Run: `$ python3.6 checkout-repos.py`

    Note: Check out the configuration variables at the beginning of script
```

For example:
```
/backup/bitbucket-backup/checkedout-repos$ find . -name *.cfg -type f -exec grep -HT -E "\b[A-Z][A-Z0-9]{19}\b" {} \; | sed -r 's/([^:]*)(.*)\b([A-Z][A-Z0-9]{19})\b(.*)/\3\t\1/g' > keys-cfg

```

## 5. search keys in all the develop code

Using the checkout repos from the previous section, we can also search in all of the code of python files:

```
find . -name *.py -type f -exec grep -HT -E "\b[A-Z][A-Z0-9]{19}\b" {} \; | sed -r 's/([^:]*)(.*)\b([A-Z][A-Z0-9]{19})\b(.*)/\3\t\1/g' > keys-py
```

## 6. search keys in all EC2 server
We can search in all linux EC2 using ansible, for all environments

Execute this command for every directory: /home and /var/www by doing

```
$ cd devops/helper-scripts/ansible-playbooks
for env in Dev QA MGMT Prod; do ./select_hosts.py -e $env --become --command 'find /home -type f -size -100k -not -path "*.ansible*" -exec grep -HT -E "\b[A-Z][A-Z0-9]{19}\b" {} \;' | sed -E 's/([^:]*)(.*)\b([A-Z][A-Z0-9]{19})\b(.*)/\3\t\1/g' | tee -a keys-ansible; done
```

Remember to execute also for /var/www by substituting in the above command /home -> /var/www

The file generated with this command, can be further processed and formatted to a more convenient, excel-friendly, csv file.

Execute for example

```
$ cd devops/helper-scripts/ansible-playbooks
$ python3 reformat-ansible-key-files.py -f keys-ansible-var-www
```

## 7. search database hosts

We can adapt our regex and do a similar search using Ansible.

Regex:
```
"\b(.*)\.us-east-1\.rds\.amazonaws\.com\b"
```

So we wrap it again with the for..loop to search all environments:
```
$ cd devops/helper-scripts/ansible-playbooks
$ for env in Dev QA MGMT Prod; \
    do \
        ./select_hosts.py -e $env --become --command 'find /home -type f -size -100k -not -path "*.ansible*" -name "*.py" -o -name "*.cfg" \
            -exec grep -HT -E "\b(.*)\.us-east-1\.rds\.amazonaws\.com\b" {} \;' | \
            sed -E 's/(.*)\t(.*\.us-east-1\.rds\.amazonaws\.com)\b/\2\t\1\t\2/g' | \
            tee -a hosts-ansible-home; \
    done
```