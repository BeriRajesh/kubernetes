#!/bin/bash

# write stdout and stderr to syslog, using logger.
# taken from: http://urbanautomaton.com/blog/2014/09/09/redirecting-bash-script-output-to-syslog/
exec 1> >(logger -s -t $(basename $0)) 2>&1

# my process id (PID)
mypid=$$

# killing running process of this script, except myself
for p in $(pgrep -f -l $(basename $0) | grep -v $$ | grep -v $mypid | grep -v "vim" | grep -v "logger" | awk '{print $1}')
do
    if ps ax | grep -v grep | grep -q $p
    then
        kill -9 $p
    fi
done

# check dependencies
INOTIFYWAIT_BINARY=$(which inotifywait)

if [ -z "$INOTIFYWAIT_BINARY" ]
then
        echo "ERROR: Please install inotify-tools package and restart the script"
        exit 1
fi

PATHTOWATCH='/var/www/annalectno/wp-content/uploads'

echo "Watching '$PATHTOWATCH' for new files, and syncronizing them to S3"

inotifywait -mr --timefmt '%d/%m/%y %H:%M' --format '%T %w %f' \
-e close_write $PATHTOWATCH | while read date time dir file; do

       FILECHANGE=${dir}${file}
       # convert absolute path to relative
       FILECHANGEREL=`echo "$FILECHANGE" | sed 's_/var/www/[^/]*/__'`

       aws --region eu-west-1 s3 cp "$FILECHANGE" "s3://assets.annalect.no/$FILECHANGEREL" --sse

done
