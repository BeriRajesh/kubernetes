#!/bin/bash
set -e

SANITY_TEST_PATH=$1
REPORTS_FOLDER=$2
mkdir -p /tmp/reports/${REPORTS_FOLDER}
echo "Running the Sanity Test on pytest"
apt-get update
pip install --upgrade pip
pip install -r ${SANITY_TEST_PATH}/requirements.txt
mkdir -p webdrivers
wget https://chromedriver.storage.googleapis.com/${BROWSER_VERSION}/chromedriver_linux64.zip
unzip ./chromedriver_linux64.zip -d webdrivers/
export PATH="$PATH:`pwd`/webdrivers"
echo "Executing Pytest..."
cd ${SANITY_TEST_PATH}
python -m pytest tests_files/* -v --junitxml="/tmp/reports/${REPORTS_FOLDER}/results.xml" 
echo "Sanity Test Completed"