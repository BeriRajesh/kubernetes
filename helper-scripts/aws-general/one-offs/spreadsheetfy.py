import pandas as pd
import glob
import re
import json

files = glob.glob('files_in_bucket_*')

bucket_keys = []

for f in files:
    bucket = re.search('files_in_bucket_(.*)\.txt', f).group(1)
    keys = json.load(open(f))
    for key in keys:
        bucket_keys.append({
            'bucket': bucket,
            'key': key
        })

df = pd.DataFrame(bucket_keys)
df.to_excel('dyson_walmart_bucket_keys.xlsx', index=False)
# print(bucket_keys)