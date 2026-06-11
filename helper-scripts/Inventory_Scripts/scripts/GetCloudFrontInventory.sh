#!/bin/bash
output_file=./Inventories/CF_Inventory.csv
echo 'Delivery Method,CloudFront_ID,Domain-Name,Comment,Origin,CNAME,STATUS,STATE,LAST MODIFIED' >> $output_file
DOMAINS=$(nohup aws cloudfront list-distributions --query 'DistributionList.Items[].[Id]'  --output=text);

arr=$(echo $DOMAINS | tr " " "\n")
for x in $arr
do
    id=$(nohup aws cloudfront get-distribution --id $x --query 'Distribution.Id' --output=text);
    domainname=$(nohup aws cloudfront get-distribution --id $x --query 'Distribution.DomainName' --output=text);
    comment=$(nohup aws cloudfront get-distribution --id $x --query 'Distribution.DistributionConfig.Comment' --output=text);
    oorigins=$(nohup aws cloudfront get-distribution --id $x --query 'Distribution.DistributionConfig.Origins.Items[*].DomainName' --output=text);
    ocnames=$(nohup aws cloudfront get-distribution --id $x --query 'Distribution.DistributionConfig.Aliases.Items[*]' --output=text);
    status=$(nohup aws cloudfront get-distribution --id $x --query 'Distribution.Status' --output=text);
    ostate=$(nohup aws cloudfront get-distribution --id $x --query 'Distribution.DistributionConfig.Enabled' --output=text);
    if [ $ostate ]; then
    fstate="Enabled"
    else
    fstate="Disabled"
    fi
    lmdate=$(nohup aws cloudfront get-distribution --id $x --query 'Distribution.LastModifiedTime' --output=text);
    echo "WEB,$id,$domainname,$comment,$oorigins,$ocnames,$status,$fstate,$lmdate" >> $output_file
done
echo "Exported The List of CloudFront Distributions Successfully"

