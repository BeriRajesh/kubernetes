#!/bin/bash
#generating Hostname
        USER_DATA_URL=http://169.254.169.254/latest/user-data
#Applied fix provided by Shashi
        sudo wget -O /user-data $USER_DATA_URL
	# Take first 12 characters of the Application
	# Modified by Satish
        APP_NAME=`grep "APP_NAME" /user-data |  cut -d "=" -f2 | cut -c1-12`
        SVC_NAME=`grep "SVC_NAME" /user-data |  cut -d "=" -f2 | cut -c1-2`
        ENV_NAME=`grep "ENV_NAME" /user-data |  cut -d "=" -f2 | cut -c1-2`
if [ -z "$APP_NAME" ] || [ -z "$SVC_NAME" ] || [ -z "$ENV_NAME" ]; then
echo "Please Stop the EC2 Instance, add proper user-data required for generating hostname and re-run script"
exit 1
fi

  IPADDR=`ifconfig eth0 | grep Bcast | cut -d ":" -f2 | cut -d " " -f 1`
  AVAILABILITYZONE=`curl --silent http://169.254.169.254/latest/meta-data/placement/availability-zone`

        echo "$0: Got Availability Zone:$AVAILABILITYZONE"
        echo "Availability Zone : $AVAILABILITYZONE" | logger -s -t "Integration"

        case $AVAILABILITYZONE in
        us-east-1a) PREFIX=$APP_NAME-$SVC_NAME-z1a-$ENV_NAME
                ;;
        us-east-1b) PREFIX=$APP_NAME-$SVC_NAME-z1b-$ENV_NAME
                ;;
       eu-west-1a) PREFIX=$APP_NAME-$SVC_NAME-eu1a-$ENV_NAME
		        ;;
       eu-west-1b) PREFIX=$APP_NAME-$SVC_NAME-eu1b-$ENV_NAME
                ;;
        *)      PREFIX="NONE"
                ;;
        esac


        HOST_NAME=$PREFIX
echo $HOST_NAME
echo $IPADDR
sudo sed -i "2i $IPADDR\t$HOST_NAME" /etc/hosts
h=`hostname`
#Applied fix provided by Shashi
sudo echo $HOST_NAME > /etc/hostname
sudo hostname -F /etc/hostname
