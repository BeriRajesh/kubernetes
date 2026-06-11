#!/bin/bash
set -euo pipefail

QUIET=${QUIET:-}
if [ ! -z "$QUIET" ]; then
	set -x
fi

usage() {
  echo "Usage: $0 --env=prod --app=airflow  ]"
  echo "  must be either 'dev', 'qa', 'stg', 'mgmt' or 'prod' environment"
  exit 1
}

while getopts :ea:-: opt; do
    [[ - == $opt ]] && opt=${OPTARG%%=*} OPTARG=${OPTARG#*=}
    case $opt in
    h | help ) print_help ; exit 0 ;;

    # environment to use when downloading the configuration or secrets
    e | env  )
                env=$OPTARG
                # Ensures that the specified environment is valid.
                [[ "${env}" == "dev" ||  "${env}" == "qa" || "${env}" == "stg" || "${env}" == "prod" || "${env}" == "mgmt" ]] || usage

                ;;

    # app whose confiration file is being downloaded
    a | app  ) app=$OPTARG ;;

    # if force is set, no question are asked. by default no secrets are downloaded, only the override.
    f | force ) FORCE=$OPTARG ;;

    # control if the aws commands have the --quiet flag. By default QUIET=--quiet
    q | QUIET ) QUIET=$OPTARG ;;

    # file options controls the name of the encrypted file being downloaded. if set the script won't ask for a name
    file ) FILE=$OPTARG ;;

    * ) usage >&2 ; exit 2 ;;
    esac
done
shift $((OPTIND - 1))


# If no environment was specified, show usage.
if [[ -z "${env:-}" ]]  || [[ -z "${app:-}" ]] ; then
    usage
fi

BUILD_ENV="${env}"
APP_NAME="${app}"
QUIET=${QUIET:-"--quiet"}
FORCE=${FORCE:-""}
FILE=${FILE:-""}

if [ "${QUIET}" == false ]; then
	QUIET=" "
	set -x
fi

case "${BUILD_ENV}" in (dev|qa|stg|prod|mgmt);; (*) usage ;; esac

echo BUILD_ENV="$BUILD_ENV"
echo APP_NAME="$APP_NAME"

#Default Environment Variables
SECRETS_BUCKET_NAME="annalect-cloud-vault"



function decrypt_config_file () {
	aws s3 $QUIET cp s3://${SECRETS_BUCKET_NAME}/container-secrets/"${BUILD_ENV}"/"${APP_NAME}"/"${APP_CONFIG}".encrypted .

    if [ -f $PWD/"${APP_CONFIG}" ]; then
        rm $PWD/"${APP_CONFIG}"
    fi

	aws-encryption-cli --decrypt --input "${APP_CONFIG}".encrypted \
		--encryption-context AppName=${APP_NAME} EnvName=${BUILD_ENV} \
		--metadata-output ~/metadata \
		--output  $PWD/"${APP_CONFIG}"
	}


function decrypt_app_secrets () {
		aws s3 $QUIET cp s3://${SECRETS_BUCKET_NAME}/container-secrets/"${BUILD_ENV}"/"${APP_NAME}"/get_app_secrets.encrypted .

		aws-encryption-cli --decrypt --input get_app_secrets.encrypted \
			--encryption-context AppName=${APP_NAME} EnvName=${BUILD_ENV} \
			--metadata-output ~/metadata \
			--output  "$PWD"/get_app_secrets
}

function decrypt_env_secrets () {
		aws s3 $QUIET cp s3://${SECRETS_BUCKET_NAME}/container-secrets/"${BUILD_ENV}"/get_env_secrets.encrypted .

		aws-encryption-cli --decrypt --input get_env_secrets.encrypted \
			--encryption-context EnvName=${BUILD_ENV} \
			--metadata-output ~/metadata \
			--output "$PWD"/get_env_secrets
}

if [ ! "$FORCE" = "true" ]; then
    read -p "Do you want to download the secret config file in S3 for $APP_NAME on $BUILD_ENV? " yn
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

        echo "You selected '${APP_CONFIG}'."

        if [ ! "$FORCE" = "true" ]; then
            read -p "Are you sure? [y/N] " response
        else
            response="y"
        fi
        case "$response" in
            [yY][eE][sS]|[yY])
                decrypt_config_file
                ;;
            *)
            exit;;
        esac
        ;;
    [Nn]* ) echo "You answered No";;
        * ) echo "Please answer yes or no.";;
esac

if [ ! "$FORCE" = "true" ]; then
    read -p "Do you want to download the get_app_secrets file in S3 for $APP_NAME on $BUILD_ENV? " yn
else
    yn="n"
fi

case $yn in
    [Yy]*)
    read -p "Are you sure? [y/N] " response
        case "$response" in
            [yY][eE][sS]|[yY])
                decrypt_app_secrets
                ;;
            *)
            exit;;
        esac
        ;;
    [Nn]* ) echo "You answered No";;
        * ) echo "Please answer yes or no.";;
esac

if [ ! "$FORCE" = "true" ]; then
    read -p "Do you want to download the get_env_secrets file in S3 for $APP_NAME on $BUILD_ENV? " yn
else
    yn="n"
fi

case $yn in
    [Yy]*)
    read -p "Are you sure? [y/N] " response
        case "$response" in
            [yY][eE][sS]|[yY])
                decrypt_env_secrets
                ;;
            *)
            exit;;
        esac
        ;;
    [Nn]* ) echo "You answered No";;
        * ) echo "Please answer yes or no.";;
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

