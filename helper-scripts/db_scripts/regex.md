# transform credentials spreadsheet RDS to conf file
    search: ([^\t]*?)\t([^\t]*?)\t([^\t]*?)\t([^\t]*?)\t([^\t]*?)\t([^\t]*?)$
    replace: {\n    "name": "$1",\n    "host": "$1",\n    "dbname": "",\n    "username": "$5",\n    "password": "$6",\n    "type": "mssql",\n}

# combination host: dbname
    search: ([^\t]*?)\t([^\t]*?)\t([^\t]*?)\t([^\t]*?)\t([^\t]*?)\t([^\t]*?)$
    replace: "$1": "$4",