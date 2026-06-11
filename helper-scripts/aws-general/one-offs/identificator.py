import pandas as pd
import boto3
import re
import json
import traceback

s3 = boto3.resource('s3')

file = 'dyson_walmart_bucket_keys.xlsx'

df = pd.read_excel(file)

bucket_resources = {}
bucket_tags = {}
bucket_owners = {}

dfdict = df.to_dict()

for i, row in df.iterrows():
    try:
        if i%100 == 0:
            print(f"{i} ", end='', flush=True)

        # print(i, row)

        if not bucket_resources.get(row.bucket):
            bucket_resources[row.bucket] = s3.Bucket(row.bucket)


        if not bucket_tags.get(row.bucket):
            bucket_tags[row.bucket] = s3.BucketTagging(row.bucket).tag_set

        if not bucket_owners.get(row.bucket):
            bucket_owners[row.bucket] = '?'
            for tag in bucket_tags[row.bucket]:
                if tag.get('Key','').lower() == 'owner':
                    bucket_owners[row.bucket] = tag.get('Value')

        df.loc[i, 'BucketOwnerTag'] = bucket_owners[row.bucket]
        df.loc[i, 'BucketTags'] = json.dumps(bucket_tags[row.bucket])

        object_summary = s3.ObjectSummary(row.bucket, row.key)
        df.loc[i, 'ObjectSize (Mb)'] = round(object_summary.size/1024/1024,2)
        df.loc[i, 'Type'] = re.search('(dyson|walmart|claritas)', row.key.lower()).group(1)
        df.loc[i, 'LastModified'] = str(object_summary.last_modified)
        # df.loc[i, 'ObjectOwner'] = object_summary.owner
        a=1
    except:
        traceback.print_exc()


df.to_excel('dyson_walmart_filled.xlsx', index=False)
