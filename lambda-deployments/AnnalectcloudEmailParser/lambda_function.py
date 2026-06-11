import boto3
import ast
import os
import datetime
import email
import re
import urllib
import urllib2
import urlparse
from boto.s3.key import Key
from urls_extract import get_urls_from_body, url_in_html_code
"""
Gets raw email and extracts the attachments and
any file from URL in the raw email. The attachments
and URL downloads are uploaded to s3, excluding files with extension 
such as 'jpg', 'png', 'jpeg', 'gif', 'html', 'exe' etc
"""

def dict_for_payloads(payloads):
	"""
	Returns a list containing dictionaries, with 
	body and other attributes of the payload.
	"""
	return [{'Content': key.get_payload(decode=True),
			'filename': key.get_filename(),
			'attachment': key.get('Content-Disposition'),
		  	'Content-Type': key.get_content_type()}
			for key in payloads]

def check_mulitpart(payload):
	"""
	Recursive function that checks if a payload
	is multipart, until it is not.
	"""
	if payload.is_multipart():
		for pay in payload.get_payload():
			return check_mulitpart(pay)
	else: 
		return [payload]

def list_of_payloads_charac(msg):
	"""
	Returns a final list that contains dictionaries
	for each payload in the raw email.
	"""
	payloads = msg.get_payload()
	ls = []
	if msg.is_multipart():
		for payload in payloads:
			ls.extend(dict_for_payloads(check_mulitpart(payload)))
	else:
		ls.extend(dict_for_payloads([msg]))
	return ls
	
def upload_to_s3(content, filename, s3, destbucket, destbucketprefix):
	"Uploads files to s3"
	
	open('/tmp/' + filename, 'wb').write(content)
	print("Copying file \"%s\" into S3 bucket..." % filename)
	s3.upload_file('/tmp/' + filename, destbucket, destbucketprefix + '/' + filename)
	print("Successfully uploaded \"%s\" into s3://%s/%s" % (filename, destbucket, destbucketprefix))

def check_ext(filename):
	"""
	Returns False if filename has extension
	'jpg', 'png', 'jpeg' or 'gif'.
	"""
	invalid_file_ext = ['jpg', 'png', 'jpeg', 'gif', 'html', 'exe']
	for ext in invalid_file_ext:
		if ext in filename.split('.')[-1]: 
			return False
	return True
	
def lambda_handler(event, context):
	"""
	Lambda function that gets raw email from s3.
	"""
	s3 = boto3.client('s3')
	sns_message = ast.literal_eval(event['Records'][0]['Sns']['Message'])
	source_bucket = str(sns_message['Records'][0]['s3']['bucket']['name'])
	key = str(urllib.unquote_plus(sns_message['Records'][0]['s3']['object']['key']).decode('utf8'))

	LOCAL_PATH = '/tmp/' + str(key.split("/")[-1])
	print("source_bucket: "+ source_bucket)
	print("source_key: "+ key)

	s3.download_file(source_bucket, key, LOCAL_PATH)

	msg = email.message_from_file(open(LOCAL_PATH))#, mode = 'r', buffering = -1))

	destbucket = msg.get('destbucket')
	destbucketprefix = msg.get('destbucketprefix')

	print("destbucket: " + destbucket)
	print("destbucketprefix: " + destbucketprefix)

	ls = list_of_payloads_charac(msg)
	ls_of_attachments = [(str(dic['Content']), dic['filename']) for dic in ls 
						if dic['attachment'] and dic['Content-Type'].split('/')[0] != 'image']
	
	for content, filename in ls_of_attachments:
		upload_to_s3(content, filename, s3, destbucket, destbucketprefix)
		
	url_ls_unfiltered = []
	url_ls = []
	
	text_plain_html = [(str(dic['Content']), dic['Content-Type']) for dic in ls 
					if dic['Content-Type'] == 'text/html'
					or dic['Content-Type'] == 'text/plain']
	
	for content, type in text_plain_html:
		if type == 'text/plain':
			url_ls_unfiltered.extend(get_urls_from_body.get_urls_from_plain_part(content))
		else:
			url_ls_unfiltered.extend(url_in_html_code.url_in_html_code(content))

	for url in url_ls_unfiltered:
		try:
			result = urllib2.urlopen(url)
			if result.getcode() == 200:
				org_url = result.geturl()
				split =  urlparse.urlsplit(org_url)	
				filename = urllib2.unquote(split.path.split("/")[-1])
				if check_ext(filename):
					url_ls.append((filename, org_url))	
		except:
			print("Inaccessible URL: " + url)
		

	for filename, url in list(set(url_ls)):
		try:
			response = urllib2.urlopen(url)
			content = response.read()
			upload_to_s3(content, filename, s3, destbucket, destbucketprefix)
		except:
			print('URL not downloadable: ' + url)	
		