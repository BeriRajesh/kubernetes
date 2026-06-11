#!/bin/bash
set -e

# echo "Not doing anything"
# exit 0

# Notice the folder structure to support python 3.7 runtime
# https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html#configuration-layers-path
INSTALL_PATH=/opt/python/lib/python3.7/site-packages

# setting necessary environment variables
export ODBCINI=/opt/odbc.ini
export ODBCSYSINI=/opt/

mkdir -p $INSTALL_PATH || true
# exit 1

BITBUCKET_KEY_FILE=docker-deployments.key
if [ -f "$BITBUCKET_KEY_FILE" ]; then
    export GIT_SSH_COMMAND="ssh -i ./docker-deployments.key -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
    chmod 0600 ./docker-deployments.key  || true
    # ssh-keyscan bitbucket.org > /known_hosts
    # cat /known_hosts
    # pip install git+ssh://git@bitbucket.org/annalect/pylect-infra.git@v.1.x --upgrade -t $INSTALL_PATH
else
    echo "$BITBUCKET_KEY_FILE not found. Won't be able to access bitbucket."
    echo "Please copy you id_rsa to Docker's installation directory."
    exit 1
fi

# download and install unixODBC
# http://www.unixodbc.org/download.html
curl ftp://ftp.unixodbc.org/pub/unixODBC/unixODBC-2.3.7.tar.gz -O
tar xzvf unixODBC-2.3.7.tar.gz
cd unixODBC-2.3.7

./configure --sysconfdir=/opt --disable-gui --disable-drivers --enable-iconv --with-iconv-char-enc=UTF8 --with-iconv-ucode-enc=UTF16LE --prefix=/opt
make
make install

cd ..
rm -rf unixODBC-2.3.7 unixODBC-2.3.7.tar.gz

# download and install ODBC driver for MSSQL 17
# https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-2017
curl https://packages.microsoft.com/config/rhel/6/prod.repo > /etc/yum.repos.d/mssql-release.repo
yum install -y e2fsprogs.x86_64 0:1.43.5-2.43.amzn1 fuse-libs.x86_64 0:2.9.4-1.18.amzn1 libss.x86_64 0:1.43.5-2.43.amzn1
ACCEPT_EULA=Y yum install -y msodbcsql17 --disablerepo=amzn*
export CFLAGS="-I/opt/include"
export LDFLAGS="-L/opt/lib"

cd /opt

cp -r /opt/microsoft/msodbcsql17/ .
rm -rf /opt/microsoft/

pip install pyodbc -t $INSTALL_PATH

cat <<EOF > odbcinst.ini
[ODBC Driver 17 for SQL Server]
Description=Microsoft ODBC Driver 17 for SQL Server
Driver=/opt/msodbcsql17/lib64/libmsodbcsql-17.5.so.2.1
UsageCount=1
EOF

cat <<EOF > odbc.ini
[ODBC Driver 17 for SQL Server]
Driver = ODBC Driver 17 for SQL Server
Description = My ODBC Driver 17 for SQL Server
Trace = No
EOF

echo "Finished building layer."