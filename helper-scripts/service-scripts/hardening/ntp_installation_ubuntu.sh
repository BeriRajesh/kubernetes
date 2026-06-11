#Install ntp..
sudo apt-get -y install ntp
sudo sysv-rc-conf --level 2345 ntpd on
sudo service ntp stop

REGION=`curl -s http://169.254.169.254/latest/dynamic/instance-identity/document|grep region|awk -F\" '{print $4}'`
echo "$0: Got AWS Region:$REGION"
case $REGION in
eu-west-1)
sudo awk '/server [0-9].ubuntu.pool.ntp.org/{gsub(/server/, "#server")};{print}' /etc/ntp.conf > /tmp/ntp.conf.1
sudo awk '/server ntp.ubuntu.com/{gsub(/server/, "#server")};{print}' /tmp/ntp.conf.1 > /tmp/ntp.conf.2
sudo awk '/#server ntp.ubuntu.com/{gsub(/$/, "\nserver 10.8.48.148 iburst\nserver ad-ds-pr-mgmt.annalectww.com iburst\nserver ad-ds-fl-mgmt.annalectww.com iburst\nserver ntp.ubuntu.com")};{print}' /tmp/ntp.conf.2 > /tmp/ntp.conf.3
sudo awk '!x[$0]++' /tmp/ntp.conf.3 > /tmp/ntp.conf.4
sudo cp /tmp/ntp.conf.4 /etc/ntp.conf
;;
us-east-1)
sudo awk '/server [0-9].ubuntu.pool.ntp.org/{gsub(/server/, "#server")};{print}' /etc/ntp.conf > /tmp/ntp.conf.1
sudo awk '/server ntp.ubuntu.com/{gsub(/server/, "#server")};{print}' /tmp/ntp.conf.1 > /tmp/ntp.conf.2
sudo awk '/#server ntp.ubuntu.com/{gsub(/$/, "\nserver ad-ds-pr-mgmt.annalectww.com iburst\nserver ad-ds-fl-mgmt.annalectww.com iburst\nserver ntp.ubuntu.com")};{print}' /tmp/ntp.conf.2 > /tmp/ntp.conf.3
sudo awk '!x[$0]++' /tmp/ntp.conf.3 > /tmp/ntp.conf.4
sudo cp /tmp/ntp.conf.4 /etc/ntp.conf
;;
*)      PREFIX="NONE"
;;
esac
sudo rm -rf /tmp/ntp.conf.*
#start ntp service...
sudo service ntp start
