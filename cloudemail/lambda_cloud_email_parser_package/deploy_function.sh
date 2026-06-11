#!/bin/bash

# creates a .zip package that can be uploaded to AWS Lambda
# copies all packages installed in the virtual environment ('venv' folder)
#    to the lambda function directory

pkgname="$(basename $PWD).zip"

rm packaged/* -r

rsync -av venv/lib/python3*/site-packages/ packaged \
    --exclude="pip*" \
    --exclude="setuptools*" \
    --exclude="__pycache__" \
    --exclude="easy_install*" \
    --exclude="boto3*/*" \
    --exclude="botocore*/*"

rsync -av src/ packaged --exclude="__pycache__"

cd packaged

zip -r9 ${pkgname} .
mv $pkgname ..