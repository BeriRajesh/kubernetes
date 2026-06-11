#!/bin/bash
### Check arguments
ENV=$1
dbName=$2
if [ $# -ne 2 ] || [ "$ENV" != "qa" ] && [ "$ENV" != "prod" ] && [ "$ENV" != "dev" ]; then echo "USAGE: mongo_dump [ dev | qa | prod ] DatabaseName." 
echo "Example: /root/utility_scripts/mongo_dump dev assembly"; exit; fi
if [[ $dbName = "" ]]; then  echo "No Database Name provided, Usage: mongo_dump [ dev | qa | prod ] DatabaseName." 
echo "Example: /root/utility_scripts/mongo_dump dev assembly"; exit; fi

#DEV_NODE="mon1-db-z1a-de"
USER=root

#Decrypt password with AWS KMS
key_id='alias/secrets'
ciphertext_blob_path=/home/bamboo/.credentials
PASS=$(/usr/local/bin/aws --region us-east-1 kms decrypt  --ciphertext-blob fileb://$ciphertext_blob_path/$USER --query Plaintext --output text | base64 --decode)

HOST=${ENV-NODE}
D=`date +%Y-%m-%d`
yest=`date +%Y-%m-%d --date '1 days ago'`
RestorePath=/backup/mongodbbackup/$ENV/$D
case "$1" in
dev)
NODE="mon1-db-z1a-de.annalectww.com"
;;
qa)
NODE="mongo-n1-db-z1a-qa.annalectww.com"

;;
prod)
NODE="mongo-n1-db-z1a-pr.annalectww.com"
    ;;
    *)
    echo "Please enter a valid environment argument"
    echo "USAGE: mongo_dump [ dev | qa | prod ] DatabaseName"
    exit
esac
if [ "$ENV" == dev ]; then
mkdir -p $RestorePath
mongodump --host $NODE --port 27017 --db $dbName --authenticationDatabase "admin" --out $RestorePath/
else
mkdir -p $RestorePath
mongodump --host $NODE --port 27017 --db $dbName --username $USER --password $PASS --authenticationDatabase "admin" --out $RestorePath/
fi

aws s3 --recursive cp /backup/mongodbbackup/dev/"$D" s3://annalect-backups/Mongo/Dev/"$D"
aws s3 --recursive cp /backup/mongodbbackup/prod/"$D" s3://annalect-backups/Mongo/Prod/"$D"
aws s3 --recursive cp /backup/mongodbbackup/qa/"$D" s3://annalect-backups/Mongo/QA/"$D"


