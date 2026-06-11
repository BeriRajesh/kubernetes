#!/bin/bash
set -euo pipefail

usage() {
  echo "Usage: $0 --env=prod --app=airflow  ]"
  echo "  must be either 'dev', 'qa', 'stg', 'mgmt' or 'prod' environment"
  exit 1
}

while getopts :ea:-: opt; do
    [[ - == $opt ]] && opt=${OPTARG%%=*} OPTARG=${OPTARG#*=}
    case $opt in
    h | help ) print_help ; exit 0 ;;

    # environment to use when uploading the configuration or secrets
    e | env  )
                env=$OPTARG
                # Ensures that the specified environment is valid.
                [[ "${env}" == "dev" ||  "${env}" == "qa" || "${env}" == "stg" || "${env}" == "prod" || "${env}" == "mgmt" ]] || usage

                ;;
    # app whose confiration file is being uploaded
    a | app  ) app=$OPTARG ;;

    # if force is set, no question are asked. by default no secrets are downloaded, only the override.
    f | force ) FORCE=$OPTARG ;;

    # control if the aws commands have the --quiet flag. By default QUIET=--quiet
    q | QUIET ) QUIET=$OPTARG ;;

    # file options controls the name of the encrypted file being uploded. if set the script won't ask for a name
    file ) FILE=$OPTARG ;;

    * ) usage >&2 ; exit 2 ;;
    esac
done
shift $((OPTIND - 1))


# If no environment was specified, show usage.
if [[ -z "${env}" ]]  || [[ -z "${app}" ]] ; then
    usage
fi

BUILD_ENV="${env}"
APP_NAME="${app}"
FORCE=${FORCE:-}
FILE=${FILE:-}
QUIET=${QUIET:-}

if [ "${QUIET}" == false ]; then
	QUIET=" "
	set -x
fi

case "${BUILD_ENV}" in (dev|qa|stg|prod|mgmt);; (*) usage ;; esac

echo BUILD_ENV="$BUILD_ENV"
echo APP_NAME="$APP_NAME"


#Encrypt config file, application and environmenet specific secret variables and store those in the S3 bucket

#Default Environment Variables
SECRETS_BUCKET_NAME="annalect-cloud-vault"
eval $(aws s3 cp s3://${SECRETS_BUCKET_NAME}/container-secrets/ecs-kms-key - | sed 's/^/export /')


##
function encrypt_config_file () {
        if [ ! -e "$APP_CONFIG" ]; then
        echo >&2 "error: missing $APP_CONFIG"
        exit 1;
        fi
        aws-encryption-cli --encrypt --input ${APP_CONFIG} \
                     --master-keys key=${KEY_ID} \
                     --encryption-context AppName=${APP_NAME} EnvName=${BUILD_ENV} \
                     --metadata-output ~/metadata \
                     --output .

        aws s3 cp ${APP_CONFIG}.encrypted s3://${SECRETS_BUCKET_NAME}/container-secrets/${BUILD_ENV}/${APP_NAME}/${APP_CONFIG}.encrypted --sse
}

## Encrypt and store application specific secret variables in s3 .e.g. Wordpress site

function encrypt_app_secrets () {
aws-encryption-cli --encrypt --input get_app_secrets \
                     --master-keys key=${KEY_ID} \
                     --encryption-context AppName=${APP_NAME} EnvName=${BUILD_ENV} \
                     --metadata-output ~/metadata \
                     --output .

aws s3 cp get_app_secrets.encrypted s3://${SECRETS_BUCKET_NAME}/container-secrets/${BUILD_ENV}/${APP_NAME}/get_app_secrets.encrypted --sse
}

## Encrypt and store environment specific secret variables in s3 .e.g. API key for an agent like Datadog or loggly
function encrypt_env_secrets () {
aws-encryption-cli --encrypt --input get_env_secrets \
                     --master-keys key=${KEY_ID} \
                     --encryption-context AppName=${APP_NAME} EnvName=${BUILD_ENV} \
                     --metadata-output ~/metadata \
                     --output .

aws s3 cp get_env_secrets.encrypted s3://${SECRETS_BUCKET_NAME}/container-secrets/${BUILD_ENV}/get_env_secrets.encrypted --sse
}

#s3://${SECRETS_BUCKET_NAME}/container-secrets/${BUILD_ENV}/${APP_NAME}/${APP_CONFIG}.encrypted
#encrypt_config_file



if [ ! "$FORCE" = "true" ]; then
    read -p "Do you want to upload the secret config file in S3 for $APP_NAME on $BUILD_ENV? " yn
else
    yn="y"
fi

case $yn in
    [Yy]*)
        if [ -z "$FILE" ]; then
            if [ ! "$FORCE" = "true" ]; then
                read -e -p "Enter the file name [serveroverride.cfg]: " filename
            fi

            if [[ $app = "ade" || $app = "adeingest" || $app = "adeweb" ]]; then
                APP_CONFIG=${filename:-"adeserveroverride.cfg"};
            else
                APP_CONFIG=${filename:-"serveroverride.cfg"};
            fi
        else
            APP_CONFIG=${filename:-$FILE};
        fi

        FILE_IN_S3="s3://${SECRETS_BUCKET_NAME}/container-secrets/${BUILD_ENV}/${APP_NAME}/${APP_CONFIG}.encrypted"
        if [ ! "$FORCE" = "true" ]; then
            read -p "File exists. This is going to add/replace ${FILE_IN_S3}. Are you sure? [y/N] " response
        else
            response="y"
        fi
        case "$response" in
            [yY][eE][sS]|[yY])
                encrypt_config_file
                ;;
            *)
            exit;;
        esac
        ;;
    [Nn]* ) echo "You selected NO.";;
        * ) echo "Please answer yes or no.";;
esac

if [ ! "$FORCE" = "true" ]; then
    read -p "Do you want to upload the app_secrets file in S3 for $APP_NAME on $BUILD_ENV? " yn
else
    yn="n"
fi

case $yn in
    [Yy]*)
        APP_CONFIG=get_app_secrets;
        FILE_IN_S3="s3://${SECRETS_BUCKET_NAME}/container-secrets/${BUILD_ENV}/${APP_NAME}/${APP_CONFIG}.encrypted"
        if [[ -f ./${APP_CONFIG} ]]; then
            read -p "File exists. This is going to add/replace ${FILE_IN_S3}. Are you sure? [y/N] " response
            case "$response" in
                [yY][eE][sS]|[yY])
                    encrypt_config_file
                    ;;
                *)
                exit;;
            esac
        else
            echo "File ./${APP_CONFIG} not found. Please create one with the desired secrets."
            exit 1
        fi
        ;;
    [Nn]* ) echo "You selected NO.";;
        * ) echo "Please answer yes or no.";;
esac

if [ ! "$FORCE" = "true" ]; then
    read -p "Do you want to upload the env_secrets file in S3 for $APP_NAME on $BUILD_ENV? " yn
else
    yn="n"
fi
case $yn in
    [Yy]*)
    APP_CONFIG=get_env_secrets;
    FILE_IN_S3="s3://${SECRETS_BUCKET_NAME}/container-secrets/${BUILD_ENV}/${APP_NAME}/${APP_CONFIG}.encrypted"
    [[ -f ./${APP_CONFIG} ]] && read -p "File exists. This is going to add/replace ${FILE_IN_S3}. Are you sure? [y/N] " response
        case "$response" in
            [yY][eE][sS]|[yY])
                encrypt_config_file
                ;;
            *)
            exit;;
        esac
        ;;
    [Nn]* ) echo "You selected NO.";;
        * )
        echo "Please answer yes or no."
        exit;;

esac

#Unset the environment variables
envs=(
    SECRETS_BUCKET_NAME
    KEY_ID
    BUILD_ENV
    APP_NAME
    APP_CONFIG
    )

for e in "${envs[@]}"; do
    unset "$e"
done

#END
