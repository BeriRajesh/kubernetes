#!/bin/bash
files_list="/home/bamboo/logs/png-s3-files-notification-every3hours.log"
#EMAIL=shailaja.gadupu@annalect.com
EMAIL="tan.song@annalect.com kimberly.white@annalect.com meghan.halligan@annalect.com katherine.szold@hearts-science.com karthik.anivilla@annalect.com deepanshu.kukreja@annalect.com tushar.khandetod@annalect.com"
echo "List of files uploaded into procter-gamble-prod S3 Bucket in last 3 hours" > $files_list 
echo -e ".................................................................................. \n" >> $files_list
yesterday_date=`date --date="yesterday" +%Y-%m-%d`
#echo $yesterday_date
aws s3 ls s3://procter-gamble-prod/ --recursive | awk -v d="$yesterday_date" '$1 >= d {print '$1'}' | sort -n | while read -r line;
  do
    createDate=`echo $line|awk {'print $1" "$2'}`
    echo $createDate
    createDate=`date -d"$createDate" +%s`
    oldDate=`date -d "-3 hour" +%s`
    if [[ $createDate -ge $oldDate ]]
      then 
        file=`echo $line`
        echo $file >> $files_list
    fi
 done;
echo -e "\n **********************************************************************************************" >> $files_list
mail -s "Procter-Gamble-Prod S3 Bucket Notification" $EMAIL < $files_list || exit 1

