#!/bin/bash
set -e

# Local Layer Working Directory (LLWD, full path)
LAYER_PATH=pyodbc-lambda-layer
LLWD="$(PWD)/$LAYER_PATH"

LAYER_BUILD_SCRIPT="build-lambda-mssql-layer.sh"
LAYER_NAME=annalectI
LAYER_DESCRIPTION="Annalect Layer I: mssql, pylect-infra"
LAYER_RUNTIME="python3.7"

DOCKER_DEPLOYMENT_KEY_PATH_USER=${1:-}
DOCKER_DEPLOYMENT_KEY_PATH=docker-deployments.key

ZIP_NAME=pyodbc-layer.zip

CWD=$(pwd)

ADD_PINFRA=true
REMOVE=true
UPDATE_LAYER=true

if [ "$2" = "test" ]; then

    # remember to be connected to OVPN

    ### some testing commands
    # bash

    # once inside the container, exccute: export PYTHONPATH=/opt/python/lib/python3.7/site-packages
    cp odbc_test.py $LLWD/
    echo "Testing pyodbc/mssql connection"
    docker run -e PYTHONPATH="/opt/python/lib/python3.7/site-packages"  -v "$LLWD":/opt -w /opt -it lambci/lambda:build-python3.7 python3 odbc_test.py
    echo "Testing pylect_infra (echoing PATH variable)"
    docker run -e PYTHONPATH="/opt/python/lib/python3.7/site-packages"  -v "$LLWD":/opt -w /opt -it lambci/lambda:build-python3.7 python3 -c 'import pylect_infra as pinfra; print(pinfra.ssm.get_value("PATH"))'

    #docker run -it -e PYTHONPATH=".:/opt/python/lib/python3.7/site-packages"  -v "$LLWD":/opt -w /opt -it lambci/lambda:build-python3.7 bash

    # exit 1
    ###
    exit 0
fi

function copy_secret_key {
    if [ ! -f "$DOCKER_DEPLOYMENT_KEY_PATH" ]; then
        if [ -z $DOCKER_DEPLOYMENT_KEY_PATH_USER ]; then
            echo "ERROR: Please specify the path for the deployment key as a first parameter. Eg. ./$0 /path/to/deployment_key.ext"
            exit 1
        fi
        if [ ! -f $DOCKER_DEPLOYMENT_KEY_PATH_USER ]; then
            echo "ERROR: Key not found at path: $DOCKER_DEPLOYMENT_KEY_PATH_USER"
            exit 1
        fi

        echo "Found key in: $DOCKER_DEPLOYMENT_KEY_PATH_USER"
        cp $DOCKER_DEPLOYMENT_KEY_PATH_USER $DOCKER_DEPLOYMENT_KEY_PATH
    fi
}

if [ "$REMOVE" == true ]; then
    echo "Removing and creating directory:: ${LAYER_PATH}"
    rm -r "${LLWD}" || true
    mkdir "${LLWD}" || true
else
    echo "Not removing previous $LLWD becuse REMOVE=$REMOVE "
fi

echo "Copying build script to: ${LAYER_PATH}"
cp ${LAYER_BUILD_SCRIPT} ${LAYER_PATH}

# call function
copy_secret_key
cp "${DOCKER_DEPLOYMENT_KEY_PATH}" ${LLWD}

echo "Building layer inside Amazon Linux Docker container..."
docker run --name "docker-$LAYER_NAME" -v "$LLWD":/opt -w /opt lambci/lambda:build-python3.7 bash "${LAYER_BUILD_SCRIPT}"

# docker run -v "$LLWD":/opt -w /opt -it lambci/lambda:build-python3.7 bash
echo "Docker ran successfully to build $ZIP_NAME"
if [ "$ADD_PINFRA" == true ]; then
    pip install git+ssh://git@bitbucket.org/annalect/pylect-infra.git@v.1.x --upgrade -t "$LLWD/python/lib/python3.7/site-packages/"
fi

# package the content in a zip file to use as a lambda layer
cd $LLWD
TEMPFNAME="$(mktemp -d)/$ZIP_NAME"
rm "$TEMPFNAME" || true
zip -r9 "$TEMPFNAME" .
mv "$TEMPFNAME" "$LLWD/$ZIP_NAME"

if [ "$UPDATE_LAYER" == true ]; then
    echo "Updating Layer"
    aws lambda publish-layer-version \
        --layer-name "${LAYER_NAME}" \
        --description "${LAYER_DESCRIPTION}" \
        --zip-file "fileb://${LLWD}/${ZIP_NAME}" \
        --compatible-runtimes "${LAYER_RUNTIME}" \
        --cli-connect-timeout 6000
else
    echo "Not updating layer becase UPDATE_LAYER = $UPDATE_LAYER "
fi

echo "Deleting private key"
rm ${LLWD}/${DOCKER_DEPLOYMENT_KEY_PATH} || true
rm ${CWD}/${DOCKER_DEPLOYMENT_KEY_PATH} || true

cd ${CWD}
echo "Finished process!"
