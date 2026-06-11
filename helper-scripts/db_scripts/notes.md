# create main user
    import pymssql
    conn = pymssql.connect(server='sql-se-dev.c488xyottj77.us-east-1.rds.amazonaws.com', user='devdbadmin', password='D3vAbm!n#1', autocommit=True)
    cursor = conn.cursor()
    cursor.execute("create login gadupu_kumar with password = 'rR96WeqUXLGNs$z';")

# allow connect to db
    cursor.execute("use ClearTarget_PRODv2;")
    cursor.execute("CREATE USER [gadupu_kumar] FOR LOGIN [gadupu_kumar];")
    cursor.execute("EXEC sp_addrolemember 'db_datawriter', [gadupu_kumar];")
    conn.commit()
    cursor.execute("EXEC sp_addrolemember 'db_datareader', [gadupu_kumar];")
    conn.commit()