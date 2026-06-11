#!/usr/bin/env bash

echo " === Verify kernel pinning === "
cat /etc/apt/preferences
sleep 5s
echo " ======================== apt-get update ========================"
apt-get update
echo " ======================== apt-mark hold ======================== "
apt-mark hold linux-headers*
apt-mark hold linux-image*
echo " === performing patching === "
apt-get dist-upgrade
echo "========= DONE =========="


