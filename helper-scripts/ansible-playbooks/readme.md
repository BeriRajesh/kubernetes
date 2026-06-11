# Helper Scripts - ANSIBLE-PLAYBOOOKS
(newest info reading the readme.md docs in the repository/folder)

## Prerequisites

1. Install and configure Ansible2.5+. Docs: https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#latest-releases-via-apt-ubuntu
2. We use dynamic inventories (EC2). This enables to select hosts on AWS by using our DevOps tags, and more. Please be familiar with the concept. Docs: https://docs.ansible.com/ansible/latest/user_guide/intro_dynamic_inventory.html#inventory-script-example-aws-ec2
3. Configure the ssh acccess keys. You need to specify the path pointing to the location of the ssh keys.
    The connection to the servers is manager using the AWS Tag called `Environment`. So you must set up your hosts inventories like:

For US hosts:
```
$ cat hosts-us/group_vars/tag_Environment_*
---
ansible_user: ubuntu
ansible_ssh_private_key_file: ~/keys/anlct-dev-key.pem
---
ansible_user: ubuntu
ansible_ssh_private_key_file: ~/keys/anlct-mgmt-key.pem
---
ansible_user: ubuntu
ansible_ssh_private_key_file: ~/keys/anlct-prod-key.pem
---
ansible_user: ubuntu
ansible_ssh_private_key_file: ~/keys/anlct-qa-key.pem
```

For EU hosts:
```
cat hosts-eu/group_vars/tag_Environment_*
---
ansible_user: ubuntu
ansible_ssh_private_key_file: ~/keys/anlcteu-dev-key.pem
---
ansible_user: ubuntu
ansible_ssh_private_key_file: ~/keys/anlcteu-mgmt-key.pem
---
ansible_user: ubuntu
ansible_ssh_private_key_file: ~/keys/anlcteu-prod-key.pem
```

You can test that the access keys are working by running trying to obtain the dynamic list of servers from the hosts script. Be sure that the script has the execute permissions (`chmod +x ./hosts-us/hosts`)
```
./hosts-us/hosts --list
```

At this point, you should be able to run Ansible against ANY of our Linux EC2 servers. For example:
```
$ ansible -i hosts-us/hosts 10.5.228.189 -m shell -a 'ls'
```

3. To make it easier, you can default to the US configuration by running:
```
$ sudo ln -s /path/to/devops/helper-scripts/ansible-playbooks/hosts-us /etc/ansible
```


At this point, you should be able to run Ansible against ANY of our Linux EC2 servers. For example:
```
$ ansible 10.5.228.189 -m shell -a 'ls'
```


## Getting Started

Your ssh access keys need to be placed in the `keys/` subdirectory (or create a symbolic link to your actual location). If the keys don't have the standard names, you can configure them in `hosts-[us|eu]/group_vars/tag_Environment_[Dev|MGMT|Prod|QA].yml` files.

The hosts configurations is expected to be in the default location: `hosts-[us|eu]/hosts`.


# Preface

This document provides documentation for the scripts

- Select hosts:
    - select_hosts.py
- Linux patching
    - patching_with_script.yml
    - patch-dev.yml
    - patch-qa.yml
    - patch-prod.yml
    - patch-mgmt.yml
- Wordpress:
    -  wordpress-update.yml
- Infrastructure reporting:
    - reports.yml
- Install datadog agent with process monitoring:
    - datadog-agent-install.yml

This notebooks use the dynamic inventories script for AWS.

All these notebook depends on public keys saved to the keys/ folder, that is usually a symbolic link to the real location of this keys. The configuration of the usage of this keys is in `hosts-[us|eu]/group_vars` where there are files identified by the dynamic inventory tag: `hosts-[us|eu]/group_vars/tag_Environment_[Dev|QA|Prod|QA].yml`.

# Select hosts (select_hosts.py)

### Pro-tip

You can make this script an executable by doing a symbolic link in your /usr/bin/local
```
$ sudo ln -s /your/path/to/select_hosts.py /usr/local/bin/h
```

Now you can invoke this script just by issuing `h` command. For example:

```
$ h
usage: h [-h] [-a APPLICATION] [-b] [-c COMMAND] [-e {Dev,QA,MGMT,Prod}]
         [-d DEBUG] [-i {us,eu}] [-l LAYER] [-p PLATFORM] [-s SERVICE_GROUP]
         [-t TOWER] [-T TAG TAG]]
```


### Preface

This utility script was made to ease the selection of IPs of servers of the infrastructure, based on `AWS tags`, and `Ansible`'s dynamic inventories.

Importantly, this script provides the ability to execute any Ansible playbook (option `-P`) to the selected hosts, taking care of all necessary variables and options.

Please review the help (option --help) to see all available options.


### Installing

Clone the repository.

### How to run

When running without options, the help is shown:

```
$ h -h
usage: h [-h] [-a APPLICATION] [-b] [-c COMMAND] [-e {Dev,QA,MGMT,Prod}]
         [-v DEBUG_VARIABLE] [-d] [-g] [-i {us,eu}] [-I IP] [-l LAYER]
         [-N NAME] [-p PLATFORM] [-P PLAYBOOK]
         [-s {all,analysis,general,dsdk,wellsfargo,utility,mongodb,bamboo,samba,openswan,apache,mesos_master,mesos_slave}]
         [-t TOWER] [-T TAG TAG] [-z AVAILABILITY_ZONE] [-u] [-n] [-o] [-y]

Helps showing IPs of hosts filtering by AWS tags, optionally also executing a
command in each host

optional arguments:
  -h, --help            show this help message and exit
  -a APPLICATION, --application APPLICATION
                        Application where hosts belong
  -b, --become          Execute command (if any) as root
  -c COMMAND, --command COMMAND
                        Command to execute on host
  -e {Dev,QA,MGMT,Prod}, --environment {Dev,QA,MGMT,Prod}
                        Environment where hosts belong
  -v DEBUG_VARIABLE, --debug-variable DEBUG_VARIABLE
                        Useful to show the value of a tag. Ex. -d ec2_id. For
                        a full list of available tags and variables, please
                        refer to http://docs.ansible.com/ansible/latest/user_g
                        uide/intro_dynamic_inventory.html#example-aws-
                        ec2-external-inventory-script
  -d, --debug-command   Show parse command and exit
  -g, --debug-options   Show raw value of parsed options
  -i {us,eu}, --inventory {us,eu}
                        Inventory (group of hosts) to use, forces refresh
  -I IP, --ip IP        Select the host with this IP address
  -l LAYER, --layer LAYER
                        Layer where hosts belong
  -N NAME, --name NAME  Filter by tag Name
  -p PLATFORM, --platform PLATFORM
                        OS platform
  -P PLAYBOOK, --playbook PLAYBOOK
                        Run playbook to selected hosts
  -s {all,analysis,general,dsdk,wellsfargo,utility,mongodb,bamboo,samba,openswan,apache,mesos_master,mesos_slave}, --service-group {all,analysis,general,dsdk,wellsfargo,utility,mongodb,bamboo,samba,openswan,apache,mesos_master,mesos_slave}
                        Service group where hosts belong
  -t TOWER, --tower TOWER
                        Tower where hosts belong
  -T TAG TAG, --tag TAG TAG
                        Specify custom tag and value. Ex. -T Name Util*
  -z AVAILABILITY_ZONE, --availability-zone AVAILABILITY_ZONE
                        Availability zone of host
  -u, --upgrade-distribution
                        Does a dist-upgrade on instance
  -n, --dry-run         Does a distupgrade on instance
  -o, --unhold          Unhold packages before doing dist-upgrade (kernel and
                        mesos)
  -y, --yes             Assumes yes to all yes/no questions

```

### Examples
The usage is very straightforward

- To show IPs of hosts in the Environment `Dev`, for the Application `ade` Layer `ingest` you can do:

```
$ ./select_hosts.py -e Dev -a ade -l ingest
Default to US hosts inventory

  hosts (1):
    10.5.227.168

Command (**unquoted**) was: /Library/Frameworks/Python.framework/Versions/2.7/bin/ansible --list-hosts !platform_windows:&tag_Application_ade:&tag_Environment_Dev:&tag_Layer_ingest -i ./hosts-us/hosts

(took 3.22s)
```

- To see the latest commit in the ade folder, we might do somthing like

```
$ ./select_hosts.py -e Prod -a ade -l ingest -c 'cd /var/www/ade && git log | head -n 1 || true'
Default to US hosts inventory

10.5.230.249 | SUCCESS | rc=0 >>
commit 68c30932a2051bacad08e433b5040bced6adc220

10.5.230.243 | SUCCESS | rc=0 >>
commit 68c30932a2051bacad08e433b5040bced6adc220

10.5.230.197 | SUCCESS | rc=0 >>
commit 68c30932a2051bacad08e433b5040bced6adc220

10.5.230.176 | SUCCESS | rc=0 >>
commit 68c30932a2051bacad08e433b5040bced6adc220

10.5.230.251 | SUCCESS | rc=0 >>
commit 68c30932a2051bacad08e433b5040bced6adc220

10.5.230.180 | SUCCESS | rc=0 >>
commit 68c30932a2051bacad08e433b5040bced6adc220

10.5.230.167 | SUCCESS | rc=0 >>
commit 68c30932a2051bacad08e433b5040bced6adc220

10.5.230.141 | SUCCESS | rc=0 >>
commit 68c30932a2051bacad08e433b5040bced6adc220

10.5.231.164 | SUCCESS | rc=0 >>
commit 68c30932a2051bacad08e433b5040bced6adc220

10.5.231.236 | SUCCESS | rc=0 >>
commit 68c30932a2051bacad08e433b5040bced6adc220


Command (**unquoted**) was: /Library/Frameworks/Python.framework/Versions/2.7/bin/ansible -m shell -a cd /var/www/ade && git log | head -n 1 || true !platform_windows:&tag_Application_ade:&tag_Environment_Prod:&tag_Layer_ingest -i ./hosts-us/hosts

(took 5.09s)
```

To execute playbook `reports.yml` in environment `MGMT`, assuming `yes` to all questions:

```
$ h -P reports.yml -e MGMT -y
```

(not providing `-y` option, would ask per every ServiceGroup. This is convenient for careful patching)


## Built With

* Ansible 2

## Contributing

These playbook are meant to be used and updated to help automate repetitive DevOps activities.

Feel free to make your branch of the project and contribute improvements.

## Authors

* **An Michel Rodriguez** (anmichel.rodriguez@annalect.com / anmichel.rodriguez@gmail.com)


## Acknowledgments

* Shashikant Kuwar for initial inspiration for this script.



# Linux patching

The easiest way to run the patching playbooks, is to use the wrapper script `patching.py`

## patching.py
This script is written in Python3.

On execution without options, it shows a condensed help:

```
$ ./patching.py
usage: patching.py [-h] [-e {Dev,QA,MGMT,Prod}]
                   [-s {all,general,analysis,wellsfargo,utility,mongodb,bamboo,samba,openvpn,openswan,apache,mesos-master,mesos-slave}]
                   [-i {us,eu}] [-u] [-n] [-o] [-y]
                   {list,patch}
patching.py: error: the following arguments are required: action
```

Using the `-h` or `--help` flags gives a better help:

```
$ ./patching.py --help
usage: patching.py [-h] [-e {Dev,QA,MGMT,Prod}]
                   [-s {all,general,analysis,wellsfargo,utility,mongodb,bamboo,samba,openvpn,openswan,apache,mesos-master,mesos-slave}]
                   [-i {us,eu}] [-u] [-n] [-o] [-y]
                   {list,patch}

Fires Ansible patching with the correct options

positional arguments:
  {list,patch}          action to perform

optional arguments:
  -h, --help            show this help message and exit
  -e {Dev,QA,MGMT,Prod}, --environment {Dev,QA,MGMT,Prod}
                        Environment to patch
  -s {all,general,analysis,wellsfargo,utility,mongodb,bamboo,samba,openvpn,openswan,apache,mesos-master,mesos-slave}, --service-group {all,general,analysis,wellsfargo,utility,mongodb,bamboo,samba,openvpn,openswan,apache,mesos-master,mesos-slave}
                        Service group to patch
  -i {us,eu}, --inventory {us,eu}
                        Inventory (group of hosts) to use
  -u, --upgrade-distribution
                        Does a dist-upgrade on instance
  -n, --dry-run         Does a distupgrade on instance
  -o, --unhold          Unhold packages before doing dist-upgrade (kernel and
                        mesos)
  -y, --yes             Assumes yes to all yes/no questions
```

This way all options and variables needed for the original `patch-env` playbooks are wrapped with this script that takes care of the filtering and passing of variables.

### Example

An example:
- If we want to patch the Dev environment, ServiceGroup `apache`, we can do:

```
$ ./patching.py patch -e Dev -s apache -u -o
The *unquoted* command is:
/Library/Frameworks/Python.framework/Versions/2.7/bin/ansible-playbook patch_with_script.yml -i hosts-us/hosts --limit=tag_Environment_Dev:&tag_ServiceGroup_apache -e {'mongodb_backup_done': True, 'upgrade_distribution': True, 'dry_run': False, 'unhold_packages': True, 'unhold_mesos_slave': True}
Patch ServiceGroup `apache` (Y/n)
...
```

The script takes care of setting the variables `-e {'mongodb_backup_done': True, 'upgrade_distribution': True, 'dry_run': False, 'unhold_packages': True, 'unhold_mesos_slave': True}`, which would otherwise be cumbersome to write.

It also takes care of the filtering, `--limit=tag_Environment_Dev:&tag_ServiceGroup_apache`

Conveniently it also shows the `Ansible` command that gets issued to the system, before actually issuing it.



## patch-[dev-qa-mgmt-prod].yml

The four playbooks to patch different environments are almost identical.

The main and only difference is the selection of hosts.

The playbooks include the `patching` role, which takes care of running all necessary tasks.

At the beginning of each play book, it is stated:

```
#
# To control if patching process (un)holds packages, this playbook can be run with the options:
#     $ ansible-playbook patch-qa.yml
#           [ -e upgrade_distribution=true|false ]
#           [ -e unhold_packages=true|false ] [ -e unhold_mesos_slave=yes|no ]
#           [ -e unhold_mesos_slave=true|false ]
#
# Packages are held by default
```

The general tasks performed by the patching role are:

    * Un-Hold packages if variable say so
    * Un-Hold mesos packages (in the appropriate instances) if variable say so
    * Do `dist-upgrade`
    * Restart the instance
    * Hold packages
    * Restart services appropriate for each instance, as specified in the ServiceGroup AWS tag. This is done by conditionally including other roles (like `apache` role, or `mongodb` role...)
    * Write a summary of the patching in /root in each instance

## Getting Started

Have your keys copied in the `keys` subdirectory.

The hosts are in the `hosts-[us|eu]/hosts` file. Before changing between US<->EU hosts, it is necessary to update the cache by doing for example

```$ host-us/host --refresh```

The `ansible.cfg` file  has some custom commented configuration.

### Prerequisites

Install and configure Ansible2.5+.


### Installing

Clone the repository.

### How to run

```bash
$ ansible-playbook -i hosts-us/hosts patch-[dev|prod|qa|mgmt].yml
```

Remember you can comment/uncomment more verbose output of the human_log callback, as described before.

To see other useful options, run

```bash
$ ansible-playbook --help
```

## Built With

* Ansible 2

## Contributing

These playbook are meant to be used and updated to help automate repetitive DevOps activities.

Feel free to make your branch of the project and contribute improvements.

## Authors

* **An Michel Rodriguez** (anmichel.rodriguez@annalect.com / anmichel.rodriguez@gmail.com)


## Acknowledgments

* Shashikant Kuwar for initial inspiration for this script.


# Wordpress

This playbook was made to automate the backup/upgrade process for wordpress sites.

The playbook can be use to upgrade wordpress sites, or to only do a backup. The backup is done by specifying the option `-e "{only_backup: True}"`.

The `only_backup` varible *has* to be specified, wither with a `True` or `False` value.

To accomplish these tasks, the playbook installs WP-CLI.

The playbook must be run with the `--tags` parameter, to specify which set of tasks are to be included.

## Getting Started

You need to copy your keys to a `keys/` subdirectory (or create a symbolic link). If the keys don't have the standard names, you can configure them in `hosts-[us|eu]/group_vars/tag_Environment_[Dev|MGMT|Prod|QA].yml` files.

The hosts are in the `hosts-[us|eu]/hosts` file. Before changing between US<->EU hosts, it is necessary to update the cache by doing for example

```$ host-us/host --refresh```

The `ansible.cfg` file  has some custom commented configuration.


### Prerequisites

Install and configure Ansible2.5+.


### Installing

Clone the repository.

### How to run

```bash
$ ansible-playbook -i hosts-us/hosts --tags=[dev|prod|deveu|prodeu] wordpress-update.yml
```

In general, this playbook performs these tasks:

    * Creates a management-user/management-group
    * Set permissions for the management-user so it can write files
    * Downloads and installs WP-CLI if necessary
    * Uses WP-CLI to make a dump of the database inside the wordpress folder
    * Compresses the database dump to a .gz
    * Compresses the Wordpress folder to a tar.gz
    * Uploads the .tar.gz to S3
    * If all these steps are successful
	    * Uses WP-CLI to update the minor versions of plugins, themes and core of wordpress
	    * Applies the wordpress-hardening script
	    * Deletes management user and group


The hardening script is specified in the playbook in the variable `post_upgrade_hardening_script_name`, and should be located in
```roles/wordpress_update/templates/```

Remember you can comment/uncomment more verbose output of the human_log callback, as described before.

To see other useful options, run

```bash
$ ansible-playbook --help
```

## Built With

* Ansible 2

## Contributing

These playbook are meant to be used and updated to help automate repetitive DevOps activities.

Feel free to make your branch of the project and contribute improvements.

## Authors

* **An Michel Rodriguez** (anmichel.rodriguez@annalect.com / anmichel.rodriguez@gmail.com)


## Acknowledgments

* Shashikant Kuwar for initial inspiration for this script.


# Infrastructure reporting

This playbook was made to automate the generation of a report that informs us the state of our infrastructure: operative system installed, kernel version, normal/critical updates pending, and many services checks on all the instances.

The playbook must can optionally be run with the `--tags` parameter, filter out which checks should be made to instances.

## Getting Started

You need to copy your keys to a `keys/` subdirectory (or create a symbolic link). If the keys don't have the standard names, you can configure them in `hosts-[us|eu]/group_vars/tag_Environment_[Dev|MGMT|Prod|QA].yml` files.

The hosts are in the `hosts-[us|eu]/hosts` file. Before changing between US<->EU hosts, it is necessary to update the cache by doing for example

```$ host-us/host --refresh```

The `ansible.cfg` file  has some custom commented configuration.

### Prerequisites

Install and configure Ansible2.5+.


### Installing

Clone the repository.

### How to run

```bash
$ ansible-playbook -i hosts-us/hosts --tags=TAGS reports.yml
```

Please run `$ ansible-playbook -i hosts-us/hosts reports.yml --list-tags` to see available values for TAGS.

After running the playbook, there should be .csv files generated for each host, and a `summary.csv` file for all hosts. This file can be opened in Excel, where you can divide the first column 'by a delimeter', the delimeter being a semicolon (";").

Remember you can comment/uncomment more verbose output of the human_log callback, as described before.

To see other useful options, run

```bash
$ ansible-playbook --help
```

## Built With

* Ansible 2

## Contributing

These playbook are meant to be used and updated to help automate repetitive DevOps activities.

Feel free to make your branch of the project and contribute improvements.

## Authors

* **An Michel Rodriguez** (anmichel.rodriguez@annalect.com / anmichel.rodriguez@gmail.com)


## Acknowledgments

* Shashikant Kuwar for initial inspiration for this script.


# Install datadog agent with process monitoring (datadog-agent-install.yml)

The playbook include the role `datadog.monitoring`, which takes care of running all necessary tasks to install and configure Datadog on the host in which the role is included. The role also configured process monitoring using the AWS tag `ServiceGroup`. This datadog.monitoring role uses the official `Datadog.datadog` role provided by Datadog and whose is [https://github.com/DataDog/ansible-datadog]()


## Getting Started

You ssh access keys need to be placed in the `keys/` subdirectory (or create a symbolic link to your actual location). If the keys don't have the standard names, you can configure them in `hosts-[us|eu]/group_vars/tag_Environment_[Dev|MGMT|Prod|QA].yml` files.

The hosts are in the `hosts-[us|eu]/hosts` file. Before changing between US<->EU hosts, it is necessary to update the cache by doing for example.

```$ host-us/host --refresh```

Since installing the agent and process monitoring in all of our infrastructure can be slow (+1h), it is recommended to use the `--limit=<your condition here>` option to filter the hosts picked to run the playbook. For example, to install/update only the process monitoring for the ServiceGroup `mesos-slave`, you can use `--limit=tag_ServiceGroup_mesos_slave`, or  `--limit=tag_Environment_Dev` to update all process monitoring only in environment `Dev`, or even filter by both `--limit=tag_Environment_Dev:&tag_ServiceGroup_mesos_slave`

The `ansible.cfg` file has some custom commented configuration.


### Prerequisites

Install and configure Ansible2.5+.


### Installing

Clone the repository.

### How to run

```bash
$ ansible-playbook -i hosts-us/hosts datadog-agent-install.yml --limit='tag_Environment_Dev'
```

Remember you can comment/uncomment more verbose output of the human_log callback, as described before.

To see other useful options, run

```bash
$ ansible-playbook --help
```

## Built With

* Ansible 2

## Contributing

These playbook are meant to be used and updated to help automate repetitive DevOps activities.

Feel free to make your branch of the project and contribute improvements.

## Authors

* **An Michel Rodriguez** (anmichel.rodriguez@annalect.com / anmichel.rodriguez@gmail.com)


## Acknowledgments

* Shashikant Kuwar for initial inspiration for this script.

