#!/bin/bash
set -e

curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
apt-get update
apt-get install xvfb python python-pip build-essential -y
pip install --upgrade pip
pip install -r ${SANITY_TEST_PATH}/requirements.txt
cp xvfb.init /etc/init.d/xvfb
chmod +x /etc/init.d/xvfb
update-rc.d xvfb defaults
service xvfb start
mkdir -p webdrivers
wget https://chromedriver.storage.googleapis.com/${BROWSER_VERSION}/chromedriver_linux64.zip
unzip ./chromedriver_linux64.zip -d webdrivers/
export PATH="$PATH:`pwd`/webdrivers"
export DISPLAY=:5
echo "Executing Test..."
cd ${SANITY_TEST_PATH}
python3 -m xmlrunner discover -t ./  -o /tmp/reports/sanity_reports > log.txt 2>&1
cat log.txt
cat log.txt | grep "ERROR"
[ $? -eq 0 ] && echo "Sanity Test Failed, Deployment is Cancelled. Please look at the Output Log and Fix the Issues." && exit 1 || echo "Sanity Test Passed Successfully"