#!/bin/bash
# Download required scripts into /root/hardening directory
sudo apt-get update
sudo aws s3 --region us-east-1 cp s3://Automationscripts/Hardening_Ubuntu/generate_hostname.sh /root/hardening/generate_hostname.sh
sudo aws s3 --region us-east-1 cp s3://Automationscripts/Hardening_Ubuntu/host_domain_join /root/hardening/host_domain_join
sudo aws s3 --region us-east-1 cp s3://Automationscripts/Hardening_Ubuntu/ntp_installation_ubuntu.sh  /root/hardening/ntp_installation_ubuntu.sh
sudo aws s3 --region us-east-1 cp s3://Automationscripts/Hardening_Ubuntu/configure_timezone  /root/hardening/configure_timezone
sudo aws s3 --region us-east-1 cp s3://Automationscripts/Hardening_Ubuntu/DomainUserRestriction /root/hardening/DomainUserRestriction

#Fix permission on DomainUserRestriction
chmod a+x /root/hardening/DomainUserRestriction

#Update /etc/sudoers 
sudo aws s3 --region us-east-1 cp s3://Automationscripts/Hardening_Ubuntu/ubuntu1604_sudoers /root/hardening/ubuntu1604_sudoers
sudo cp /root/hardening/ubuntu1604_sudoers /etc/sudoers

#fix for rc.local
#sudo sed -i -e '/DomainUserRestriction/s/ sh//g' /etc/rc.local

#Generate Hostname
sudo sh /root/hardening/generate_hostname.sh

#Configure NTP
sudo sh /root/hardening/ntp_installation_ubuntu.sh

#Configure TimeZone
sudo sh /root/hardening/configure_timezone

#Configure AWS CloudWatch Memory Metric
sudo aws s3 --region us-east-1 cp s3://Automationscripts/Hardening_Ubuntu/awsmem-monitor-script-ubuntu.sh /root/hardening/ && sudo sh /root/hardening/awsmem-monitor-script-ubuntu.sh

#Add Log-Cleaning Cron
sudo aws s3 --region us-east-1 cp s3://Automationscripts/Hardening_Ubuntu/log-cleanup-script.sh /root/hardening/ && sudo sh /root/hardening/log-cleanup-script.sh
