#!/bin/bash
HOST="anlctprod-mssql-01.c488xyottj77.us-east-1.rds.amazonaws.com"
DB="empowerid"
USER="aok.reporting"
SCRIPT=/home/bamboo/png-scripts/aip-reporting.sql
OUTPUT=/home/bamboo/png-scripts/PG-AIP-Reporting.csv
LOGFILE=/home/bamboo/logs/png-aip-reporting.log

key_id='alias/secrets'
ciphertext_blob_path=/home/bamboo/.credentials

passphrase=$(/usr/local/bin/aws --region us-east-1 kms decrypt  --ciphertext-blob fileb://$ciphertext_blob_path/$USER --query Plaintext --output text | base64 --decode) || exit 1

sqlcmd -S $HOST -d $DB -U $USER -P $passphrase -i $SCRIPT -o $OUTPUT -W -s"," -w 1024 -m 1 > $LOGFILE || exit 1
/usr/local/bin/aws s3 cp $OUTPUT s3://procter-gamble-prod/aip_report/ --sse AES256 || exit 1
