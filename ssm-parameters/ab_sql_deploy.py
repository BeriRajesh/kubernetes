#!/usr/bin/env python
import requests
import os
import boto3
from getParameterSecrets import getCredentials

#env = os.environ['env']
env = 'dev'

if env == 'dev':
	apiKey = getCredentials('dev.audience.batchjob.apikey') 
if env == 'prod': 
	apiKey = getCredentials('prod.audience.batchjob.apikey')
if env == 'qa': 
	apiKey = getCredentials('qa.audience.batchjob.apikey')
if env == 'stg': 
	apiKey = getCredentials('stg.audience.batchjob.apikey')

apiKey = apiKey[0]
host = "z4amqgh4i3.execute-api.us-east-1.amazonaws.com"
gateway_endpoint = "https://vpce-09209225d0b441eac-azzwwnjl.execute-api.us-east-1.vpce.amazonaws.com/"
appName = env +"_"+ 'audience_builder'

headers = {"x-api-key": apiKey, "Host":host}
api_endpoint = gateway_endpoint + env + '/submit'
jobCommand = "lib/batch_test.py"
jobName = "audiencebuilder_sql_deploy"

print 'Environment = ' + env
print 'jobName = ' + jobName
print 'jobCommand = ' + jobCommand
print 'appName = ' + appName

payload={ 
	"jobCommand": jobCommand, 
	"jobName": jobName, 
	"arguments": {
        "ARG1_NAME": "arg1",
        "ARG2_NAME": "arg2",
        "ARG3_NAME": "arg3"
		}, 
		"appName": appName 
	}
r = requests.post(
   api_endpoint,
   headers=headers,
   json=payload
)
print r.text
root@bamboo:/opt/ecs-docker# vi ab_sql_deploy.py 
root@bamboo:/opt/ecs-docker# cat ab_sql_deploy.py 
#!/usr/bin/env python
import requests
import os
import boto3
from getParameterSecrets import getCredentials

env = os.environ['env']
#env = 'prod'

if env == 'dev':
	apiKey = getCredentials('dev.audience.batchjob.apikey') 
if env == 'prod': 
	apiKey = getCredentials('prod.audience.batchjob.apikey')
if env == 'qa': 
	apiKey = getCredentials('qa.audience.batchjob.apikey')
if env == 'stg': 
	apiKey = getCredentials('stg.audience.batchjob.apikey')

apiKey = apiKey[0]
host = "z4amqgh4i3.execute-api.us-east-1.amazonaws.com"
gateway_endpoint = "https://vpce-09209225d0b441eac-azzwwnjl.execute-api.us-east-1.vpce.amazonaws.com/"
appName = env +"_"+ 'audience_builder'

headers = {"x-api-key": apiKey, "Host":host}
api_endpoint = gateway_endpoint + env + '/submit'
jobCommand = "lib/batch_test.py"
jobName = "audiencebuilder_sql_deploy"

print 'Environment = ' + env
print 'jobName = ' + jobName
print 'jobCommand = ' + jobCommand
print 'appName = ' + appName

payload={ 
	"jobCommand": jobCommand, 
	"jobName": jobName, 
	"arguments": {
        "ARG1_NAME": "arg1",
        "ARG2_NAME": "arg2",
        "ARG3_NAME": "arg3"
		}, 
		"appName": appName 
	}
r = requests.post(
   api_endpoint,
   headers=headers,
   json=payload
)
print r.text
