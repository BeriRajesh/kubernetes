#!/bin/bash
#set -euo pipefail

#
echo "A script to upload serveroverride or secret config file or download and/or update the existing serveroverride file resides in S3."
#read -r -p "Are You Ready to Start? [Y/n] " input
#case $input in
#    [yY][eE][sS]|[yY]);;
#    [nN][oO]|[nN]) exit;;
#    *) echo "Invalid input..."; exit 1;;
#esac


# Validate if appName folder already exists in s3

function validate_config_file_in_s3 () {
	FILE_IN_S3="s3://${SECRETS_BUCKET_NAME}/container-secrets/${BUILD_ENV}/${APP_NAME}/${APP_CONFIG}.encrypted"

    if [ `aws s3 ls --recursive "${FILE_IN_S3}" | wc -l` -eq 1 ]; then
		echo "The encrypted copy of "${APP_CONFIG}" exists in Annalect S3 bucket."
		echo "${FILE_IN_S3}"
	else
		echo "The ${APP_CONFIG} file doesn't exists in s3 for ${APP_NAME} in ${BUILD_ENV}."
		exit
	fi
}


# set Environment Variables
SECRETS_BUCKET_NAME="annalect-cloud-vault"
eval $(aws s3 cp s3://${SECRETS_BUCKET_NAME}/container-secrets/ecs-kms-key - | sed 's/^/export /')

# Decrypt and Download serveroverride file in current directory
function download_config_file () {
    aws s3 cp s3://${SECRETS_BUCKET_NAME}/container-secrets/"${BUILD_ENV}"/"${APP_NAME}"/"${APP_CONFIG}".encrypted .
    echo "Decrypting file locally at your current working directory."
    aws-encryption-cli --decrypt \
    --input "${APP_CONFIG}".encrypted \
    --wrapping-keys key="arn:aws:kms:us-east-1:661095214357:key/${KEY_ID}" \
    --encryption-context AppName="${APP_NAME}" EnvName="${BUILD_ENV}" \
    --metadata-output /tmp/metadata \
    --commitment-policy require-encrypt-require-decrypt \
    --output  "${APP_CONFIG}" \
    --quiet

    if [ $? -eq 0 ]; then
        echo "Please update the "${APP_CONFIG}" downloaded at `pwd`, and then re-run $0 to re-upload."
    fi
  }

# Check if folder for APP_NAME exists in s3
function check_app_folder () {
    wordcount=`aws s3 ls s3://${SECRETS_BUCKET_NAME}/container-secrets/${BUILD_ENV}/${APP_NAME} | wc -l`
    if [[ ${wordcount} -eq 0 ]]; then echo "Folder '${APP_NAME}'' not found in S3";exit 1;fi
  }

# Encrypt serveroverride file
function encrypt_config_file () {
        if [ ! -e "$APP_CONFIG" ]; then
        echo >&2 "error: missing $APP_CONFIG"
        exit 1;
        fi
        aws-encryption-cli --encrypt \
                     --input "${APP_CONFIG}" \
                     --wrapping-keys key="arn:aws:kms:us-east-1:661095214357:key/${KEY_ID}" \
                     --encryption-context AppName="${APP_NAME}" EnvName="${BUILD_ENV}" \
                     --metadata-output /tmp/metadata \
                     --commitment-policy require-encrypt-require-decrypt \
                     --output . \
                     --quiet

        aws s3 cp ${APP_CONFIG}.encrypted s3://${SECRETS_BUCKET_NAME}/container-secrets/${BUILD_ENV}/${APP_NAME}/${APP_CONFIG}.encrypted --sse
}

# Upload serveroverride file from current directory
function upload_config_file () {
    FILE_IN_S3="s3://${SECRETS_BUCKET_NAME}/container-secrets/${BUILD_ENV}/${APP_NAME}/${APP_CONFIG}.encrypted"
    if [ ! -f "${APP_CONFIG}" ]; then
        echo "File '${APP_CONFIG}'' not found"
        ls
        exit 1
    fi

    read -e -p "It assumes you already updated/validated ${PWD}/"${APP_CONFIG}".
This is going to add/replace ${FILE_IN_S3}.
Do you want to continue? [yes/No] " response

    response=${response:-"No"}

    case "$response" in
        [yY][eE][sS]) encrypt_config_file;;
        [Nn]* ) exit;;
            * ) echo -e "\nINVALID INPUT: Please answer yes or no."; upload_config_file;
    esac
}


# Check Build Environment
function check_build_env () {
    echo
    echo 'Please choose the BUILD_ENV and press [ENTER]: '
    options=("dev" "qa" "stg" "prod" "Cancel")

    select env in "${options[@]}"
    do
        case $env in
            "dev")
                BUILD_ENV=$env
                KEY_ID=$KEY_ID_DEV
                echo "The Environment is: $BUILD_ENV"; break
                ;;
            "qa")
                BUILD_ENV=$env
                KEY_ID=$KEY_ID_QA
                echo "The Environment is: $BUILD_ENV"; break
                ;;
            "stg")
                BUILD_ENV=$env
                KEY_ID=$KEY_ID_STG
                echo "The Environment is: $BUILD_ENV"; break
                ;;
            "prod")
                BUILD_ENV=$env
                KEY_ID=$KEY_ID_PROD
                echo "The Environment is: $BUILD_ENV"; break
                ;;
            "Cancel")
                exit
                ;;
            *) echo "INVALID option $REPLY";;
        esac
    done
}

function check_app_name () {
    echo
    read -e -p "Please enter the APP_NAME and press [ENTER]: " APP_NAME
    check_app_folder
    read -e -p "Please enter a name of the serveroverride file or just [ENTER] for default (default is serveroverride.cfg) : " secret
	APP_CONFIG="${secret:-serveroverride.cfg}"
}


function list_register_application_S3_folder () {
    check_build_env
    aws s3 ls "${SECRETS_BUCKET_NAME}"/container-secrets/ --recursive | grep container-secrets/"${BUILD_ENV}" | cut -d/ -f3 | uniq
}

#create new s3 app bucket
function create_new_s3app_bucket () {
    echo
    read -e -p "Please enter the New APP_NAME to create  and press [ENTER]: " APP_NAME
    read -e -p "Please enter name of the Secrets File and press [ENTER]: " APP_CONFIG
    #Check Environment
	check_build_env
	#appname check 
    FILE_IN_S3="s3://${SECRETS_BUCKET_NAME}/container-secrets/${BUILD_ENV}/${APP_NAME}/"
    #echo "App name: $FILE_IN_S3 "
    #aws s3 ls ${SECRETS_BUCKET_NAME}/container-secrets/${BUILD_ENV}/${APP_NAME}/ --recursive | grep container-secrets/${BUILD_ENV}/${APP_NAME}/${APP_CONFIG}
    

    #Create bucket
    touch ${APP_CONFIG}
    upload_config_file
    aws s3 cp ./${SECRETS_FILE_NAME} s3://${SECRETS_BUCKET_NAME}/container-secrets/${BUILD_ENV}/${NEW_APP_NAME}/${SECRETS_FILE_NAME}
	
    echo "New test S3  $APP_NAME has been created under ${BUILD_ENV} environment"
}


echo
echo "Do you wish to download/update the serveroverride file in S3? Please enter your choice: "

options=("download_override" "upload_override" "list_all_available_applications" "create_new_application" "Quit")

select opt in "${options[@]}"
do
    case $opt in
        "download_override")
            check_build_env
            check_app_name
            validate_config_file_in_s3
            download_config_file
            break
            ;;
        "upload_override")
            check_build_env
            check_app_name
            upload_config_file
            break
            ;;
        "list_all_available_applications")
            list_register_application_S3_folder
            break
            ;;
        "create_new_application")
            create_new_s3app_bucket
            break
            ;;
        "Quit")
            break
            ;;
        *) echo "INVALID option $REPLY";;
    esac
done

# Unset the environment variables
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

# END
