#!/bin/bash
if [  "$1" == "help" ] ; then
  echo "USAGE:";
  echo "       mysqldumpbackup.sh Name MyHOST "
  echo 
  echo "       Name:   The target RDS Name.";
  echo 
  echo "       MyHOST: The target RDS Endpoint.";
  exit 1
fi

if [ "$#" -lt 2 ] ; then
	echo
	echo "Wrong number of Required Parameters [$#].";
	echo "run: ./mysqldumpbackup help for more information";
	echo
	exit 1;
fi

MyUSER="BACKUPUSER"
#Decrypt password with AWS KMS
key_id='alias/secrets'
ciphertext_blob_path=/home/bamboo/.credentials
MyPASS=$(/usr/local/bin/aws --region us-east-1 kms decrypt  --ciphertext-blob fileb://$ciphertext_blob_path/$MyUSER --query Plaintext --output text | base64 --decode)

MyHOST=${1}
DB=${2}

# Linux bin paths, change this if it can't be autodetected via which command
MYSQL="$(which mysql)"
MYSQLDUMP="$(which mysqldump)"
CHOWN="$(which chown)"
CHMOD="$(which chmod)"
GZIP="$(which gzip)"
MKDIR="$(which mkdir)"

# Backup Dest directory, change this if you have someother location
MBD=`$MKDIR -p /backup/mysql-backup/dumps`
DIR="/backup/mysql-backup/dumps"

FILE=""$DIR"/"$DB".sql.gz"
echo $FILE
$MYSQLDUMP -u $MyUSER -h $MyHOST -p$MyPASS $DB --single-transaction > $FILE

echo $DIR
