#!/bin/bash
set -x

# Script that uses zappa to deploy to Lambda
# Assumes current directory has a projects/<project> Git repo

SCRIPT_NAME="$0"
ARGS="$@"
NEW_VERSION_NAME="zappa-deploy-new.sh"

function check_update() {
    echo "---"
    echo "Checking for updates to this script..."

    git archive --remote=git@bitbucket.org:annalect/devops.git release -- zappa-deployment-scripts/${SCRIPT_NAME} | tar -xO > $NEW_VERSION_NAME

    set +e
    diff -q "$SCRIPT_NAME" ${NEW_VERSION_NAME} > /dev/null
    DIFF_RESULT=$?
    set -e

    if [[ ${DIFF_RESULT} == 0 ]]; then
        echo "We're using the latest version, yay!"
        echo "---"
    elif [[ ${DIFF_RESULT} == 1 ]]; then
        echo "There is a new version... restarting..."
        cp ${SCRIPT_NAME} "${SCRIPT_NAME}-$(date +%Y%m%d-%H%M).bak"
        mv ${NEW_VERSION_NAME} ${SCRIPT_NAME}
        chmod +x ${SCRIPT_NAME}
        $SCRIPT_NAME $ARGS
        exit $?
    elif [[ ${DIFF_RESULT} == 2 ]]; then
        echo "!!! There was trouble in the diff. You should look this into detail !!!"
        echo "Trying to deploy anyway with this running version."
    fi
}

# you can set the environment variable NOT_AUTO_UPDATE no any value
if [[ -z "$NOT_AUTO_UPDATE" ]]; then
    # check for new version
    check_update
fi

EXAMPLE_USAGE="$0 <dev|qa|prod|none> <project> <branch> [<stage>]"

if [ "$#" -lt 3 ]; then
    echo "Need to pass at least two argument. Ex. ${EXAMPLE_USAGE}"
    exit 1
fi


if [[ ! $1 == 'dev' && ! $1 == 'qa' && ! $1 == 'prod' && ! $1 == 'none' ]]; then
    echo "Wrong first argument. Use this way: ${EXAMPLE_USAGE}"
    exit 1
fi

BUILD_ENV=$1
PROJECT=$2
BRANCH=$3
ENDPOINT="$4"

STAGE="${PROJECT}_${BRANCH}"
if [ ! -z "$ENDPOINT" ]; then
    STAGE="${STAGE}_${ENDPOINT}"
fi

echo ------
echo "Entering projects/${PROJECT} and updating repo. Be sure they exist and are writable by user '$(whoami)''"
echo ------

pushd projects/${PROJECT}

git reset --hard

OLD_COMMIT_HASH=$(git log | head -n1 | awk '{print $2}')

git clean -fd --exclude=venv | true
git checkout -f $BRANCH | true
git fetch | true
git reset --hard origin/$BRANCH | true

NEW_COMMIT_HASH=$(git log | head -n1 | awk '{print $2}')

NEW_REQUIREMENTS=0
if git diff --name-only $OLD_COMMIT_HASH $NEW_COMMIT_HASH | grep requirements.txt; then
    NEW_REQUIREMENTS=1
fi

aws s3 cp s3://annalect-annalect-zappa/projects-conf/zappa_settings-${STAGE}.json zappa_settings.json
aws s3 cp s3://annalect-annalect-zappa/general-conf/template-__init__.py src/__init__.py
aws s3 cp s3://annalect-annalect-zappa/general-conf/requirements-zappa.txt .

# set Environment Variables
SECRETS_BUCKET_NAME="annalect-cloud-vault"
APP_NAME=${PROJECT}

# fix removing the underscore (_) from audience_builder
if [ "${PROJECT}" == "audience_builder" ]; then
    APP_NAME="audiencebuilder"
fi

if [[ ${BUILD_ENV} != 'none' ]]; then
    set +v
    eval $(aws s3 cp s3://${SECRETS_BUCKET_NAME}/container-secrets/ecs-kms-key - | sed 's/^/export /')

    APP_CONFIG="serveroverride.cfg"
    if [[ "${APP_NAME}" == "ade" ]]
    then
        APP_CONFIG="adeserveroverride.cfg"
    fi

    echo ------
    echo "Downloading ${BUILD_ENV}::${APP_NAME}::${APP_CONFIG} ..."
    aws s3 cp s3://${SECRETS_BUCKET_NAME}/container-secrets/"${BUILD_ENV}"/"${APP_NAME}"/"${APP_CONFIG}".encrypted . > /dev/null
    echo ------

    # echo "Decrypting file locally at your current working directory."
    aws-encryption-cli --decrypt --input "${APP_CONFIG}".encrypted \
    --encryption-context AppName=${APP_NAME} EnvName=${BUILD_ENV} \
    --metadata-output /tmp/metadata \
    --output  "${APP_CONFIG}" \
    --quiet
    set -v

    # temporal fix for currentSiteBaseUrl for audience_builder_devui
    if [ "${STAGE}" == "audience_builder_devui" ]; then
        echo ------
        echo "temporal bugfix: forcing https://devuiaudience.annalect.cloud for devui in currentSiteBaseUrl in serveroverride"
        sed --in-place -e 's#^.*currentSiteBaseUrl.*$#currentSiteBaseUrl = https://devuiaudience.annalect.cloud#g' ${APP_CONFIG}
        echo ------
    fi
    if [ "${STAGE}" == "ade_develop" ]; then
        echo ------
        echo "[SSO]" >> ${APP_CONFIG}
        echo "currentSiteBaseUrl = https://devadeweb.annalect.cloud"  >> ${APP_CONFIG}
        # sed --in-place -e 's#^.*currentSiteBaseUrl.*$#currentSiteBaseUrl = https://devadeweb.annalect.cloud#g' ${APP_CONFIG}
        echo ------
        mv ${APP_CONFIG} src/${APP_CONFIG}
    fi
fi

# setting location of virtual environment
if [[ -d venv ]]
then
    VENV="venv"
elif [[ -d src/venv ]]
then
    VENV=src/venv
fi

# only recreate virtualenvironment if requirements.txt file changed
if [[ "${NEW_REQUIREMENTS}" == "1" ]]
then
    # exit 1
    echo "Recreating and activating venv"
    rm -r $VENV || true
    virtualenv -p python3.6 $VENV
    source $VENV/bin/activate
    pip3 install -r requirements.txt 
fi

echo "Activating venv"
# set +x
source $VENV/bin/activate
# set -v

pip3 install -r requirements-zappa.txt  

# ADE has its files setup differently
if [[ "${APP_NAME}" == "ade" ]]
then
    cp zappa_settings.json src/
    cd src
fi
zappa update "${STAGE}"

set +v
rm serveroverride* || true
deactivate

echo "---"
echo "All OK!"
echo "---"
