#!/bin/bash
#Variables
DEPLOY_USER=ansso
DEPLOY_PATH=/var/www/ade
DEPLOY_CODE=prod

# RunScript=1 is for enabling execution of commands and RunScript=0 for not to execute commands

#Update config files
RunScript=1
if [ $RunScript -eq 1 ]; then
sudo aws s3 --region us-east-1 cp s3://annalect.bootstrap-bucket/ade/Prod/US/ingest/adeserveroverride.cfg /var/www/ade/src/adeserveroverride.cfg
sudo chmod a+r /var/www/ade/src/adeserveroverride.cfg
sudo chown ansso.ansso /var/www/ade/src/adeserveroverride.cfg
echo "copied adeserveroverride.cfg"
echo `ls -ltr /var/www/ade/src/adeserveroverride.cfg`
sudo service apache2 reload  2>&1 >> /var/log/adecodeupdate.log
fi

#Configure logstash to send mesos logs to loggly
RunScript=1
if [ $RunScript -eq 1 ]; then
env=Prod
sudo aws s3 --region us-east-1 cp s3://annalect.bootstrap-bucket/ade/${env}/US/ingest/logstash-loggly.conf /opt/logstash/logstash-loggly.conf
sudo aws s3 --region us-east-1 cp  s3://annalect.bootstrap-bucket/ade/${env}/US/ingest/logstash-autostart.sh /opt/logstash-autostart.sh
sudo chmod a+x /opt/logstash-autostart.sh
logstash-autostart.sh &
fi

#Mesos-Slave configuration
RunScript=1
if [ $RunScript -eq 1 ]; then
zk="zk://10.5.230.199:2181/mesos"
sudo service mesos-slave stop
sudo rm -rf /etc/mesos-slave/ip
sudo rm -rf /etc/mesos-slave/hostname
sudo rm -rf /etc/mesos/zk

#Configure Master zk
echo $zk | sudo tee /etc/mesos/zk

#Enable to listen on interface (eth0 or eth1)
sudo /sbin/ifconfig eth0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}' | sudo tee /etc/mesos-slave/ip
sudo cp /etc/mesos-slave/ip /etc/mesos-slave/hostname

#start the mesos-slave service
sudo service mesos-slave start
fi

#END
