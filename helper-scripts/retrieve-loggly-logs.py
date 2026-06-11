import time
import sys
import requests
from requests.auth import HTTPBasicAuth

import json

from pprint import pprint

# payload = {
#     "q":"/api/*",
#     "from":"-2d",
#     "until":"-1d",
#     "size":"2"
# }

nlines = "1000";

payload = {
    "q":"/aws/rds/instance/adeprod/slowquery/*",
    "from":"2018-02-06 00:00:00.000",
    "until":"2018-02-07 00:00:00.000",
    "size": nlines
}

fh = open('slowqueries-180606-07.log','w')


url = "https://annalect.loggly.com/apiv2/events/iterate"
count = 0
start_time = time.time()
while not url == "":
    print('Retrieving {} log entries from Loggly...'.format(nlines))
    count += 1
    r = requests.get(url, params=payload, auth=HTTPBasicAuth('annalecttio', 'B@4ubal12'))
    elapsed_time = round(time.time() - start_time)

    # print('aqui')
    # print(r.json())
    # print(r.url)

    if 'next' not in r.json():
        break;


    # setting up for next url
    url = r.json()['next']
    payload = {}

    print('{}- {} - Next url: {}'.format(elapsed_time, count, url))

    events = r.json()['events']

    e=0
    for event in events:
        if e%100==0:
            print(e, end=" ")
        e+=1

        if 'message' in json.loads(event['raw']):
            logline = json.loads(event['raw'])['message']
            fh.write(logline)

fh.close()