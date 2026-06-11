#!/bin/bash
EMAIL="annalecttio@annalect.com"
SQLFILE=/home/bamboo/comscore-scripts/comscore_analyze_tables.sql
LOGFILE=/home/bamboo/logs/comscore_analyze_tables.log


#Encrypt and Decrypt password with AWS KMS
key_id='alias/secrets'
ciphertext_blob_path=/home/bamboo/.credentials
username=awsreporting

passphrase=$(/usr/local/bin/aws --region us-east-1 kms decrypt  --ciphertext-blob fileb://$ciphertext_blob_path/$username --query Plaintext --output text | base64 --decode) || exit 1

export PGPASSWORD="$passphrase" || exit 1
echo -e "Executed Analyze command" >> $LOGFILE
psql -h comscore-procdata-dw2.clf6bikxcquu.us-east-1.redshift.amazonaws.com -U $username -d comscore -p 5439 -q -f $SQLFILE >> $LOGFILE
echo -e "\n" >> $LOGFILE
mail -s "Comscore Analyze command" $EMAIL < $LOGFILE
