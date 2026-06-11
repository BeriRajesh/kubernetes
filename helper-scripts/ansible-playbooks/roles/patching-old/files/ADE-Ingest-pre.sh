#!/usr/bin/env bash

TODAY=`date +"%FT%H%M"`
echo "===hostname===" > pre-patching-"$TODAY".txt
hostname
echo "===uptime==="
uptime
echo "===lsb_release==="
lsb_release -a
echo "===uname==="
uname -msr
echo "===python==="
python -V 2>&1
echo "===filesystem==="
df -h
echo "===netstat==="
netstat -ntplu
echo "===logstash==="
ps -ef|grep logstash
echo "=== Verify logstash is running or not ==="
ps -ef|grep logstash
echo "===java==="
update-alternatives --config java
echo "========= DONE =========="
