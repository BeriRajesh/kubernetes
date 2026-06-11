#!/bin/bash
#Variables
DEPLOY_USER=ansso
DEPLOY_PATH=/var/www/ade
DEPLOY_CODE=develop

# RunScript=1 is for enabling execution of commands and RunScript=0 for not to execute commands


#Update config files
RunScript=0
if [ $RunScript -eq 1 ]; then
sudo aws s3 --region us-east-1 cp s3://annalect.bootstrap-bucket/ade/Dev/US/ingest/adeserveroverride.cfg /var/www/ade/src/adeserveroverride.cfg
sudo chmod a+r /var/www/ade/src/adeserveroverride.cfg
sudo chown ansso /var/www/ade/src/adeserveroverride.cfg
echo "Updated adeserveroverride.cfg"
echo `ls -ltr /var/www/ade/src/adeserveroverride.cfg`
sudo service apache2 reload  2>&1 >> /var/log/adecodeupdate.log
fi

#Configure logstash to send mesos logs to loggly
RunScript=1
if [ $RunScript -eq 1 ]; then
env=Dev
sudo aws s3 --region us-east-1 cp s3://annalect.bootstrap-bucket/ade/${env}/US/ingest/logstash-loggly.conf /opt/logstash/logstash-loggly.conf
sudo aws s3 --region us-east-1 cp  s3://annalect.bootstrap-bucket/ade/${env}/US/ingest/logstash-autostart.sh /opt/logstash-autostart.sh
sudo chmod a+x /opt/logstash-autostart.sh
sudo ln -sf  /opt/logstash-autostart.sh /usr/local/bin/logstash-autostart.sh
logstash-autostart.sh &
fi

#Fix fileload permissions in bootstrap script and on ingest servers 
#sudo adduser --ingroup  www-data --disabled-password --gecos "" marathon
sudo chown ansso /var/www/ade/util/log
sudo chgrp www-data /var/www/ade/util/fileload /var/www/ade/util/log /var/www/ade/util/querycache
sudo chmod g+rwxs /var/www/ade/util/fileload /var/www/ade/util/log /var/www/ade/util/querycache
sudo setfacl -m "default:group::rwx" /var/www/ade/util/fileload /var/www/ade/util/log /var/www/ade/util/querycache
sudo usermod -g www-data marathon

#Mesos-Slave configuration
RunScript=1
if [ $RunScript -eq 1 ]; then
zk="zk://10.5.226.215:2181/mesos"
sudo systemctl stop mesos-slave.service 
sudo rm -rf /etc/mesos-slave/ip
sudo rm -rf /etc/mesos-slave/hostname
sudo rm -rf /etc/mesos/zk

#Configure Master
echo $zk | sudo tee /etc/mesos/zk
#Enable to listen on interface (eth0 or eth1)
#sudo /sbin/ifconfig eth0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}' | sudo tee /etc/mesos-slave/ip
IPV4=`/usr/bin/curl -s http://169.254.169.254/latest/meta-data/local-ipv4`
echo $IPV4 | sudo tee /etc/mesos-slave/ip
sudo cp /etc/mesos-slave/ip /etc/mesos-slave/hostname

#start the mesos-slave service
sudo systemctl start mesos-slave.service
fi

#END
