#!/bin/bash
output_file=./Inventories/RedShift_Inventory.csv
#echo "Cluster-Name	Endpoint	Port	Node	No-of-Nodes	Zone	Cluster-Parameter	Cluster-Subnet-Group	Enhanced-VPC-Routing	Cluster-Status	Preferred-Maintenance-Window	Parameter-Group-Apply-Status	Database-Name	Master-User-name	Encrypted	Automated-Snapshot-Retention-Period	Allow-Version-Upgrade	Project	Environment	Name	Client	Agency	Usage" >> $output_file
echo "ClusterIdentifier	Endpoint	Address Port	DBName	NodeType	MasterUsername	AvailabilityZone	NumberOfNodes	ClusterAvailabilityStatus	VpcId	PubliclyAccessible	Encrypted	ClusterStatus	ClusterSubnetGroupName	SnapshotRetentionPeriod	EnhancedVpcRouting	PreferredMaintenanceWindow	VpcSecurityGroupId	ParameterGroupName	ParameterApplyStatus	PrivateIPAddress	NodeRole	PublicIPAddress	AutomatedSnapshotRetentionPeriod	AllowVersionUpgrade	Project	Environment	Name	Client	Agency	Usage" >> $output_file
#REGIONS=$(nohup aws ec2 describe-regions --query "Regions[].{Name:RegionName}" --output text);
#regions=$(echo $REGIONS | tr " " "\n")
regions="us-east-1 eu-west-1"
for region in $regions
do
aws --region $region redshift describe-clusters --query 'Clusters[].[ClusterIdentifier,Endpoint.Address,Endpoint.Port,DBName,NodeType,MasterUsername,AvailabilityZone,NumberOfNodes,ClusterAvailabilityStatus,VpcId,PubliclyAccessible,Encrypted,ClusterStatus,ClusterSubnetGroupName,ClusterSnapshotCopyStatus[0].RetentionPeriod,EnhancedVpcRouting,PreferredMaintenanceWindow,VpcSecurityGroups[0].VpcSecurityGroupId,ClusterParameterGroups[0].ParameterGroupName,ClusterParameterGroups[0].ParameterApplyStatus,ClusterNodes[0].PrivateIPAddress,ClusterNodes[0].NodeRole,ClusterNodes[0].PublicIPAddress,AutomatedSnapshotRetentionPeriod,AllowVersionUpgrade,Tags[?Key==`Project`].Value | [0],Tags[?Key==`Environment`].Value | [0],Tags[?Key==`Name`].Value | [0],Tags[?Key==`Client`].Value | [0],Tags[?Key==`Agency`].Value | [0],Tags[?Key==`Usge`].Value | [0]]' --output text >> $output_file
done



