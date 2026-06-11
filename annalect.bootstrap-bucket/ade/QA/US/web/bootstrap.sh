#!/bin/bash
echo "Starting bootstrap script at " `date`
#Variables
ENV=QA #ENV should be Prod, QA or Dev
BRANCH=release #BRANCH should be prod, release or develop
LAYER=web
DEPLOY_USER=ansso
DEPLOY_PATH=/var/www/ade

# RunScript=1 is for enabling execution of commands and RunScript=0 for not to execute commands

#Update config files
RunScript=0
if [ $RunScript -eq 1 ]; then
cd $DEPLOY_PATH
sudo -u $DEPLOY_USER git fetch --all >> /var/log/user-data.log
sudo -u $DEPLOY_USER git reset --hard origin/$BRANCH >> /var/log/user-data.log
cd /var/www/ade/src
sudo -u $DEPLOY_USER -H /bin/bash -c 'source venv/bin/activate; pip install -r requirements.txt' >> /var/log/user-data.log
sudo aws s3 --region us-east-1 cp s3://annalect.bootstrap-bucket/ade/${ENV}/US/${LAYER}/adeserveroverride.cfg /var/www/ade/src/adeserveroverride.cfg
sudo chmod a+r /var/www/ade/src/adeserveroverride.cfg
sudo chown ansso /var/www/ade/src/adeserveroverride.cfg
sudo service apache2 reload
fi

#Fix permission with fileload and querycache
sudo chown -R ansso /var/www/ade/util/fileload /var/www/ade/util/querycache

#fix issue with /home/ansso/.cache writing permissions
sudo mkdir -p /home/ansso/.cache || true
sudo chmod 777 -R /home/ansso/.cache

echo "End of bootstrap script at " `date`

#END

