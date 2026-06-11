from pymilvus import connections, utility

connections.connect("default", host="xxxxxxxx-db.annalect.com", port="443", secure=True, user='XXXXXX', password='XXXXXXXXXXXX',)
#hostname format EX : qamilvus-db.annalect.com 

roles = utility.list_roles(include_user_info=True)
print(f"roles in Milvus: {roles}")