#!/usr/bin/env python
"""
Example usage:
python s3_events_restore.py --filename=s3_events_04-22-2017-17-35-33.json
"""
import boto3
import json
import argparse

def main(filename):
	s3_client  = boto3.client('s3')
	s3  	   = boto3.resource('s3')
	
	
	emailsrcbucket = 'annalectcloudmail'
	key		   = 's3_events_backup/' + filename
	
	print(key)
	obj = s3_client.get_object(Bucket='annalectcloudmail', Key=key)
	topicconfigurations = json.loads(obj['Body'].read())
	
	
	
	bucket_notification = s3.BucketNotification(emailsrcbucket)	
				
	s3_response = bucket_notification.put(
			NotificationConfiguration = topicconfigurations
			)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(
			description='Restore S3 bucket event notifications')
    
	parser.add_argument('--filename', dest='filename', required=True,
        	             help='provide json filename to restore back s3 events')

	args = parser.parse_args()
	main(args.filename)