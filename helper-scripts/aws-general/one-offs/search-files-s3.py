import boto3
import re
import json
import multiprocessing
import time
import traceback


s3 = boto3.client('s3')

client = s3

s3objects_queue = multiprocessing.Queue()

def filter_objects(obj):
    return pattern.search(obj['Key']) is not None

def get_objects(client, params):
    s3objects_queue.put(client.list_objects_v2(**params))

buckets = client.list_buckets()

regex = "(dyson|walmart|claritas)"
pattern = re.compile(regex, re.IGNORECASE)

with open('scanned_buckets.txt', 'a+') as fp:
    fp.seek(0)
    cached_buckets = fp.read()

num_buckets = len(buckets['Buckets'])
for i, bucket in enumerate(buckets['Buckets']):
    j = i+1

    bucket_name = bucket['Name']

    print(f'{j}/{num_buckets} ({round(j/num_buckets, 1)*100}%) - {bucket_name=}')
    bucket = boto3.resource('s3').Bucket(bucket_name)

    if bucket_name in cached_buckets:
        print(f"  Already searched in {bucket_name=}")
        continue

    skip_bucket = False
    ignored_buckets_regex = ['loadbalancer-logs', 's3access-logs', 's3bucket-inventory', '-terraform-', '-alienvault-']
    for ignored_bucket_regex in ignored_buckets_regex:
        if re.search(ignored_bucket_regex, bucket_name):
            skip_bucket = True
            break

    if skip_bucket:
        print(f'  Skipping {bucket_name=}')
        continue

    print("  Number of files scanned: ", end="")

    files = []
    try:
        for i, obj in enumerate(bucket.objects.all()):
            a=1
            if pattern.search(obj.key):
                files.append(obj.key)
            if i%1000 == 0:
                print(f'{i} ', end="")
    except Exception:
        print()
        traceback.print_exc()
        continue

    with open('scanned_buckets.txt', 'a+') as fp:
        fp.write(f"{bucket_name}\n")

    print()
    print(f"  {len(files)} found in {bucket_name=} meeting {regex=} (case insensitive)")

    if files:
        with open(f'files_in_bucket_{bucket_name}.txt', 'w') as fp:
            fp.write(f"{json.dumps(files, indent=4, default=str)}\n")
            fp.write(f"\n")


# print(files)


