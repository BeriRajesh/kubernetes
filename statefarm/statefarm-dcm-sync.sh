#!/bin/bash
#EMAIL="shailaja.gadupu@annalect.com"
EMAIL="annalecttio@annalect.com john.briscoe@annalect.com"
LOGFILE=/home/bamboo/logs/statefarm-dcm.log

alias gsutil-statefarm=BOTO_CONFIG=$HOME/.boto-dcm-9724\ gsutil

echo "Starting the sync from google bucket:cdt_-dcm_account9724/ to s3 bucket:omg-agencies/omd/statefarm/dcm\n" > $LOGFILE || exit 1

gsutil-statefarm -m rsync -r gs://dcdt_-dcm_account9724/ s3://omg-agencies/omd/statefarm/dcm >> $LOGFILE

echo "Sync completed" >> $LOGFILE || exit 1
mail -s "StateFarm DCM Sync status" $EMAIL < $LOGFILE || exit 1
