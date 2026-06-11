"""
Example usage:
python cloudEmail_sesRules_s3Event_setup.py --dest_s3_path=s3://omg-agencies/omd/wellsfargo/trueview --cloudemail=shashi@annalect.cloud
"""
import boto3
import json
import argparse
import datetime
from StringIO import StringIO
from botocore.client import ClientError

def archive_s3events(topicconfigurations, s3_client):
	
	json_str = json.dumps({u'TopicConfigurations': topicconfigurations})
	key	     = "s3_events_backup/s3_events_{mmddyyyy}.json".format(
					mmddyyyy = datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S"))
	
	json_file = StringIO(json_str)
			
	s3_client.upload_fileobj(json_file, 'annalectcloudmail', key)
	print("Uploaded existing event configuration copy into S3 at: s3://annalectcloudmail/%s" % key)


def main(dest_s3_path, cloudemail):
	# Create an SES/S3 client
	s3        = boto3.resource('s3', region_name='us-east-1')
	client    = boto3.client('ses', region_name='us-east-1')
	s3_client = boto3.client('s3', region_name='us-east-1')
	
	#Filter bucket and prefix from dest_s3_path
	dbp = dest_s3_path
	
	if dbp.startswith('s3://'): dbp = dbp[5:]
	if dbp.startswith('/'): dbp = dbp[1:]
	if dbp.endswith('/'): dbp = dbp[:-1]
	
	p      			 = dbp.split('/')
	destbucket 		 = p[0]
	destbucketprefix = '/'.join(p[1:])
	
	bucket = s3.Bucket(destbucket)
     
	try: s3.meta.client.head_bucket(Bucket=bucket.name)
	except ClientError:
		print("Dest S3 Bucket named %s does not exist, please provide valid s3 bucket" % bucket.name)
		exit()
	
	#Filter cloudemail for ses_rulename
	s	= cloudemail.split('@')
	ses_rule_name= s[0]
	
	print("dest_bucket="+ destbucket)
	print("dest_bucket_prefix="+ destbucketprefix)
	print("cloud_email="+ cloudemail)
	print("dest_s3_path_to_store_data="+ dest_s3_path)
	print("ses_rule_name="+ ses_rule_name)
	
	#srcbucket 		    = 'adwdev' 	# Source S3 bucket to store incoming RAW SES email
	#sns_arn_topic		= 'arn:aws:sns:us-east-1:661095214357:Shashi'
	#Variables
	srcbucket 		    = 'annalectcloudmail' 	# Source S3 bucket to store incoming RAW SES email
	sns_arn_topic		= 'arn:aws:sns:us-east-1:661095214357:annalectcloudemail'
	#ses_rulename 		= 'shashik' 		#Name of SES Rule
	#cloudemail	   		= ['shashik@annalect.cloud', 'shashi@annalect.cloud']   #Recipient for the rule
	#destbucket 		= 'omg-agencies'        # Destination S3 Bucket to store attachement(s) or file fro URL's
	#destbucketprefix 	= 'heartsscience/att/foursquare'      # Path of destination S3 Bucket
	#cloudemail        = cloudemail
	
	#Create SES Receipt Rule
	ses_response = client.create_receipt_rule(
	    RuleSetName='default-rule-set',
	    After='spam-filter-rule',
	    Rule={
	        'Name': ses_rule_name,
	        'Enabled': True,
	        'ScanEnabled': True,
	        'TlsPolicy': 'Require',
	        'Recipients': [cloudemail],
	    "Actions": [
	            {
	                "AddHeaderAction": {
	                    "HeaderName": "destbucket", 
	                    "HeaderValue": destbucket
	                }
	            }, 
	            {
	                "AddHeaderAction": {
	                    "HeaderName": "destbucketprefix", 
	                    "HeaderValue": destbucketprefix
	                }
	            }, 
	            {
	                "S3Action": {
	                    "ObjectKeyPrefix": '{destbucket}/{destbucketprefix}/mail'.format(destbucket=destbucket,destbucketprefix=destbucketprefix), 
	                    "BucketName": srcbucket
	                }
	            }
	        ] 
	    }
	)
	
	#Configure S3 Event 
	s3_event = {
	                'Id': cloudemail,
	                'TopicArn': sns_arn_topic,
	                'Events': [
	                    's3:ObjectCreated:*',
	                ],
	                'Filter': {
	                    'Key': {
	                        'FilterRules': [
	                            {
    	                            'Name': 'prefix',
    	                            'Value': '{destbucket}/{destbucketprefix}/mail/'.format(destbucket=destbucket,destbucketprefix=destbucketprefix),
    	                        },
    	                    ]
    	                }
    	            }
    	        }


	bucket_notification = s3.BucketNotification(srcbucket)	
	
	data = s3_client.get_bucket_notification_configuration(
    				Bucket=srcbucket
				)
				
	topicconfigurations = data[u'TopicConfigurations']
	
	archive_s3events(topicconfigurations, s3_client)
	
	print("numberOfs3EventsBefore: " + str(len(topicconfigurations)))
	
	topicconfigurations.append(s3_event)
	
	s3_response = bucket_notification.put(
			NotificationConfiguration={
			'TopicConfigurations': topicconfigurations
				}
			)
	
	data_after = s3_client.get_bucket_notification_configuration(
    				Bucket=srcbucket
				)
				
	topicconfigurations_after = data[u'TopicConfigurations']
	print("numberOfs3EventsAfter: " + str(len(topicconfigurations)))
	

if __name__ == '__main__':
	parser = argparse.ArgumentParser(
			description='Manage CloudEmail SES Rules and S3 Event Notifications setup')
    
	parser.add_argument('--dest_s3_path', dest='dest_s3_path', required=True,
        	             help='Name of the dest S3 path to save data')
	parser.add_argument('--cloudemail', dest='cloudemail', required=True,
   	 	                 help='annalectcloud email address')

	args = parser.parse_args()
    
	main(args.dest_s3_path, args.cloudemail)

