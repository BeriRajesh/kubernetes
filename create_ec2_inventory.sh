#!/bin/bash
SHELL=/bin/bash PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
week_day=`date +"%a"`
output=text
output=${output:-table}
REGIONS=eu-west-1,sa-east-1,us-east-1,us-west-1,us-west-2,ap-northeast-1,ap-southeast-1,ap-southeast-2
DEFAULT_REGION=us-east-1
profile=${region:-$DEFAULT_REGION}
output_file=/home/bamboo/devops/ec2_inventory_${week_day}.xls

echo "Updated on `date +"%m-%d-%Y"`"  > $output_file
echo "EC2 Instance	PrivateIpAddress	PublicIpAddress	AWS -AZ	InstanceId	Tag:Application	Tag:ENV	Tag:Project	Tag:Tower	ServiceGroup	Layer	InstanceType	InstanceState" >> $output_file

awscommand=`which aws`

region=us-east-1
profile=${region:-$DEFAULT_REGION}
aws --region $region ec2 describe-instances --query 'Reservations[].Instances[].[Tags[?Key==`Name`].Value | [0],PrivateIpAddress, PublicIpAddress, Placement.AvailabilityZone, InstanceId,Tags[?Key==`Application`].Value | [0], Tags[?Key==`Environment`].Value | [0], Tags[?Key==`Project`].Value | [0], Tags[?Key==`tower`].Value | [0], Tags[?Key==`ServiceGroup`].Value | [0], Tags[?Key==`Layer`].Value | [0], InstanceType, State.Name]' --output $output >> $output_file

region=eu-west-1
profile=${region:-$DEFAULT_REGION}
aws  --region $region ec2 describe-instances --query 'Reservations[].Instances[].[Tags[?Key==`Name`].Value | [0],PrivateIpAddress, PublicIpAddress, Placement.AvailabilityZone, InstanceId,Tags[?Key==`Application`].Value | [0], Tags[?Key==`Environment`].Value | [0], Tags[?Key==`Project`].Value | [0], Tags[?Key==`tower`].Value | [0], Tags[?Key==`ServiceGroup`].Value | [0], Tags[?Key==`Layer`].Value | [0], InstanceType, State.Name]' --output $output >> $output_file

#Upload to S3
aws s3 --region us-east-1 --quiet cp $output_file s3://Technical_Infrastructure/AWS-INVENTORY/
