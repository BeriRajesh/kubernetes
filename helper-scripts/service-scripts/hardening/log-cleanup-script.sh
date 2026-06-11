#!/bin/bash
grep  "/var/log/" /var/spool/cron/crontabs/root
count=`grep  "/var/log/" /var/spool/cron/crontabs/root | wc -l`
if [ $count -eq 1 ]; then
echo "Exiting as Log Cleanup Job is already added"
else
sudo crontab -l | { cat; echo '00 00 * * 6 cd /var/log/ ; find . -name "*.log.*" -mtime +15 -type f -exec rm -f {} \;'; } | sudo crontab -
echo ""
echo ""
fi
