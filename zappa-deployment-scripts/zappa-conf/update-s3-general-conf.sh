#!/bin/bash
set -e

aws s3 cp requirements-zappa.txt           s3://annalect-annalect-zappa/general-conf/
aws s3 cp template-__init__.py             s3://annalect-annalect-zappa/general-conf/
aws s3 cp zappa_settings-STAGE.sample.json s3://annalect-annalect-zappa/general-conf/