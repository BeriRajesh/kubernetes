#!/usr/bin/env python3

"""
Helper script to manage Ansible patching
"""
import argparse
import errno
import io
import sh
import sys
import readline


def get_args():
    parser = argparse.ArgumentParser(
        description='Fires Ansible patching with the correct options')
    parser.add_argument("action", choices=['list', 'patch'],
                        help="action to perform")
    # parser.add_argument("-v", "--verbose", default=0,
    #                     help="increase output verbosity", actions='count')
    parser.add_argument("-e", "--environment", choices=['Dev', 'QA', 'MGMT', 'Prod'], default='',
                        help="Environment to patch")

    parser.add_argument("-s", "--service-group", choices=["all"] + service_group_list, default='all',
                        help="Service group to patch")

    parser.add_argument("-i", "--inventory", choices=["us", "eu"], default='us',
                        help="Inventory (group of hosts) to use")

    # parser.add_argument("-t", "--step", action='store_true',
    #                     help="Inventory (group of hosts) to use")

    parser.add_argument("-u", "--upgrade-distribution", action='store_true',
                        help="Does a dist-upgrade on instance")

    parser.add_argument("-n", "--dry-run", action='store_true',
                        help="Does a distupgrade on instance")

    parser.add_argument("-o", "--unhold", action='store_true',
                        help="Unhold packages before doing dist-upgrade (kernel and mesos)")

    parser.add_argument("-y", "--yes", action='store_true',
                        help="Assumes yes to all yes/no questions")

    args = parser.parse_args()

    # print(args)
    # sys.exit()
    return args


def get_hosts():
    hosts_inclusions.append("tag_Environment_" + args.environment)

    hosts = ""
    for item in hosts_inclusions:
        if hosts != "":
            hosts += ":&"

        hosts += item

    for item in hosts_unions:
        if hosts != "":
            hosts += ":"

        hosts += item
    return hosts


def get_host_group():
    if args.inventory == "us":
        host_group = "hosts-us/hosts"
    elif args.inventory == "eu":
        host_group = "hosts-eu/hosts"
    else:
        sys.exit('error: host_group not recognized')

    return host_group


def get_action_list():
    action_list = []
    if args.action == 'list':
        action_list.append('--list-hosts')

    # if args.step:
    #     action_list.append('--step')

    return action_list


def sh_interact(char, stdin):
    global aggregated_output
    sys.stdout.write(char)
    sys.stdout.flush()
    aggregated_output += char
    if aggregated_output.endswith("ontinue: "):
        print('>')
        val = input()
        stdin.put(val + "\n")


service_group_list = ["analysis", "general", "dsdk", "wellsfargo", "utility", "mongodb", "bamboo", "samba", "openvpn",
                      "openswan", "apache", "mesos_master", "mesos_slave"]

if __name__ == '__main__':

    args = get_args()

    aggregated_output = ""

    hosts_exclusions = list()
    hosts_inclusions = list()
    hosts_unions = list()

    hosts = get_hosts()
    action_list = get_action_list()
    host_group = get_host_group()

    service_groups = [args.service_group]

    if service_groups == ['all']:
        service_groups = service_group_list

    variables = {}
    variables.update({"mongodb_backup_done": True})
    variables.update({"upgrade_distribution": args.upgrade_distribution})
    variables.update({"dry_run": args.dry_run})
    variables.update({
        "unhold_packages": args.unhold,
        "unhold_mesos_slave": args.unhold
    })
    variables.update({"ansible_python_interpreter": "/usr/bin/python2.7"})

    for sg in service_groups:
        sg_filter = ':&tag_ServiceGroup_' + sg

        # baking command with options
        run_playbook = sh.ansible_playbook.bake(
            ["patch_with_script.yml"] + action_list,
            i=host_group,
            limit=hosts+sg_filter,
            e=str(variables))
        # ,
        # ,
        # _iter = True,
        # _iter_noblock = True, _out_bufsize = False

        print('The *unquoted* command is: ')
        print(run_playbook)

        if not args.yes and input('Patch ServiceGroup `{}` (Y/n)'.format(sg)) == 'n':
            print("Not patching ServiceGroup `{}`".format(sg))
            continue

        # print(" ".join(['\n\n', 'ansible-playbook']+ansible_options.split(" ")+variables+['\n\n']))
        # continue

        try:
            run_playbook(_out=sh_interact, _out_bufsize=0)
            # for line in run_playbook():
            #     if line == 1:
            #         sys.exit('error')
            #     if line == errno.EWOULDBLOCK:
            #         # print("doing something else...")
            #         # time.sleep(0.5)
            #         pass
            #     else:
            #         print(line)
            #         pass
        except Exception as e: # sh.ErrorReturnCode_1:
            # print('error: {}'.format(var_err))
            print('error: {}'.format(e))
            pass
