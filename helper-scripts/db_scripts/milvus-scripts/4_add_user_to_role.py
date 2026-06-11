from pymilvus import connections, utility
from pymilvus.orm.role import Role

connections.connect("default", host="xxxxxxxx-db.annalect.com", port="443", secure=True, user='XXXXXX', password='XXXXXXXXXXXX',)
#hostname format EX : qamilvus-db.annalect.com 

role = Role(name="milvusdb_admin")
# role.add_user("balaji_kalahasthi")

# role.add_user("balaji_kalahasthi")
# role.add_user("gadupu_kumar")
# role.add_user("shibir_gr")
# role.add_user("shashikanth_kuwar")
# role.add_user("santhosh_swaminathan")
# role.add_user("jonathan_elfreich")
# role.add_user("charlie_huckel")
# role.add_user("eric_linden")
# role.add_user("ben_greene")

role.add_user("milvus_assist_db_user")