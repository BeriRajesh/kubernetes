#!/bin/bash
set -euo pipefail

# pip install 'aws-encryption-sdk-cli>2'

if [[ "${QUIET:-}" == false ]]; then
    set -x
fi

#
echo "A script to upload serveroverride or secret config file or download and/or update the existing serveroverride file resides in S3."
read -r -p "Are You Ready to Start? [Y/n] " input
case $input in
    [yY][eE][sS]|[yY]);;
    [nN][oO]|[nN]) exit;;
    *) echo "Invalid input..."; exit 1;;
esac


# Validate if ECS Task Family exists
function validate_apps_task_familiy () {

    task_family="${APP_NAME}"-"${BUILD_ENV}"
    ecs_task_family=$(aws ecs list-task-definition-families --family-prefix "${task_family}" --output text | cut -f 2 | grep "^${task_family}$")

    if [[ "${task_family}" == "${ecs_task_family}" ]]; then
        echo The registered ECS task family for this app is "$ecs_task_family."
    else
        echo "No task_defination named "${task_family}" found in ECS, it appears that the container for ${APP_NAME} is not build in ${BUILD_ENV} yet."
        exit
    fi
}


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
    aws-encryption-cli --decrypt --input "${APP_CONFIG}".encrypted \
    --encryption-context AppName=${APP_NAME} EnvName=${BUILD_ENV} \
    --metadata-output /tmp/metadata \
    --output  "${APP_CONFIG}" \
    --quiet

    if [ $? -eq 0 ]; then
        echo "Please update the "${APP_CONFIG}" downloaded at `pwd`, and then re-run $0 to re-upload."
    fi
  }

# Encrypt serveroverride file
function encrypt_config_file () {
        if [ ! -e "$APP_CONFIG" ]; then
        echo >&2 "error: missing $APP_CONFIG"
        exit 1;
        fi
        aws-encryption-cli --encrypt --input ${APP_CONFIG} \
                     --master-keys key=${KEY_ID} \
                     --encryption-context AppName=${APP_NAME} EnvName=${BUILD_ENV} \
                     --metadata-output /tmp/metadata \
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
                BUILD_ENV=$env; echo "The Environment is: $BUILD_ENV"; break
                ;;
            "qa")
                BUILD_ENV=$env; echo "The Environment is: $BUILD_ENV"; break
                ;;
            "stg")
                BUILD_ENV=$env; echo "The Environment is: $BUILD_ENV"; break
                ;;
            "prod")
                BUILD_ENV=$env; echo "The Environment is: $BUILD_ENV"; break
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
    validate_apps_task_familiy

    echo
    read -e -p "Please enter a name of the serveroverride file or just [ENTER] for default (default is serveroverride.cfg) : " secret
	APP_CONFIG="${secret:-serveroverride.cfg}"
}


function list_register_task_family () {
    check_build_env
    # aws ecs list-task-definition-families --output table | grep -e -$BUILD_ENV
    aws s3 ls "${SECRETS_BUCKET_NAME}"/container-secrets/ --recursive | grep container-secrets/"${BUILD_ENV}" | cut -d/ -f3-
}



# Choose ADE Layer
function check_ade_app_layer () {
    echo
    echo 'Please choose the BUILD_ENV and press [ENTER]: '
    options=("dev" "qa" "prod" "Cancel")

    select env in "${options[@]}"
    do
        case $env in
            "dev")
                BUILD_ENV=$env; echo "The Environment is: $BUILD_ENV"; ADE_ENV=Dev; break
                ;;
            "qa")
                BUILD_ENV=$env; echo "The Environment is: $BUILD_ENV"; ADE_ENV=QA; break
                ;;
            "prod")
                BUILD_ENV=$env; echo "The Environment is: $BUILD_ENV"; ADE_ENV=Prod; break
                ;;
            "Cancel")
                exit
                ;;
            *) echo "INVALID option $REPLY";;
        esac
    done

    echo
    echo 'Please choose the APP_LAYER and press [ENTER]: '
    options=("adeingest" "adeweb" "Cancel")

    select layer in "${options[@]}"
    do
        case $layer in
            "adeingest")
                APP_LAYER=$layer; echo "The ADE Layer is: $APP_LAYER"; ADE_LAYER=ingest; break
                ;;
            "adeweb")
                APP_LAYER=$layer; echo "The ADE Layer is: $APP_LAYER"; ADE_LAYER=web; break
                ;;
            "Cancel")
                exit
                ;;
            *) echo "INVALID option $REPLY";;
        esac
    done

    echo
    read -e -p "Please enter a name of the serveroverride file or just [ENTER] for default (default is adeserveroverride.cfg) : " secret
    APP_CONFIG="${secret:-adeserveroverride.cfg}"
}



#ADE Download - adeserveroverride.cfg
function download_ade_serveroverride () {
    check_ade_app_layer
    aws s3 cp s3://${SECRETS_BUCKET_NAME}/container-secrets/${BUILD_ENV}/${APP_LAYER}/${APP_CONFIG} .
}

#ADE Upload - adeserveroverride.cfg
function upload_ade_serveroverride () {
    check_ade_app_layer
    aws s3 cp ${APP_CONFIG} s3://${SECRETS_BUCKET_NAME}/container-secrets/${BUILD_ENV}/${APP_LAYER}/${APP_CONFIG} --sse
    aws s3 --region us-east-1 cp ${APP_CONFIG} s3://annalect.bootstrap-bucket/ade/${ADE_ENV}/US/${ADE_LAYER}/adeserveroverride.cfg --sse

    # deleting local file
    rm ${APP_CONFIG}
}


echo
echo "Do you wish to download/update the serveroverride file in S3? Please enter your choice: "

options=("download_override" "upload_override" "list_ecs_registered_task_family" "download_ade_serveroverride" "upload_ade_serveroverride" "Quit")

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
        "list_ecs_registered_task_family")
            list_register_task_family
            break
            ;;
        "download_ade_serveroverride")
            download_ade_serveroverride
            break
            ;;
        "upload_ade_serveroverride")
            upload_ade_serveroverride
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
