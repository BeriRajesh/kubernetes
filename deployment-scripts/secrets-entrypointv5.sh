#!/bin/bash
set -euo pipefail

# version 1.16 / Jul-07 2021
#	fixed minor bug - put SERVEROVERRIDE_KEY variable in quote
#   add support to get BITBUCKET_DEPLOYMENT_KEY on container
# version 1.15 / Apr-21 2021
#	adding support for running docker container locally with pylect-infra
# version 1.14 / Apr-21 2021
#	adding support for aws-encryption-cli >= 2.0.0
# version 1.12 / Apr-02 2021
#	adding support for retrieving secrets from Parameter Store and/or Secrets Manager
# version 1.11 / Jan-27 2020
#   merged with airflow's secrets-entrypoint
#   added message after container's command execution
# version 1.10 / May-28-2019
#	deleting possible configuration files before decrypting and moving
# version 1.9 / May-28-2019
#   removing unneeded lines with `echo`
# version 1.8 / May-20-2019
# 	general way of moving configuration to destination
# version 1.7 / May-15-2019
# 	moving secret file to '/'
# version 1.6 / May-8-2019
#	default value for CONFIG_PATH
#   removing initial / from CONFIG_PATH
#	adding set -e to fail if errors on script
# version 1.5 / May-7-2019
#	if RUN_SECRET_ENTRYPOINT = 0, the script executes #@ and exits.
# version 1.4 / Mar-18-2019
#	recovering original functionality of GET_APPS_SECRETS and GET_ENV_SECRETS
# version 1.3 / Mar-18-2019
# 	"No env|app secrets" messages under $QUIET
# version 1.2 / Mar-07-2019
#	subsituted all --quiet with $QUIET
#	bugfix on
# version 1.1 - Feb2019
# 	added GET_BUNDLE_SECRETS
#	added QUIET parameter

#Retrieve the encrypted config file, application and environmenet specific secret variables from S3 bucket
#Service-Defined Environment Variables should be added in task-defintion file for the container
#APP_NAME=
#BUILD_ENV=


CONFIG_PATH=${CONFIG_PATH:-"serveroverride.cfg"}
# CONFIG_PATH=${CONFIG_PATH#/}


# Setting default values
RUN_SECRET_ENTRYPOINT=${RUN_SECRET_ENTRYPOINT:-true}
SECRETS_BUCKET_NAME=${SECRETS_BUCKET_NAME:-}
KEY_ID_ARN=${KMS_KEY_ID_ARN:-}
BUILD_ENV=${BUILD_ENV:-}
APP_NAME=${APP_NAME:-}
SERVEROVERRIDE_KEY=${SERVEROVERRIDE_KEY:-}
GET_APPS_SECRETS=${GET_APPS_SECRETS:-}
GET_ENV_SECRETS=${GET_ENV_SECRETS:-}
GET_BUNDLE_SECRETS=${GET_BUNDLE_SECRETS:-}
PUT_BUNDLE_SECRETS=${PUT_BUNDLE_SECRETS:-}
BITBUCKET_DEPLOYMENT_KEY=${BITBUCKET_DEPLOYMENT_KEY:-}
QUIET=${QUIET:-}

if [ "${RUN_SECRET_ENTRYPOINT}" == "false" ]; then
	echo "Not running secrets-entrypoint, instead only running '$@'"
	exec "$@"
	exit $?
fi


# Retrieve BITBUCKET_DEPLOYMENT_KEY from ssm parameter store
if [ "${RUN_SECRET_ENTRYPOINT}" == true ] && [ ! -z "${BITBUCKET_DEPLOYMENT_KEY}" ]; then
	if [ ! -d ~/.ssh ]; then mkdir -p ~/.ssh; fi
	echo "$BITBUCKET_DEPLOYMENT_KEY" > ~/.ssh/id_rsa && chmod 600 ~/.ssh/id_rsa
	cp ~/.ssh/id_rsa  docker-deployments.key
	ssh-keygen -F bitbucket.org || ssh-keyscan bitbucket.org >>~/.ssh/known_hosts	
fi

# allowing non quiet downloads from s3, for testing purposes
if [ "$QUIET" == false ]
then
	QUIET=''
	set -x
else
	QUIET='--quiet'
fi

if [ -z "${SECRETS_BUCKET_NAME}" ]; then
	SECRETS_BUCKET_NAME="annalect-cloud-vault"
	DECRYPT=1
else
	DECRYPT=0
fi

# Check that the environment variable has been set correctly
if [ -z "${BUILD_ENV}" ] && [ -z "${APP_NAME}" ]; then
  echo >&2 'error: missing required environment variables'
  exit 1
fi

# Retrieving AWS AZ and Region from Instance Metadata which is available locally for the instance on AWS.
#This is not required as running the script from us-east-1 region
# default REGION
# REGION='us-east-1'
# set +e
# AWS_AVAIL_ZONE=`curl -m 2 -s http://169.254.169.254/latest/meta-data/placement/availability-zone`
# if [ ! -z "$AWS_AVAIL_ZONE" ]; then
	# REGION=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document|grep region|awk -F\" '{print $4}')
# fi
# set -e

#Print output for variables
echo BUILD_ENV="$BUILD_ENV"
echo APP_NAME="$APP_NAME"
echo DOCKER_CMD=${@:-}
# echo AWS_DEFAULT_REGION=$REGION

function decrypt_config_file () {
	aws s3 $QUIET cp s3://${SECRETS_BUCKET_NAME}/container-secrets/"${BUILD_ENV}"/"${APP_NAME}"/"${APP_CONFIG}".encrypted .
	echo "Retrieving serveroverride from s3 vault..."

	if [  -f "${APP_CONFIG}" ]; then rm -r "${APP_CONFIG}"; fi  || true
	if [  -f "${CONFIG_PATH}" ]; then rm -r "${CONFIG_PATH}"; fi || true

	aws-encryption-cli --decrypt --input "${APP_CONFIG}".encrypted \
		--wrapping-keys key=${KEY_ID_ARN} \
		--encryption-context AppName=${APP_NAME} EnvName=${BUILD_ENV} \
		--metadata-output ~/metadata \
		--commitment-policy require-encrypt-require-decrypt \
		--output  "${APP_CONFIG}"

	if [ -f "${CONFIG_PATH}" ]; then
		echo "Copied serveroverride at ${CONFIG_PATH} for ${APP_NAME}-${BUILD_ENV}"
	else
		mv "${APP_CONFIG}" "${CONFIG_PATH}"
		echo "The serveroverride moved to ${CONFIG_PATH}."
	fi

}

function download_config_file () {
	aws s3 $QUIET cp s3://${SECRETS_BUCKET_NAME}/container-secrets/"${BUILD_ENV}"/"${APP_NAME}"/"${APP_CONFIG}".encrypted "${CONFIG_PATH}"
}

function decrypt_app_secrets () {
		aws s3 $QUIET cp s3://${SECRETS_BUCKET_NAME}/container-secrets/"${BUILD_ENV}"/"${APP_NAME}"/get_app_secrets.encrypted .

		aws-encryption-cli --decrypt --input get_app_secrets.encrypted \
			--wrapping-keys key=${KEY_ID_ARN} \
			--encryption-context AppName=${APP_NAME} EnvName=${BUILD_ENV} \
			--metadata-output ~/metadata \
			--commitment-policy require-encrypt-require-decrypt \
			--output get_app_secrets
}

function decrypt_env_secrets () {
		aws s3 $QUIET cp s3://${SECRETS_BUCKET_NAME}/container-secrets/"${BUILD_ENV}"/get_env_secrets.encrypted .

		aws-encryption-cli --decrypt --input get_env_secrets.encrypted \
			--wrapping-keys key=${KEY_ID_ARN} \
			--encryption-context EnvName=${BUILD_ENV} \
			--metadata-output ~/metadata \
			--commitment-policy require-encrypt-require-decrypt \
			--output get_env_secrets
}

function decrypt_bundle_secrets () {
	TMPDIR="$(mktemp -d -p '/src')"
	# aws s3 cp --recursive s3://annalect-adt/test/ $TMPDIR
	aws s3 cp $QUIET s3://${SECRETS_BUCKET_NAME}/container-secrets/"${BUILD_ENV}"/"${APP_NAME}"/ $TMPDIR --recursive
	for fullfile in "$(ls -1 $TMPDIR/* 2>/dev/null)"
	do
		if [ -z "$fullfile" ]
		then
			continue;
		fi;

		echo $fullfile
		# we need the file parts to see if they have the '.encrypted' extension
		filename=$(basename -- "$fullfile")


		# check if filename has extension
		if [[ $filename == *"."* ]]
		then
			fullfilename="${fullfile%.*}"
			extension="${filename##*.}"

			if [ "$extension" == "encrypted" ]
			then
				echo "decrypting $fullfile"
				aws-encryption-cli -v --decrypt --input $fullfile \
					--wrapping-keys key=${KEY_ID_ARN} \
					--encryption-context AppName=${APP_NAME} EnvName=${BUILD_ENV} \
					--metadata-output ~/metadata \
					--commitment-policy require-encrypt-require-decrypt \
					--output $fullfilename
				mv "${fullfilename}" "$filename"
			else
				mv "${fullfile}" "$filename"
			fi

		else
			echo "not necessary to decrypt $fullfile"
			fullfilename=$fullfile
			extension=""

			mv "${fullfile}" "/src/$filename"
		fi

		if [ $filename == "envs.sh" ]
		then
			source envs.sh
		fi

	done
}

function encrypt_bundle_secrets () {
	echo "Not yet implemented."
	exit 2

	# if [ -z ${1:-} ]
	# then
	# 	echo "Please specify a directory of files to encrypt. These will be uploaded to the vault for '$APP_NAME'."
	# 	exit 1
	# fi

	# TMPDIR=$1
	# if [ ! -d $TMPDIR ]
	# then
	# 	echo "Please specify a valid directory."
	# 	exit 2
	# fi

	# ENCRYPTDIR=$(mktemp -d -p.)
	# aws s3 cp --recursive s3://annalect-adt/test/ $TMPDIR
	# for fullfile in $(ls -1 $TMPDIR/*)
	# do

	# 	# we need the file parts to see if they have the '.encrypted' extension
	# 	filename=$(basename -- "$fullfile")
	# 	fullfilename="${fullfile%.*}"
	# 	extension="${filename##*.}"

	# 	if [ "$extension" == "encrypted" ]
	# 	then
	# 		aws-encryption-cli -v --encrypt --input $fullfile \
	# 			--encryption-context AppName=${APP_NAME} EnvName=${BUILD_ENV} \
	# 			--metadata-output ~/metadata \
	# 			--output $ENCRYPTDIR/$filename.encrypted
	# 	fi

	# done

}

function get_serveroverride () {

	echo "Retrieving serveroverride from SSM Parameter store..."

	if [ -n "${SERVEROVERRIDE_KEY}" ] && [ "${SERVEROVERRIDE_KEY}" == "ssm" ]; then
		echo "Container running locally."
 		pylect-infra ssm print_value --cli --key /${BUILD_ENV}/${APP_NAME}/serveroverride --output $CONFIG_PATH
 		return
	fi

	if [  -f "${CONFIG_PATH}" ]; then 
		echo "The ${CONFIG_PATH} already exists, removing it."
		rm -r "${CONFIG_PATH}"
	fi || true

	if [ -n "${SERVEROVERRIDE_KEY}" ] && [ "${SERVEROVERRIDE_KEY}" != "ssm" ]; then
		echo "Container running on ECS or Batch"
		echo "$SERVEROVERRIDE_KEY" > "${CONFIG_PATH}"
	fi


	if [ -f "${CONFIG_PATH}" ]; then
		echo "Copied serveroverride at ${CONFIG_PATH} for ${APP_NAME}-${BUILD_ENV}"
		echo "Config Timestamp: " `ls -ltr ${CONFIG_PATH}` 
	else
		echo "Couldn't copy serveroverride at ${CONFIG_PATH} for ${APP_NAME}-${BUILD_ENV}"
	fi
}

if [ "$GET_BUNDLE_SECRETS" == true ]
then
	decrypt_bundle_secrets
elif [ "${PUT_BUNDLE_SECRETS}" == true ]
then
	encrypt_bundle_secrets
fi

if [ "${DECRYPT}" -eq "1" ]
then
	#Download CONFIG_FILE from S3, decrypt it and copy at desired location
	if [ "${RUN_SECRET_ENTRYPOINT}" == true ] && [ -z "${SERVEROVERRIDE_KEY}" ]; then
		if [ -n "$CONFIG_PATH" ]; then
			APP_CONFIG=${CONFIG_PATH##*/}
			decrypt_config_file
		fi
	fi
else
	#Only Download CONFIG_FILE from S3 to desired location
	if [ "${RUN_SECRET_ENTRYPOINT}" == true ] && [ -z "${SERVEROVERRIDE_KEY}" ]; then
		if [ -n "$CONFIG_PATH" ]; then
			APP_CONFIG=${CONFIG_PATH##*/}
			download_config_file
		fi
	fi
fi

# Retrieve SERVEROVERRIDE_KEY from ssm parameter store or secret manager
if [ "${RUN_SECRET_ENTRYPOINT}" == true ] && [ ! -z "${SERVEROVERRIDE_KEY}" ]; then
	get_serveroverride
fi

# Load the application specific environment variables from S3 secret file into container environment
if [ "${GET_APPS_SECRETS}" == true ]; then
		decrypt_app_secrets
		eval $(cat get_app_secrets | sed 's/^/export /')
else
	if [ ! -z "${QUIET}" ]; then echo "No application specific environment variables to import from S3"; fi
fi

#Load the environment specific  variables from S3 secret file into container environment
if [ "${GET_ENV_SECRETS}" == true ]; then
		decrypt_env_secrets
		eval $(cat get_env_secrets | sed 's/^/export /')
else
	if [ ! -z "${QUIET}" ]; then echo "No environment specific variables to import from S3"; fi
fi



exec "$@"
