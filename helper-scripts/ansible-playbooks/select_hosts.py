#!/usr/bin/env python3

"""
Helper script that uses Ansible to show the IP's of selected hosts
"""
import argparse
import os
import subprocess
import sys
import time


def get_args():
    parser = argparse.ArgumentParser(
        description='Helps showing IPs of hosts filtering by AWS tags, optionally also executing a command in each host')
    # parser.add_argument("action", choices=['list', 'patch'],
    #                     help="action to perform")
    # parser.add_argument("-v", "--verbose", default=0,
    #                     help="increase output verbosity", actions='count')
    parser.add_argument("-a", "--application",
                        help="Application where hosts belong")
    parser.add_argument("-A", "--ask-vault-pass", action="store_true",
                        help="Passes parameter to Ansible. Only meaningful when used with -P")
    parser.add_argument("-b", "--become", action='store_true',
                        help="Execute command (if any) as root")
    parser.add_argument("-c", "--command",
                        help="Command to execute on host")
    parser.add_argument("-e", "--environment", choices=['Dev', 'QA', 'MGMT', 'Prod'],
                        help="Environment where hosts belong")
    parser.add_argument("-v", "--debug-variable",
                        help="Useful to show the value of a tag. Ex. -d ec2_id. For a full list of available tags and "
                             "variables, please refer to http://docs.ansible.com/ansible/latest/user_guide/"
                             "intro_dynamic_inventory.html#example-aws-ec2-external-inventory-script")
    parser.add_argument("-d", "--debug-command", action='store_true',
                        help="Show parse command and exit")
    parser.add_argument("-g", "--debug-options", action='store_true',
                        help="Show raw value of parsed options")
    parser.add_argument("-i", "--inventory", choices=["us", "eu"],
                        help="Inventory (group of hosts) to use, forces refresh")
    parser.add_argument("-I", "--ip",
                        help="Select the host with this IP address")
    parser.add_argument("-l", "--layer",
                        help="Layer where hosts belong")
    parser.add_argument("-N", "--name",
                        help="Filter by tag Name")
    parser.add_argument("-p", "--platform",
                        help="OS platform")
    parser.add_argument("-P", "--playbook",
                        help="Run playbook to selected hosts")
    parser.add_argument("-s", "--service-group", choices=service_group_list,
                        help="Service group where hosts belong")
    parser.add_argument("-t", "--tower",
                        help="Tower where hosts belong")
    parser.add_argument("-T", "--tag", nargs=2,
                        help="Specify custom tag and value. Ex. -T Name Util*")
    parser.add_argument("-z", "--availability-zone",
                        help="Availability zone of host")

    parser.add_argument("-u", "--upgrade-distribution", action='store_true',
                        help="Does a dist-upgrade on instance. "
                             "Only meaningful when used with -P and a patching playbook.")

    parser.add_argument("-n", "--dry-run", action='store_true',
                        help="Does a distupgrade on instance. "
                             "Only meaningful when used with -P and a patching playbook.")

    parser.add_argument("-o", "--unhold", action='store_true',
                        help="Unhold packages before doing dist-upgrade (kernel and mesos). "
                             "Only meaningful when used with -P and a patching playbook.")

    parser.add_argument("-y", "--yes", action='store_true',
                        help="Assumes yes to all yes/no questions. Only meaningful when used with -P.")

    parser.add_argument("--list-hosts", action='store_true',
                        help="Adds --list-hosts options. Only meaningful when used with -P.")

    parser.add_argument("--tags",
                        help="Value specified here is passed verbatim to '--tags- in Ansible.")

    parser.add_argument("--minimum-output", action='store_true',
                        help="Only output Ansible's output.")

    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.parse_args(['--help'])
        # parser.error('No arguments provided.')

    if args.debug_options:
        print(args)
        sys.exit()

    return args


def parse_command(args):
    if args.command is not None:
        option_list.extend("-m", "shell", "-a", args.command)


def parse_args_hosts(args):
    hosts = ['!platform_windows']
    arg_dict = vars(args)
    for option in arg_dict:
        if arg_dict[option] is None:
            continue
        # print(option)
        # print(arg_dict[option])

        prefix = "&"
        if type(arg_dict[option]) is str and len(arg_dict[option]) > 0 and arg_dict[option][0] == "!":
            arg_dict[option] = arg_dict[option][1:]
            prefix = "!"
        if option == "application":
            hosts.append(prefix + "tag_Application_{}".format(arg_dict[option]))
        elif option == "environment":
            hosts.append(prefix + "tag_Environment_{}".format(arg_dict[option]))
        elif option == "ip":
            hosts.append(prefix + "{}".format(arg_dict[option]))
        elif option == "layer":
            hosts.append(prefix + "tag_Layer_{}".format(arg_dict[option]))
        elif option == "name":
            hosts.append(prefix + "tag_Name_{}".format(arg_dict[option]))
        elif option == "service_group" and args.playbook is None:
            hosts.append(prefix + "tag_ServiceGroup_{}".format(arg_dict[option]))
        elif option == "tower":
            hosts.append(prefix + "tag_tower_{}".format(arg_dict[option]))
        elif option == "tag":
            hosts.append(prefix + "tag_{}_{}".format(arg_dict[option][0], arg_dict[option][1]))
        elif option == "availability_zone":
            hosts.append(prefix + "{}".format(arg_dict[option]))

    if 'platform' not in arg_dict:
        hosts.append('!platform_windows')
    elif arg_dict['platform'] is not None:
        prefix = "&"
        if arg_dict['platform'][0] == "!":
            arg_dict['platform'] = arg_dict['platform'][1:]
            prefix = "!"
        hosts.append(prefix + "platform_".format(arg_dict[option]))

    if hosts[0][0] == '&':
        hosts[0] = hosts[0][1:]

    return ":".join(hosts)


def parse_args_commands(args):
    command = ["all"]

    if "playbook" in vars(args) and args.playbook is not None:
        command = []
        command.extend([args.playbook])
    elif "command" in vars(args) and args.command is not None:
        command.extend(["-m", "shell", "-a", "'" + args.command + "'"])
    elif "debug_variable" in vars(args) and args.debug_variable is not None:
        command.extend(["-m", "debug", "-a", "var="+args.debug_variable])

    if command == ["all"] or args.list_hosts:
        command.extend(["--list-hosts"])

    if "become" in vars(args) and args.become:
        command.extend(["--become"])

    if "ask_vault_pass" in vars(args) and args.ask_vault_pass:
        command.extend(["--ask-vault-pass"])

    return command


# todo: have a single source-of-truth for service_groups_list, and avoid hardcoding the list here
service_group_list = ["analysis", "general", "dsdk", "wellsfargo", "utility", "mongodb", "bamboo", "samba",
                      "openswan", "apache", "mesos_master", "mesos_slave"]

if __name__ == '__main__':
    abs_path = os.path.dirname(os.path.realpath(__file__))
    if abs_path == os.getcwd():
        abs_path = "."
    else:
        os.environ['ANSIBLE_CONFIG'] = abs_path

    start_time = time.time()

    option_list = []

    args = get_args()
    hosts_str = parse_args_hosts(args)
    command_list = parse_args_commands(args)

    executing_playbook = "playbook" in vars(args) and args.playbook is not None

    if args.inventory is not None:
        if not args.minimum_output:
            print('Using `{}` hosts inventory. Refreshing inventory...'.format(args.inventory))
        cmd = "{}/hosts-{}/hosts --refresh".format(abs_path, args.inventory)
        if args.debug_command:
            print(cmd)
        else:
            out = subprocess.check_output(cmd, shell=True)
            if not args.minimum_output:
                print("Inventory refreshed...")
        inventory = "{}/hosts-{}/hosts".format(abs_path, args.inventory)
    else:
        if not args.minimum_output:
            print('Default to US hosts inventory')
        inventory = "{}/hosts-us/hosts".format(abs_path)

    if args.yes or args.playbook is None:
        service_groups = ['']
    else:
        if args.service_group is None:
            service_groups = service_group_list
        else:
            service_groups = [args.service_group]

    # sys.exit(hosts_str)

    variables = {"running_with_script": True}


    # sys.exit(service_groups)
    # print(args.yes)
    # sys.exit(args.yes)

    if executing_playbook:
        if args.availability_zone is None:
            if input("You are applying a playbook without specifying an availability zone. "
                     "Do you want to continue this way? y/N") != "y":
                sys.exit("Please specify an availability zone and restart the script.")

    for sg in service_groups:
        hosts_str_cycle = hosts_str

        if not args.yes and executing_playbook:
            hosts_str_cycle = hosts_str + ':&tag_ServiceGroup_' + sg

        tags = ""
        if executing_playbook:
            variables.update({"ansible_python_interpreter": "/usr/bin/python2.7"})
            variables.update({"mongodb_backup_done": True})
            variables.update({"upgrade_distribution": args.upgrade_distribution})
            variables.update({"only_backup": not args.upgrade_distribution})
            variables.update({"dry_run": args.dry_run})
            variables.update({
                "unhold_packages": args.unhold,
                "unhold_mesos_slave": args.unhold
            })
            if args.tags is not None:
                tags = "--tags=" + args.tags

            # ansible_command = subprocess.check_output(["which", "ansible-playbook"]).decode().strip()
            ansible_command = "ansible-playbook"
        else:
            # ansible_command = subprocess.check_output(["which", "ansible"]).decode().strip()
            ansible_command = "ansible"
            if abs_path != ".":
                command_list.extend(['--playbook-dir', abs_path])

        cmd = "{ansible_command} {command_list} --limit='{hosts}' -i {inventory} -e \"{variables}\" {tags}".format_map({
            "ansible_command": ansible_command,
            "command_list": " ".join(command_list),
            "hosts": hosts_str_cycle,
            "inventory": inventory,
            "variables": variables,
            "tags": tags
        })

        if args.debug_command:
            print()
            print(cmd)
            continue

        try:
            if args.playbook is not None and \
                    not args.yes and \
                    input('Execute for ServiceGroup `{}` (Y/n)'.format(sg)) == 'n':
                if not args.minimum_output:
                    print("Skipping serviceGroup `{}`".format(sg))
                continue
            print()
            # print(subprocess.check_output(cmd, shell=True).decode().strip())
            # sys.stdout.write(line)
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            for line in process.stdout:
                print(line.decode().strip())

        except Exception as e:
            print("There was an error:")
            print('error: {}'.format(e))
        finally:
            if not args.minimum_output:
                print("\n\nCommand was:\n\n\t{}".format(cmd))
                print("\n(took {:.2f}s)".format(time.time() - start_time))
