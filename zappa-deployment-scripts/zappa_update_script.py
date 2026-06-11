"""Python3 Script to deploy a Git project using zappa"""

import argparse
import os
import subprocess
import sys


def get_args():
    parser = argparse.ArgumentParser(
        description='Updates a Zappa configured stage')

    parser.add_argument("--base-path", default=DEFAULT_BASE_PATH,
                        help="Base path, useful for testing. Defaults to /home/bamboo/zappa-deployments")

    parser.add_argument("-p", "--project", required=True,
                        choices=["audience_builder"],
                        help="Name of the repo to pull. Ex audience_builder")

    parser.add_argument("-b", "--branch", required=True,
                        help="Name of the branch of the repo.")

    parser.add_argument("-s", "--stage",
                        help="Name to be appended to the stage name (defaults to project-branch).")

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


def exec_command(cmd, comments=""):
    """Executed cmd and returns its output"""

    if type(cmd) == str:
        print("\n**\n** Doing: {}\n**".format(cmd))
        shell = True
    elif type(cmd) == list:
        print("\n**\n** Doing: {}\n**".format(" ".join(cmd)))
        shell = False
    else:
        print("Invalid command {}".format(cmd))
        sys.exit(1)

    process = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE)
    for line in process.stdout:
        print(line.decode().strip())


def validate_environment(project_dir):
    """ Validates that necessary files are present """

    if args.create_project is False:
        if os.path.isdir(project_dir) is False:
            print("Project path {} does not exist".format(project_dir))
            sys.exit(1)

        if os.path.isdir(os.path.join(project_dir, '.git')) is False:
            print("Project path {} is not a Git repo".format(project_dir))
            sys.exit(1)

        print("Project path exists and is a Git repo: {}".format(project_dir))
    else:
        print("Create Project Feature not yet implemented")
        sys.exit(1)

    if os.path.isdir(os.path.join(project_dir, "..", "..", CONFIGURATION_DIR)) is False:
        print("Configuration path {} does not exist".format(CONFIGURATION_DIR))
        sys.exit(1)

    print("Configuration path {} exists".format(CONFIGURATION_DIR))


def update_project(project_dir, branch):
    """ Updates repository of project_dir to the specified branch """

    os.chdir(project_dir)

    # force reset
    exec_command("git reset --hard")

    # delete extraneous files
    exec_command("git clean -f")

    # checking out branch
    exec_command(["git", "checkout", "-f", branch])

    # pulling branch
    exec_command(["git", "pull", "origin", branch])

    return True


def prepare_deployment_environment(project_dir):
    """Install project requirements file and zappa requirements"""

    os.chdir(project_dir)

    # activate virtual environment or create new
    if not os.path.isdir('venv'):
        print("Creating virtual environment")
        exec_command("virtualenv -p python2 venv")

    # installing zappa requirements
    zappa_requirement_file = "requirements-zappa.txt"
    zappa_settings = "zappa_settings.json"
    init_py = "template-__init__.py"

    if not os.path.isfile(zappa_requirement_file):
        exec_command(
            'cp ../../{}/{} .'.format(CONFIGURATION_DIR, zappa_requirement_file))

    if not os.path.isfile(zappa_settings):
        exec_command(
            'cp ../../{}/{} .'.format(CONFIGURATION_DIR, zappa_settings))

    if not os.path.isfile(init_py):
        exec_command(
            'cp ../../{}/{} src/__init__.py'.format(CONFIGURATION_DIR, init_py))

def execute_deployment_shell_script(project_dir):
    """Creates and execute deployment deployment_script"""


    os.chdir(project_dir)

    deployment_script = """
#!/bin/bash

PROJECT_PATH=$1
STAGE=$2

PWD


. venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-zappa.txt

#zappa update $STAGE

deactivate
"""

    # create and execute deployment_script
    script_name = "deploy.sh"
    fh = open("deploy.sh", 'w')
    fh.write(deployment_script)
    fh.close()

    import stat
    os.chmod(script_name, stat.S_IXUSR)

    exec_command(["bash", script_name, PROJECT, STAGE])


if __name__ == '__main__':
    CONFIGURATION_DIR = "zappa-conf"

    # getting args
    DEFAULT_BASE_PATH = "/home/bamboo/devops/zappa-deployment-scripts"
    args = get_args()

    PROJECT = args.project

    # full path, although base_path could be relative
    BASE_PATH = os.path.abspath(args.base_path)

    PROJECT_DIR = os.path.join(BASE_PATH, 'projects', PROJECT)
    BRANCH = args.branch

    STAGE = "{}-{}".format(PROJECT, BRANCH)
    if args.stage:
        STAGE = "{}-{}".format(STAGE, args.stage)

    # does it exist?
    validate_environment(PROJECT_DIR)

    update_project(PROJECT_DIR, BRANCH)

    prepare_deployment_environment(PROJECT_DIR)

    execute_deployment_shell_script(PROJECT_DIR)

    print("END!")
