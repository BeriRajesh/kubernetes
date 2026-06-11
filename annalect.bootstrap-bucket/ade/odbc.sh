#!/bin/bash
#Installing the Microsoft ODBC Driver for SQL Server on Linux
cd /tmp/
sudo wget http://download.microsoft.com/download/B/C/D/BCDD264C-7517-4B7D-8159-C99FC5535680/RedHat6/msodbcsql-11.0.2270.0.tar.gz
sudo tar -zxvf msodbcsql-11.0.2270.0.tar.gz
cd msodbcsql-11.0.2270.0/
sudo bash install.sh install --accept-license --force
sudo ln -s /lib/x86_64-linux-gnu/libcrypto.so.1.0.0 /usr/lib/x86_64-linux-gnu/libcrypto.so.10;
sudo ln -s /lib/x86_64-linux-gnu/libssl.so.1.0.0 /usr/lib/x86_64-linux-gnu/libssl.so.10;
#To verify that the ODBC driver on Linux was registered successfully, execute the following command:
sudo odbcinst -q -d -n "ODBC Driver 11 for SQL Server"
