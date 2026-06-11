#!/usr/bin/env bash 

echo "Welcome to Inventory Generation"
echo "Inventory generation will take quite a bit of time. Please be patient..."
echo "Deleting old Inventories"
rm -rf ./Inventories/*.csv

echo "Exporting Ec2 Inventories is in progress.........."
sh ./scripts/GetEc2Inventory.sh
echo "Successfully Exported the EC2 Inventories"

echo "Exporting RedShift Inventories is in progress........."
sh ./scripts/GetRedShiftInventory.sh
echo "Successfully Exported the RedShift Inventories"

echo "Exporting RDS Inventories is in progress........"
sh ./scripts/GetRDSInventory.sh
echo "Successfully Exported the RDS Inventories"

echo "Exporting ELB Inventories is in progress........"
sh ./scripts/GetELBInventory.sh
echo "Successfully Exported the ELB Inventories"

echo "Exporting CloudFront Inventories is in progress........"
sh ./scripts/GetCloudFrontInventory.sh
echo "Successfully Exported the CloudFront Inventories"

echo "All Scrips ran Successfully and Inventories are generated......."
echo "Thank you for your patience"

echo "Have a great day"