#!/bin/bash
set -e

files_list="/home/bamboo/logs/google-s3-files-notification-every4hours.log"
#EMAIL=shashikant.kuwar@annalect.com
EMAIL="samiksha.chhetri@annalect.com Rajan.Singh@annalect.com Richa.Kushwaha@annalect.com Shishir.Singh@annalect.com Melitta.Ellerbe@annalect.com Michele.Pirri@annalect.com Christina.Xing@annalect.com shashikant.kuwar@annalect.com konstantin.markov@annalect.com"
yesterday_date=`date --date="yesterday" +%Y-%m-%d`
#count=$(aws s3 ls s3://omg-agencies/annalect/competitive/google/ --recursive | awk -v d="$yesterday_date" '$1 >= d {print '$1'}' |wc -l)
current_time=`date '+%Y-%m-%d %H:%M:%S' -d  "4 hour ago"`
> $files_list
aws s3 ls s3://omg-agencies/annalect/competitive/google/ --recursive | awk -v d="$yesterday_date" '$1 >= d {print '$1'}' | sort -n | while read -r line;
  do
    createDate=`echo $line|awk {'print $1" "$2'}`
    echo $createDate
    createDate=`date -d"$createDate" +%s`
    oldDate=`date -d "-4 hour" +%s`
    if [[ $createDate -ge $oldDate ]]
      then
        file=`echo $line`
        echo $file >> $files_list
    fi
 done;
if [ -s $files_list ]; then
message="List of files uploaded into s3://omg-agencies/annalect/competitive/google/ in last 4 hours"
# sed -i -e "List of file(s) in omg-agencies s3 bucket delivered after $current_time UTC -\\n" $files_list
files_list=$(echo "$message\n\n$(cat $files_list)")
echo -e "$files_list" | mail -s "Google S3 Delivery Notification" $EMAIL
fi