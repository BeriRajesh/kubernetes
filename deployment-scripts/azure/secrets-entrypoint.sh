#!/bin/bash

VAULT_KEY_NAME=${VAULT_KEY_NAME:-}
VAULT_KEY_SECRET=${VAULT_KEY_SECRET:-}
CONFIG_PATH=${CONFIG_PATH:-}

echo $VAULT_KEY_NAME
echo $VAULT_KEY_SECRET
echo $CONFIG_PATH
#To login into the account using identity on the cloud
az login --identity --allow-no-subscriptions
echo "login done"

#GET VALUE from the keyvaults and creating a file named serveroverride-temp.cfg
if [  -f "${APP_CONFIG}" ]; then rm -r "${APP_CONFIG}"; fi  || true
if [  -f "${CONFIG_PATH}" ]; then rm -r "${CONFIG_PATH}"; fi || true
az keyvault secret show --vault-name "${VAULT_KEY_NAME}" --name "${VAULT_KEY_SECRET}" --query value > serveroverride-temp.cfg
echo "keyvault get success"
#creating a proper format from the tempfile to serveroverride.cfg
sed 's/.//' serveroverride-temp.cfg | sed 's/.$//' | awk '{gsub(/\\n/,"\n")}1' | sed 's/\\"/"/g' > "${CONFIG_PATH}"
echo "keyvault format "
#removing the temporary file
rm -rf serveroverride-temp.cfg

export $(grep -v '^#' .env | xargs)
echo "cat .env started"
cat ${CONFIG_PATH}
echo "cat .env end"
/usr/bin/supervisord -c supervisord.conf -n