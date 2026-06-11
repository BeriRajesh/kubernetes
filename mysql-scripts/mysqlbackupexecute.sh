#!/bin/bash

#set -x

#EMAIL="cloud-command-center-L2team@wipro.com Cloud-Command-Center-L1Team@wipro.com annalecttio@annalect.com shailaja.gadupu@annalect.com"
EMAIL="adt@annalect.com shashikant.kuwar@annalect.com"
LOGFILE="/home/bamboo/logs/rdsbackup.log"
COMMAND="/home/bamboo/mysql-scripts/mysqldumpbackup.sh"

errors="false"


DB_ENDPOINTS=(\
    pipeline-dev.c488xyottj77.us-east-1.rds.amazonaws.com \
    anlctprod-eu-mysql.ctr41hpvtdsv.eu-west-1.rds.amazonaws.com \
    adeprod.c488xyottj77.us-east-1.rds.amazonaws.com \
    anlctdev-e1-mysql-001.c488xyottj77.us-east-1.rds.amazonaws.com \
    anlctdev-eu-mysql.ctr41hpvtdsv.eu-west-1.rds.amazonaws.com \
    anlctmgmt-e1-mysql-001.c488xyottj77.us-east-1.rds.amazonaws.com \
    anlctprod-e1-mysql-001.c488xyottj77.us-east-1.rds.amazonaws.com \
    anlctqa-e1-mysql-001.c488xyottj77.us-east-1.rds.amazonaws.com \
    menaportal-emea-dev.ctr41hpvtdsv.eu-west-1.rds.amazonaws.com \
    pipeline-aapl-prod.c488xyottj77.us-east-1.rds.amazonaws.com \
)


    # plportal-dev.c488xyottj77.us-east-1.rds.amazonaws.com \
    # plportal-qa.c488xyottj77.us-east-1.rds.amazonaws.com \
    # plportal-stg.c488xyottj77.us-east-1.rds.amazonaws.com \

echo -----------------
echo Starting backup

for ENDPOINT in ${DB_ENDPOINTS[@]}
do
    echo "Excuting" $COMMAND "${ENDPOINT/.*}" "${ENDPOINT}" 2>> "${LOGFILE}"
    $COMMAND "${ENDPOINT/.*}" "${ENDPOINT}" 2>> "${LOGFILE}"
done


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
      echo "Bamboo Link: https://bamboo.annalect.com/browse/CRON-RDSBKP" >> $LOGFILE
      echo "Please check to see if there is something wrong here" >> $LOGFILE
      echo "---------------------------------------------------------------------------------------" >> $LOGFILE
      mail -s "High Impact Incident: RDS Backup Error" $EMAIL < $LOGFILE
   fi
fi

#END
