#!/bin/bash

#set -x

# write stdout and stderr to syslog, using logger.
# taken from: http://urbanautomaton.com/blog/2014/09/09/redirecting-bash-script-output-to-syslog/
# exec 1> >(logger -s -t $(basename $0)) 2>&1

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
	exit;
fi

echo "Starting backup of ${1} ..."

MyUSER="BACKUPUSER"

#Decrypt password with AWS KMS
key_id='alias/secrets'
ciphertext_blob_path=/home/bamboo/.credentials
MyPASS=$(/usr/local/bin/aws --region us-east-1 kms decrypt  --ciphertext-blob fileb://$ciphertext_blob_path/$MyUSER --query Plaintext --output text | base64 --decode)

#Name=${1:-"pipeline-dev"}
Name=${1}
MyHOST=${2}

# Linux bin paths, change this if it can't be autodetected via which command
MYSQL="$(which mysql)"
MYSQLDUMP="$(which mysqldump)"
CHOWN="$(which chown)"
CHMOD="$(which chmod)"
GZIP="$(which gzip)"
MKDIR="$(which mkdir)"
TODAY="$(date -I)"
Yest=`date -I --date '1 days ago'`

# Backup Dest directory, change this if you have someother location
DIR="/backup/mysql-backup/"$Name"/"$TODAY""
MBD=`$MKDIR -p ${DIR}`

# Get data n dd-mm-yyyy format
NOW=$TODAY #"$(date +"%d-%m-%Y")"

# File to store current backup file
FILE=""
# Store list of databases
DBS=""

# DO NOT BACKUP these databases
IGGY="tmp information_schema performance_schema mysql sys"

if [ ! -d $DIR ]
then
    mkdir -p ${DIR}
fi

# Only root can access it!
#$CHMOD 0600 "MBD"

# Get all database list first
DBS="$($MYSQL -u $MyUSER -h $MyHOST -A -p$MyPASS -Bse 'show databases')"
for db in $DBS
do
    skipdb=-1
    if [ "$IGGY" != "" ];
    then
        for i in $IGGY
        do
            [ "$db" == "$i" ] && skipdb=1 || :
        done
    fi

    if [ "$skipdb" == "-1" ] ; then
        FILE=""$DIR"/"$Name"-$db-$NOW.sql"

        echo " Doing backup of ${db}..."

        time $MYSQLDUMP -u $MyUSER -h $MyHOST -p$MyPASS $db --single-transaction > $FILE

        echo "   ... finished backup of ${db}..."


        # do all inone job in pipe,
        # connect to mysql using mysqldump for select mysql database
        # and pipe it out to gz file in backup dir :)
        echo "   Compressing backup ..."
        # nice $GZIP $FILE || true
        $GZIP $FILE || true
        FILE="${FILE}.gz"
        echo "   ... finished compressing backup"

    else
        echo "   Skipping ${db}"
    fi
done

#s3cmd put -r "$DIR"  s3://Oracle_MYSQL_Backup/MYSQL_BACKUP/"$Name"/
#s3cmd put -r "$DIR"  s3://annalect-backups/RDS/MYSQL_BACKUP/"$Name"/
echo Executing: aws s3 cp --recursive "$DIR"  s3://annalect-backups/RDS/MYSQL_BACKUP/"${Name}"/"${TODAY}"/

aws s3 cp --recursive "$DIR"  s3://annalect-backups/RDS/MYSQL_BACKUP/"${Name}"/"${TODAY}"/
#aws s3  "$DIR"  s3://annalect-backups/RDS/MYSQL_BACKUP/"$Name"/

echo Executing: find /backup/mysql-backup/"${Name}"/"${TODAY}" -type d -exec rm -rf {} \;
find /backup/mysql-backup/"${Name}"/"${TODAY}" -type d -exec rm -rf {} \; || true

#END
