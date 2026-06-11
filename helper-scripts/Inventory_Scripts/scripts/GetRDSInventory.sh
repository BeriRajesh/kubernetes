#!/bin/bash

output_file=./Inventories/RDS_Inventory.csv

#echo "DB-instance	DB-cluster-identifier	Engine	Engine-version	Status	Preferred-Backup-Window	Class	VPC	Multi-AZ-Support	Storage-type	Storage-Space(Gib)	Zone	DB-subnet-group-name	Character-set	Option-group	Created-time	If-Storage-Encrypted	End-Point" >> $output_file
echo "DBInstanceIdentifier	DBInstanceClassEngine	DBInstanceStatus	MasterUsername	DBName	Endpoint.address	Endpoint.port	AllocatedStorage	InstanceCreateTime	PreferredBackupWindow	BackupRetentionPeriod	DBSecurityGroups	VpcSecurityGroupId	status	DBParameterGroupName	ParameterApplyStatus	AvailabilityZone	DBSubnetGroupName	DBSubnetGroupDescription	VpcId	SubnetGroupStatus	SubnetIdentifier	Name	SubnetStatus	PreferredMaintenanceWindow	MultiAZ	EngineVersion	AutoMinorVersionUpgrade	ReadReplicaDBInstanceIdentifiers	OptionGroupName	Status	PubliclyAccessible	StorageType	DbInstancePort	DBClusterIdentifier	StorageEncrypted	KmsKeyId	DbiResourceId	CACertificateIdentifier	CopyTagsToSnapshot	IAMDatabaseAuthenticationEnabled	PerformanceInsightsEnabled	DeletionProtection	EnabledCloudwatchLogs1	EnabledCloudwatchLogs2" >> $output_file
#REGIONS=$(nohup aws ec2 describe-regions --query "Regions[].{Name:RegionName}" --output text);
#regions=$(echo $REGIONS | tr " " "\n")
regions="us-east-1 eu-west-1"
for region in $regions 
do
aws --region $region rds describe-db-instances --query 'DBInstances[].[DBInstanceIdentifier,	DBInstanceClass, DBInstanceStatus,	MasterUsername,	DBName,	Endpoint.Address,	Endpoint.Port,	AllocatedStorage,	InstanceCreateTime,	PreferredBackupWindow,	BackupRetentionPeriod,	DBSecurityGroups[0],	VpcSecurityGroups[0].VpcSecurityGroupId,	VpcSecurityGroups[0].Status,	DBParameterGroups[0].DBParameterGroupName,	DBParameterGroups[0].ParameterApplyStatus,	AvailabilityZone,	DBSubnetGroup.DBSubnetGroupName,	DBSubnetGroup.DBSubnetGroupDescription,	DBSubnetGroup.VpcId,	DBSubnetGroup.SubnetGroupStatus,	DBSubnetGroup.Subnets[0].SubnetIdentifier,	DBSubnetGroup.Subnets[0].SubnetAvailabilityZone.Name,	DBSubnetGroup.Subnets[0].Subnets.SubnetStatus,	PreferredMaintenanceWindow,	MultiAZ,	EngineVersion,	AutoMinorVersionUpgrade,	ReadReplicaDBInstanceIdentifiers[0],	OptionGroupMemberships[0].OptionGroupName,	OptionGroupMemberships[0].Status,	PubliclyAccessible,	StorageType,	DbInstancePort,	DBClusterIdentifier,	StorageEncrypted,	KmsKeyId,	DbiResourceId,	CACertificateIdentifier,	CopyTagsToSnapshot,	IAMDatabaseAuthenticationEnabled,	PerformanceInsightsEnabled,DeletionProtection,EnabledCloudwatchLogsExports[0],EnabledCloudwatchLogsExports[1]]' --output text >> $output_file
done

