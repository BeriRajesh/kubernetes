#!/bin/bash
files_list="/home/bamboo/logs/png-s3-files-notifications-daily.txt"
echo -e "List of files in procter-gamble-prod S3 Bucket: \n" > $files_list 
# Konstain requested change 180321:
EMAIL="tan.song@annalect.com"
echo -e "\n **********************************************************************************************" >> $files_list
echo -e "  Date       Time       Size                File\n" >> $files_list 
echo -e "********************************************************************************************** \n" >> $files_list
aws s3 ls s3://procter-gamble-prod/ --recursive | sort -n >> $files_list || exit 1
echo -e "\n **********************************************************************************************" >> $files_list
mail -s "Procter-Gamble-Prod S3 Bucket Files Lists Notification" $EMAIL < $files_list || exit 1
