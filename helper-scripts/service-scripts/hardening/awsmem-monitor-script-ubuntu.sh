#!/bin/bash
#Script to install cloudwatch monitoring codes on Ubuntu system to send memory metrics to AWS CloudWatch
#!/bin/bash
grep  "mon-put-instance" /var/spool/cron/crontabs/root
count=`grep  mon-put-instance /var/spool/cron/crontabs/root | wc -l`
if [ $count -gt 1 ]; then echo "There are total $count jobs running for sending memory data to AWS CloudWatch, please remove duplicate cron entries running"; exit 1;fi
if [ $count -eq 1 ]; then
echo "Exiting as AWS CloudWatch Monitoring codes already installed"
else
SCRIPT_PATH=/opt
sudo apt-get -y install unzip libwww-perl libdatetime-perl
cd $SCRIPT_PATH
wget http://aws-cloudwatch.s3.amazonaws.com/downloads/CloudWatchMonitoringScripts-1.2.2.zip
unzip CloudWatchMonitoringScripts-1.2.2.zip
rm CloudWatchMonitoringScripts-1.2.2.zip
cd $SCRIPT_PATH/aws-scripts-mon
sudo crontab -l | { cat; echo '*/5 * * * * '$SCRIPT_PATH'/aws-scripts-mon/mon-put-instance-data.pl --mem-used-incl-cache-buff --mem-util --disk-space-util --disk-path=/ --from-cron'; } | sudo crontab -
echo ""
echo ""
echo "Testing Setup .........."
./mon-put-instance-data.pl --mem-util --verify –verbose
RESULT=$?
if [ $RESULT -eq 0 ]; then echo "To view the data sent to CloudWatch, go to the AWS CloudWatch dashboard and select "System/Linux:InstanceId" to view the specific instance metrics."; fi
fi
