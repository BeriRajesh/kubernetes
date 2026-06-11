import datadog_helper
from pprint import pprint
import json

def get_rds_screenboard():
    with open('screenboards/anlct-adt-rds.json', 'r') as f:
        return f.read()


screenboard = json.loads(get_rds_screenboard())

print(screenboard['id'])