#!/bin/bash
set -e

REQUIREMENTS_FILE=requirements.txt
if [ ! -f "${REQUIREMENTS_FILE}" ]; then
    echo "WARNING: ${REQUIREMENTS_FILE} file not found. Not intalling any requirements."
    exit 0
fi

DOCKER_DEPLOYMENT_KEY_PATH=${1:-}

export GIT_SSH_COMMAND="ssh -i $DOCKER_DEPLOYMENT_KEY_PATH -o UserKnownHostsFile=./known_hosts"
ssh-keyscan bitbucket.org > ./known_hosts

chmod 0600 $DOCKER_DEPLOYMENT_KEY_PATH

cat requirements.txt | grep -v \
    -e pyodbc \
    -e pylect_infra \
    > requirements.filtered.txt

docker run -v $(pwd):/var/task -w /var/task lambci/lambda:build-python3.7 pip3 install -r requirements.filtered.txt -t packages
