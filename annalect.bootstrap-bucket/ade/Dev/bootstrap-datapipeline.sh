#!/bin/bash
#Variables
DEPLOY_USER=ansso
DEPLOY_PATH=/var/www/ade
DEPLOY_CODE=develop

# RunScript=1 is for enabling execution of commands and RunScript=0 for not to execute commands


RunScript=1
if [ $RunScript -eq 1 ]; then
sudo aws s3 --region us-east-1 cp s3://Automationscripts/bootstraps/ade/odbc.sh /tmp/odbc.sh
sudo chmod a+x /tmp/odbc.sh
sudo sh /tmp/odbc.sh  2>&1 >> /var/log/odbcinstall.log
fi

#Update config files
RunScript=1
if [ $RunScript -eq 1 ]; then
sudo aws s3 --region us-east-1 cp s3://Automationscripts/bootstraps/ade/Dev/adeserveroverride.cfg /var/www/ade/src/adeserveroverride.cfg
sudo chmod a+r /var/www/ade/src/adeserveroverride.cfg
sudo chown ansso.ansso /var/www/ade/src/adeserveroverride.cfg
echo "Updated adeserveroverride.cfg"
echo `ls -ltr /var/www/ade/src/adeserveroverride.cfg`
sudo service apache2 reload  2>&1 >> /var/log/adecodeupdate.log
fi

#END


