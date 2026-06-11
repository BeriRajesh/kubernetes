#!/bin/bash

echo "===hostname==="
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
echo "===java==="
update-alternatives --config java
echo "========= DONE =========="

