#!/bin/bash

echo " === Verify kernel pinning === "
cat /etc/apt/preferences
sleep 5s
echo " ======================== apt-get update ========================"
apt-get update
echo " ======================== apt-mark hold ======================== "
apt-mark hold linux-headers*
apt-mark hold linux-image*
echo " ======================== mesos,zookeeper & marathon hold ======================== "
apt-mark hold mesos marathon zookeeper
echo " ======================== apt-get dist-upgrade --dry-run ======================== "
apt-get dist-upgrade --dry-run

apt-get dist-upgrade
echo " ======================== dist-upgrade - Patch DONE ======================== "

echo " ======================== Verify apt-get dist-upgrade --dry-run ======================== "
apt-get dist-upgrade --dry-run
echo " ======================== DONE ======================="

