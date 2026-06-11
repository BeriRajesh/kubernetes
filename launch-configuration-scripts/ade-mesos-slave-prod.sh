#!/bin/bash
echo "Starting user-data at " `date` > /var/log/user-data.log
ENV=Prod #ENV should be Prod, QA or Dev
BRANCH=prod #BRANCH should be prod, release or develop
LAYER=ingest
DEPLOY_USER=ansso
DEPLOY_PATH=/var/www/ade
cd $DEPLOY_PATH
sudo -u $DEPLOY_USER git fetch --all >> /var/log/user-data.log
sudo -u $DEPLOY_USER git reset --hard origin/$BRANCH >> /var/log/user-data.log
cd /var/www/ade/src
sudo -H pip install -r requirements.txt >> /var/log/user-data.log
sudo aws s3 --region us-east-1 cp s3://annalect.bootstrap-bucket/ade/${ENV}/US/${LAYER}/adeserveroverride.cfg /var/www/ade/src/adeserveroverride.cfg
sudo chmod a+r /var/www/ade/src/adeserveroverride.cfg
sudo chown ansso /var/www/ade/src/adeserveroverride.cfg
sudo service apache2 restart
sudo aws s3 --region us-east-1 cp s3://annalect.bootstrap-bucket/ade/${ENV}/US/${LAYER}/bootstrap.sh /root/bootstrap.sh >> /var/log/user-data.log
sudo sh /root/bootstrap.sh 2>&1 > /var/log/bootstrap.log

echo "End of user-data execution at " `date` >> /var/log/user-data.log
#END

