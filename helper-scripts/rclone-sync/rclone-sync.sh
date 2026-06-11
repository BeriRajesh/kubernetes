#!/bin/bash

set -e

# path to the rclone executable
RCLONE_PATH=$(which rclone)

# rclone operation to perform
RCLONE_OPERATION="copy"

# extra params for rclone in case they are needed
RCLONE_EXTRAPARAMS="--no-traverse -v"

# rclone must have the remotes already configured (usually in /etc/rclone.conf)
DESTINATION_REMOTE="s3env"
SOURCE_REMOTE="annalectftp"

# checking the existence of the configuration for the remotes
for remote in $DESTINATION_REMOTE $SOURCE_REMOTE
do
    if ! rclone listremotes |  grep -q $remote
    then
        echo "Error: remote $remote is not configured. Please configure using 'rclone config'"
        exit 1
    fi

done

# source and destination paths
SOURCE_PATH="/Usr/omg-agencies/heartsscience/att/attbusiness/from_att"
DESTINATION_PATH="omg-agencies/heartsscience/att/attbusiness/from_att"

# if any parameter is passed to the script, then it exexutes in --dry-run mode and no changes are made
DRY_RUN=""
if [ ! -z $1 ]
then
    DRY_RUN="--dry-run"
fi

if [ -z RCLONE_PATH ]
then
    echo "rclone apparently not installed, output of `which rclone` was empty."
fi


COMMAND="$RCLONE_PATH $RCLONE_OPERATION $RCLONE_EXTRAPARAMS $DRY_RUN $SOURCE_REMOTE:$SOURCE_PATH $DESTINATION_REMOTE:$DESTINATION_PATH"

echo "Executing command:"
echo $COMMAND

RESULT=$($COMMAND)

echo
echo "executed command:"
echo $COMMAND

if [ ! $? -eq 0 ]
then
  echo "There was an error" >&2
  exit 1
fi
