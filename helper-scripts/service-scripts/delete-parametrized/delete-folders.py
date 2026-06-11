#!/usr/bin/env python3

import re
import subprocess
import sys

""" script to delete folders listed in a configuration file """

# from delete_folders_conf import folders

def get_folders_as_list(fname=None):
    if not fname:
        fname = "delete_folders_conf.py"

    lines = list()
    for line in open(fname, 'r'):
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("\""):
            lines.append(line)

    return lines


folder_rows = get_folders_as_list()


for row in folder_rows:
    fields = row.split("\t")

    action = fields[0]
    host = fields[1]
    size = fields[2]
    path = "/".join(fields[4:])

    if path[0] != '/':
        path = '/' + path

    # print(host)
    ip_from_host = re.search(r".*-(.*)$", host).group(1)
    # print(ip_from_host)

    print(f"Verifying size of {path}...")

    if not ip_from_host:
        sys.exit(f"Error with line, couldn't get IP adress of host: `{row}``")

    cmd = f"h -I {ip_from_host} --minimum-output --become -c 'du -hs {path}'"
    print(f"command: {cmd}", flush=True)
    # input("?")

    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    for line in process.stdout:
        print(line.decode().strip())
