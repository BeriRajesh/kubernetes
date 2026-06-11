#!/bin/bash
#EMAIL="cloud-command-center-L2team@wipro.com Cloud-Command-Center-L1Team@wipro.com annalecttio@annalect.com shailaja.gadupu@annalect.com"
#EMAIL="shailaja.gadupu@annalect.com shashikant.kuwar@annalect.com"
EMAIL=shailaja.gadupu@annalect.com
LOGFILE="/home/bamboo/logs/mongobackup.log"
COMMAND="/home/bamboo/mongo-scripts/mongo_dump.sh"
errors="false"
yest=`date +%Y-%m-%d --date '1 days ago'`

#Mongo Backup - US VPC - - Add US Mongo Instance here
$COMMAND dev alloc 2>  $LOGFILE
$COMMAND qa alloc 2>>  $LOGFILE
$COMMAND prod alloc 2>>  $LOGFILE
$COMMAND dev assembly 2>>  $LOGFILE
$COMMAND qa assembly 2>>  $LOGFILE
$COMMAND prod assembly 2>>  $LOGFILE

find "/backup/mongodbbackup/dev/"$yest"" -type d | xargs rm -rf >> $LOGFILE 
find "/backup/mongodbbackup/prod/"$yest"" -type d | xargs rm -rf >> $LOGFILE
find "/backup/mongodbbackup/qa/"$yest"" -type d | xargs rm -rf >> $LOGFILE

if [ -s $LOGFILE ]; then
   while read -r line;
   do
   #ignoring the warning messages
      severity=`echo $line | cut -b 1-7`
      #echo $severity
      if [[ $severity != "WARNING" ]]; then
         errors="true"
         #echo "errors true"
      fi      
   done < $LOGFILE
   if [ $errors = "true" ]; then
      echo "---------------------------------------------------------------------------------------" >> $LOGFILE
      echo "The task triggered from Bamboo and executed on Utility Server" >> $LOGFILE
      echo "Script Triggered: "$COMMAND"" >> $LOGFILE
      echo "Bamboo Link: https://bamboo.annalect.com/browse/CRON-MONBKP" >> $LOGFILE
      echo "Please check to see if there is something wrong here" >> $LOGFILE
      echo "---------------------------------------------------------------------------------------" >> $LOGFILE
      mail -s "High Impact Incident: Mongo Backup Error" $EMAIL < $LOGFILE
   fi
fi


#END
