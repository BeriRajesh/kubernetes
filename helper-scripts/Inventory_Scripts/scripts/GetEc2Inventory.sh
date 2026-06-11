#!/bin/bash
output_file=./Inventories/EC2_Inventory.csv
echo "EC2Instance	InstanceId	InstanceType	Availability Zone	Instance-State	Private-Ip-Address	Public-Ip-address	if-EBS-Optimised	VPC ID	Subnet ID	Image-ID	Tag:Application	Tag:Patch Group	Tag:ServiceGroup	Tag:Environment	Tag:Monitoring	Tag:Project	Tag:Tower	Tag:Description	Tag:Business Unit	Tag:Cost Center" >> $output_file
REGIONS=$(nohup aws ec2 describe-regions --query "Regions[].{Name:RegionName}" --output text);
regions=$(echo $REGIONS | tr " " "\n")
for region in $regions
do
aws --region $region ec2 describe-instances --query 'Reservations[].Instances[].[Tags[?Key==`Name`].Value | [0],InstanceId,InstanceType,Placement.AvailabilityZone,State.Name,PrivateIpAddress,PublicIpAddress,EbsOptimized,VpcId,SubnetId,ImageId,Tags[?Key==`Application`].Value | [0],Tags[?Key==`Patch Group`].Value | [0],Tags[?Key==`ServiceGroup`].Value | [0],Tags[?Key==`Environment`].Value | [0],Tags[?Key==`Monitoring`].Value | [0],Tags[?Key==`Project`].Value | [0],Tags[?Key==`tower`].Value | [0],Tags[?Key==`Description`].Value | [0],Tags[?Key==`Business Unit`].Value | [0],Tags[?Key==`Cost Center`].Value | [0]]' --output text >> $output_file
done
