#!/bin/bash
set -e

TEST_NAME=$1
SELENIUM_TEST_PATH=$2
REPORTS_FOLDER=$3
echo "Pre-Configuring for the "${TEST_NAME}
mkdir -p /tmp/reports
curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
apt-get update
apt-get install xvfb python python-pip build-essential -y
pip install --upgrade pip
pip install -r ${SELENIUM_TEST_PATH}/requirements.txt
cp xvfb.init /etc/init.d/xvfb
chmod +x /etc/init.d/xvfb
update-rc.d xvfb defaults
service xvfb start
mkdir -p webdrivers
wget https://chromedriver.storage.googleapis.com/${BROWSER_VERSION}/chromedriver_linux64.zip
unzip ./chromedriver_linux64.zip -d webdrivers/
export PATH="$PATH:`pwd`/webdrivers"
export DISPLAY=:5
echo "Preconfig Completed for "${TEST_NAME}" and Executing Test Now..."
echo "Executing "${TEST_NAME}"...."
python -m xmlrunner discover -s ${SELENIUM_TEST_PATH}  -o /tmp/reports/${REPORTS_FOLDER} > log.txt 2>&1
cat log.txt