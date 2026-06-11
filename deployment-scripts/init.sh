#!/bin/bash
set -e

aws s3 --quiet cp s3://annalect-cloud-vault/container-secrets/secrets-entrypoint.sh /

if [ -f "/secrets-entrypoint.sh" ]; then
    chmod +x /secrets-entrypoint.sh
    /secrets-entrypoint.sh
else
    echo "Running barebones"
fi

# execute CMD specified in Dockerfile
exec "$@"