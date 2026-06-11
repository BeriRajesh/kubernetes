#!/bin/bash
echo "Starting user-data at " `date` > ~/boot.log
VERSION=develop
DEPLOY_USER=ubuntu
DEPLOY_PATH=/home/ubuntu/ytsafe
cd $DEPLOY_PATH
sudo -u $DEPLOY_USER git fetch --all >> ~/boot.log
sudo -u $DEPLOY_USER git reset --hard origin/$VERSION >> ~/boot.log
#sudo pip install -r requirements.txt >> ~/boot.log
cd /home/ubuntu/ytsafe/src/
for i in `seq 10`
do
#python safe_agent.py & 
rm -rf ~/list.txt
ls  >> ~/list.txt &
done
echo "End of user-data execution at " `date` >> ~/boot.log
