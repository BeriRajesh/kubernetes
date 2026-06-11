#!/bin/bash
set -e

if [ ! -d venv ]; then
    python3 -m venv venv
fi

source venv/bin/activate

if [ -f "function.zip" ]; then rm function.zip; fi

echo "Installing our dependencies"
pip install git+ssh://git@bitbucket.org/annalect/pylect-infra.git@v.1.2.6 --upgrade
# pip -q install ../../../pylect-infra --upgrade

cd venv/lib/python3.6/site-packages/

echo "Compressing dependencies"
zip -qr9 ${OLDPWD}/function.zip .
cd $OLDPWD

# not deleting cache...
# "*/__pycache__" \
# "__pycache__/*" \
# "*/__pycache__/*" \

echo "Removing unnecesary packages from .zip"
zip -qd function.zip \
    "easy_install.py" \
    "pip*" \
    "docutils/*" \
    "botocore/*" \
    "boto3/*" \
    "s3transfer/*" \
    "setuptools/*" \
    "*.egg-info/*" \
    "*.dist-info/*"


echo "Adding our .py files"
zip -qg function.zip lambda_function.py
zip -qg function.zip rollback_deployments.py

echo "Updating Lambda"
aws lambda update-function-code --function-name rollback_ecr_deployments --zip-file fileb://function.zip
