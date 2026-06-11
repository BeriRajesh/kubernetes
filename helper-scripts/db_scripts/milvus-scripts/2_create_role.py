from pymilvus import connections, utility
from pymilvus.orm.role import Role


connections.connect("default", host="xxxxxxxx-db.annalect.com", port="443", secure=True, user='XXXXXX', password='XXXXXXXXXXXX',)
#hostname format EX : qamilvus-db.annalect.com 
role = Role(name="milvusdb_viewer", using="default")
role.create()

test=utility.list_roles(True, using="default")
print(f"roles in Milvus: {test}")