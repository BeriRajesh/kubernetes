"""Python3 Script to deploy a Git project using zappa"""

import argparse
import os
import subprocess
import sys


def get_args():
    parser = argparse.ArgumentParser(
        description='Updates a Zappa configured stage')

    parser.add_argument("--base-path", default="/home/bamboo/zappa-deployments",
                        help="Base path, useful for testing. Defaults to /home/bamboo/zappa-deployments")

    parser.add_argument("-p", "--project", required=True,
                        help="Name of the repo to pull. Ex audience_builder")

    parser.add_argument("-b", "--branch", required=True,
                        help="Name of the branch of the repo.")

    parser.add_argument("-s", "--stage", required=True,
                        help="Name of the configured zappa stage to update.")

    parser.add_argument("-c", "--create-project", default=False, action="store_true",
                        help="Name of the configured zappa stage to update.")

    parser.add_argument("--debug-options", default=False, action="store_true",
                        help="Debug options passed to the script.")


    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.parse_args(['--help'])
        sys.exit()
        # parser.error('No arguments provided.')


    if args.debug_options:
        print(args)
        sys.exit()



    return args


def validate_project_dir(project_dir):
    if args.create_project is False:
        if os.path.isdir(project_dir) is False:
            print("Project path {} does not exist".format(project_dir))
            sys.exit(1)
        print("Project path exists: {}".format(project_dir))
        return True
    else:
        print("Create Project Feature not yet implemented")
        sys.exit(1)


def update_project(project_dir, branch):
    """ Updates repository of project_dir to the specified branch """


    print("CHDIR into : {}".format(project_dir))
    os.chdir(project_dir)

    if os.path.isdir(".git") is False:
        print("Path not a Git repository")
        sys.exit(1)

    # force reset
    print("Doing: git reset --hard")
    out = subprocess.check_output(["git", "reset", "--hard"])

    # delete extraneous files
    print("Doing: git clean -f")
    out = subprocess.check_output(["git", "clean", "-f"])

    # checking out branch
    print("Doing: git checkout -f {}".format(branch))
    out = subprocess.check_output(["git", "checkout", "-f", branch])

    # pulling branch
    print("Doing: git pull origin {}".format(branch))
    out = subprocess.check_output(["git", "pull", "origin", branch])

    return True


def update_lamba(project_dir, branch):
    """
    Uses zappa to deploy project to Lambda.

    First copies configuration from configuration dir, then issues a zappa update.
    """

    os.chdir(project_dir)

    configuration_dir = os.path.join(project_dir, CONFIGURATION_DIR)

    if os.path.isdir(configuration_dir) is False:
        print("No configuration path found at {}".format(configuration_dir))
        sys.exit(1)

    print("ok")


if __name__ == '__main__':
    CONFIGURATION_DIR = "zappa-conf"

    args = get_args()

    DEPLOY_ROOT = os.path.abspath(args.base_path)

    PROJECT_DIR = DEPLOY_ROOT + '/' + args.project
    BRANCH = args.branch


    validate_project_dir(PROJECT_DIR)

    update_project(PROJECT_DIR, BRANCH)

    update_lamba(PROJECT_DIR, BRANCH)
