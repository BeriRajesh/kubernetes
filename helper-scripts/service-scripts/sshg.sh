#!/bin/bash

keyspath=~/keys/*.pem

if [ -z "$2" ]; then
        echo Connecting to $1 ...
fi

for f in $keyspath
do
	# echo $f
        keys="$keys -i $f"
done

ssh -o LogLevel=error -o StrictHostKeyChecking=no ubuntu@$1 $keys "$2"
