#!/bin/bash

output_file=./Inventories/ELB_Inventory.csv
echo "Name,DNS name,State,VPC ID,Availability Zones,Type,Created At" >> $output_file

REGIONS=$(nohup aws ec2 describe-regions --query "Regions[].{Name:RegionName}" --output text);
regions=$(echo $REGIONS | tr " " "\n")
for region in $regions
do
    ELB_ACTIVE=$(nohup aws --region $region elbv2 describe-load-balancers --query 'LoadBalancers[].[LoadBalancerArn]' --output text);
    arr_active=$(echo $ELB_ACTIVE | tr " " "\n")
    for x in $arr_active
    do
        
        name=$(nohup aws --region $region elbv2 describe-load-balancers --load-balancer-arn=$x  --query 'LoadBalancers[].[LoadBalancerName]' --output text);
        dns=$(nohup aws --region $region elbv2 describe-load-balancers --load-balancer-arn=$x  --query 'LoadBalancers[].[DNSName]' --output text);
        state=$(nohup aws --region $region elbv2 describe-load-balancers --load-balancer-arn=$x --query 'LoadBalancers[].[State.Code]' --output text);
        vpc=$(nohup aws --region $region elbv2 describe-load-balancers --load-balancer-arn=$x --query 'LoadBalancers[].[VpcId]' --output text);
        zones=$(nohup aws --region $region elbv2 describe-load-balancers --load-balancer-arn=$x --query 'LoadBalancers[].[AvailabilityZones[*].ZoneName]' --output text);
        type=$(nohup aws --region $region elbv2 describe-load-balancers --load-balancer-arn=$x --query 'LoadBalancers[].[Type]' --output text);
        created=$(nohup aws --region $region elbv2 describe-load-balancers --load-balancer-arn=$x --query 'LoadBalancers[].[CreatedTime]' --output text);
        echo "$name,$dns,$state,$vpc,$zones,$type,$created" >> $output_file  
    done

    ELB_INACTIVE=$(nohup aws --region $region elb describe-load-balancers --query 'LoadBalancerDescriptions[].[LoadBalancerName]' --output text);
    arr_inactive=$(echo $ELB_INACTIVE | tr " " "\n")
    for x in $arr_inactive
    do
        dns=$(nohup aws --region $region elb describe-load-balancers --load-balancer-name=$x  --query 'LoadBalancerDescriptions[].[DNSName]' --output text);
        state=""
        vpc=$(nohup aws --region $region elb describe-load-balancers --load-balancer-name=$x --query 'LoadBalancerDescriptions[].[VPCId]' --output text);
        zones=$(nohup aws --region $region elb describe-load-balancers --load-balancer-name=$x --query 'LoadBalancerDescriptions[].[AvailabilityZones[*]]' --output text);
        type="application"
        created=$(nohup aws --region $region elb describe-load-balancers --load-balancer-name=$x --query 'LoadBalancerDescriptions[].[CreatedTime]' --output text);
        echo "$x,$dns,$state,$vpc,$zones,$type,$created" >> $output_file  
    
    done
done