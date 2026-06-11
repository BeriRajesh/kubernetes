import sys
sys.path.append('/opt')
sys.path.append('/opt/python')

import pyodbc
import os

# def Test2(rootDir):
#     for lists in os.listdir(rootDir):
#         path = os.path.join(rootDir, lists)
#         print(path)
#         if os.path.isdir(path):
#             Test2(path)

print(f"cwd is: {os.getcwd()}")
# Test2('/')
driver = '{ODBC Driver 17 for SQL Server}'
sqlServer = 'anlctdev-mssql-01.c488xyottj77.us-east-1.rds.amazonaws.com'
sqlDatabase = 'EmpowerID_Dev'
sqlPort = '1433'

sqlUsername = 'sqldbadmin'
sqlPassword = 'S3vAbm!n#1'

def main(event):
    print('Drivers:')
    print(pyodbc.drivers())
    print('Attempting Connection...')
    conn = pyodbc.connect(f"DRIVER={driver};SERVER={sqlServer};PORT={sqlPort};DATABASE={sqlDatabase};UID={sqlUsername};PWD={sqlPassword}");
    print('Connected!!!')

if __name__ == "__main__":
    main({})