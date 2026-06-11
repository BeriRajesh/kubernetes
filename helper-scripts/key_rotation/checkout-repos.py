#!/usr/bin/env python3.6

"""
- Checks out all repos from the current directory into checkedout-repos directory
- Searches a regex in all checkout repos

Sample usage:
    1- Log in to Bamboo server
    2- Go to `$ cd /backup/bitbucket-backup`
    3- Verify that the latest version of this script is in that path
    4- Run: `$ python3.6 checkout-repos.py`

    Note: Check out the configuration variables at the beginning of script

"""

import os
import sys
import subprocess
import shutil

cwd = os.getcwd()

#flag to enable checking out the repos in their develop|dev|Dev branch
checkout_repos_path = 'checkedout-repos'
checkout_repos_flag = False

# flag to enable searching for the regex in the repo's *.cfg files
search_regex_flag = False
aws_keys_regex = "[A-Z0-9]{20}"

def execute_command(str):
    print(str)
    out = subprocess.check_output(str, shell=True, stderr=subprocess.STDOUT)
    return out.decode()

def checkout_repos(cwd='', checkout_repos_path=checkout_repos_path):
    os.chdir(cwd)
    directories = os.listdir(".")
    for repo in directories:
        print()
        print(f'Repo: {repo}')
        os.chdir(cwd)
        if not os.path.isdir(repo): continue

        destination = f"{checkout_repos_path}/{repo}"
        if os.path.isdir(destination):
            print("Repository already cloned")
        else:
            # if os.path.isdir(destination):
            #     print(f"Deleting old: {destination} before cloning")
            #     shutil.rmtree(destination)
            try:
                out = execute_command(f'git clone {repo} {destination}')
                print(f"Checked out repo {repo} to {destination}")
                print(out.strip())
                os.chdir(destination)
                branches = execute_command(f'git branch -a').split('\n')
                if branches == ['']:
                    print(f"No branches in {repo}, continuing.")
                    continue
                done = False
                for branch in branches:
                    dev_branches = ['develop','dev', 'Dev']
                    for branch_name in dev_branches:
                        if branch_name in branch:
                            out = execute_command(f'git checkout -b {branch_name} origin/{branch_name}')
                            print(out.strip())
                            done=True
                            break
                    if done: break

                else:
                    print(f"Available branches: {branches}")
                    print("No develop branch")
            except subprocess.CalledProcessError as e:
                print("ERROR with {}: command '{}' return with error (code {}): {}".format(repo, e.cmd, e.returncode, e.output))
                continue

        os.chdir(destination)
        if not os.path.isdir('.git'):
            print('.git directory not found. continuing.')
            continue
        branches = execute_command(f'git branch -a').split('\n')
        if branches == ['']:
            print(f"No branches in {repo}, continuing.")
            continue

        print(f'.git dir found. cwf: {os.getcwd()}')

        out = execute_command(f'git pull')
        print(out.strip())
    print('Finished checking out repos!')



if checkout_repos_flag:
    checkout_repos(cwd=cwd, checkout_repos_path=checkout_repos_path)

if search_regex_flag == True:
    os.chdir(cwd)
    os.chdir(checkout_repos_path)

    out = execute_command(f'find . -name *.cfg -exec grep -E "{aws_keys_regex}" {{}} \\; -print')
    print(out)

    print('Finished greeping for expressions!')

