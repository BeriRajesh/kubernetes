import time

import numpy as np
from pymilvus import (
    connections,
    utility,
    FieldSchema, CollectionSchema, DataType,
    Collection,
)
fmt = "\n=== {:30} ===\n"
search_latency_fmt = "search latency = {:.4f}s"
num_entities, dim = 3000, 8

print(fmt.format("start connecting to Milvus"))
connections.connect("default", host="xxxxxxxx-db.annalect.com", port="443", secure=True, user='XXXXXX', password='XXXXXXXXXXXX',)
#hostname format EX : qamilvus-db.annalect.com 

# has = utility.has_collection("hello_milvus")
# print(f"Does collection hello_milvus exist in Milvus: {has}")

utility.create_user("milvus_assist_db_user", "XXXXXXXXXXXXXXXX", using="default")
utility.create_user("xxxx_xxxxxxx", "xxxxxxxxxxxxx", using="default")

