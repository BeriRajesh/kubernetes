from pymilvus import connections, utility
from pymilvus.orm.role import Role

connections.connect("default", host="xxxxxxxx-db.annalect.com", port="443", secure=True, user='XXXXXX', password='XXXXXXXXXXXX',)
#hostname format EX : qamilvus-db.annalect.com 

role = Role(name="milvusdb_admin", using="default")

### user appropriate roles as required

role.grant("Collection", "test_bhaskar_1_simple", "*")
role.grant("Collection", "*", "*")
role.grant("Global", "*", "CreateCollection")
role.grant("Global", "*", "DropCollection")
role.grant("Global", "*", "DescribeCollection")
role.grant("Global", "*", "ShowCollections")
role.grant("Global", "*", "CreateResourceGroup")
role.grant("Global", "*", "DropResourceGroup")
role.grant("Global", "*", "DescribeResourceGroup")
role.grant("Global", "*", "ListResourceGroups")
role.grant("Global", "*", "ListResourceGroups")

role.revoke("Global", "*", "CreateOwnership")
role.revoke("Global", "*", "DropOwnership")
role.revoke("Global", "*", "SelectOwnership")
role.revoke("Global", "*", "ManageOwnership")





# role2 = Role(name="milvusdb_viewer", using="default")
# role2.grant("Collection", "*", "Read")