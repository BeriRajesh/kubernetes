import boto3
import time;
from datetime import timedelta
deltatime =60 * 60 * 24
failed_count=0
client = boto3.client('batch')
queues = client.describe_job_queues()

from datetime import datetime
# print(datetime.utcnow().timestamp())

for queue in queues['jobQueues']:
    # print(queue['jobQueueName'])
    failed_jobs = client.list_jobs(jobQueue=queue['jobQueueName'],jobStatus='FAILED')
    count=len(failed_jobs['jobSummaryList'])
    if count != 0:
        print(queue['jobQueueName'])
        int_count=0
        for failed_job in failed_jobs['jobSummaryList']:
            if(datetime.utcnow().timestamp()-deltatime < failed_job['createdAt']/1000.0 ):
                if str(failed_job).count('container') > 0:
                    if str(failed_job['container']).count('exitCode') > 0:
                        exit_code=failed_job['container']['exitCode']
                else:
                    exit_code="N/A" 
                print('\t',failed_job['jobId'], ',',failed_job['jobName'], ',', failed_job['status'], ',',exit_code, ',', failed_job['statusReason'])
                int_count=int_count+1
                failed_count=failed_count+1

        print("\n    Failed jobs in ", queue['jobQueueName'], " : ", int_count , '\n' )  
        print("*******************************************************************************************************************")    

    # else:
    #     print("\tNo Jobs failed in this queue in the last 24 hours")

print("Total Number of Batch Jobs Failed since ", str(timedelta(seconds=deltatime)), ": ", failed_count )
print("*******************************************************************************************************************") 
