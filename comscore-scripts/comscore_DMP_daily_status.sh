#!/bin/bash
#EMAIL="shailaja.gadupu@annalect.com"
EMAIL="annalecttio@annalect.com john.briscoe@annalect.com"
LOGFILE=/home/bamboo/logs/comscore_census_cat_file_status.log
CENSUS_SQLFILE=/home/bamboo/devops/comscore-scripts/comscore_census_daily_file_status.sql
CS_CAT_SQLFILE=/home/bamboo/devops/comscore-scripts/comscore_cs_cat_daily_file_status.sql
CA_CENSUS_SQLFILE=/home/bamboo/devops/comscore-scripts/comscore_census_ca_daily_file_status.sql
CA_CS_CAT_SQLFILE=/home/bamboo/devops/comscore-scripts/comscore_cs_cat_ca_daily_file_status.sql
UK_CENSUS_SQLFILE=/home/bamboo/devops/comscore-scripts/comscore_census_uk_daily_file_status.sql
UK_CS_CAT_SQLFILE=/home/bamboo/devops/comscore-scripts/comscore_cs_cat_uk_daily_file_status.sql

#Encrypt and Decrypt password with AWS KMS
key_id='alias/secrets'
ciphertext_blob_path=/home/bamboo/.credentials
username=awsreporting

passphrase=$(/usr/local/bin/aws --region us-east-1 kms decrypt  --ciphertext-blob fileb://$ciphertext_blob_path/$username --query Plaintext --output text | base64 --decode) || exit 1

export PGPASSWORD="$passphrase" || exit 1
echo -e "\n" > $LOGFILE
echo -e "Here is the status of COMSCORE DMP Data loaded into the DSDK for the last 5 days\n" >> $LOGFILE
echo -e "What to See?  column visit_date should have yesterday's date and column day_differences should be 1. If there is any mismatch please see the Troubleshooting Steps section here - https://annalect.atlassian.net/wiki/display/AIO/COMSCORE+-+DMP\n" >> $LOGFILE

echo "COMSCORE CENSUS DATA FOR US" >> $LOGFILE
echo -e "_________________________\n" >> $LOGFILE
psql -h dsdk-v0p1-annalect.clf6bikxcquu.us-east-1.redshift.amazonaws.com -U $username -d dsdk -p 5439 -q -f $CENSUS_SQLFILE >> $LOGFILE || exit 1
echo -e "\n" >> $LOGFILE
echo "COMSCORE CS CAT DATA FOR US" >> $LOGFILE
echo -e "_________________________\n" >> $LOGFILE
psql -q -h dsdk-v0p1-annalect.clf6bikxcquu.us-east-1.redshift.amazonaws.com -U $username -d dsdk -p 5439 -f $CS_CAT_SQLFILE >> $LOGFILE || exit 1

echo "COMSCORE CENSUS DATA FOR CA" >> $LOGFILE
echo -e "_________________________\n" >> $LOGFILE
psql -h dsdk-v0p1-annalect.clf6bikxcquu.us-east-1.redshift.amazonaws.com -U $username -d dsdk -p 5439 -q -f $CA_CENSUS_SQLFILE >> $LOGFILE || exit 1
echo -e "\n" >> $LOGFILE
echo "COMSCORE CS CAT DATA FOR CA" >> $LOGFILE
echo -e "_________________________\n" >> $LOGFILE
psql -q -h dsdk-v0p1-annalect.clf6bikxcquu.us-east-1.redshift.amazonaws.com -U $username -d dsdk -p 5439 -f $CA_CS_CAT_SQLFILE >> $LOGFILE || exit 1

echo "COMSCORE CENSUS DATA FOR UK" >> $LOGFILE
echo -e "_________________________\n" >> $LOGFILE
psql -h dsdk-v0p1-annalect.clf6bikxcquu.us-east-1.redshift.amazonaws.com -U $username -d dsdk -p 5439 -q -f $UK_CENSUS_SQLFILE >> $LOGFILE || exit 1
echo -e "\n" >> $LOGFILE
echo "COMSCORE CS CAT DATA FOR UK" >> $LOGFILE
echo -e "_________________________\n" >> $LOGFILE
psql -q -h dsdk-v0p1-annalect.clf6bikxcquu.us-east-1.redshift.amazonaws.com -U $username -d dsdk -p 5439 -f $UK_CS_CAT_SQLFILE >> $LOGFILE || exit 1

mail -s "(MustSee)COMSCORE : redshift dsdk file status" $EMAIL < $LOGFILE || exit 1
