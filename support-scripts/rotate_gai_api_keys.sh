#!/bin/bash

AWS_REGION="${AWS_REGION:-us-east-1}"
ROTATION_DEADLINE="${ROTATION_DEADLINE:-7}" # keys expiring in less than this number of days will be rotated
EXPIRATION_AGE="${EXPIRATION_AGE:-90}" # this expiration age will be used when creating new keys

ACCEPTABLE_ENVIRONMENTS="dev qa stg prod"
ACCEPTABLE_SIDECARS="conversation dictionary orchestration"


check_value() {
    local error_message=""
    local value="$1"
    local valid_values="$2"
    local name="$3"

    if [[ -z $value ]]; then
        error_message+="Error: $name is not set.\n"
        return
    fi

    if [[ $value =~ [[:space:]] ]]; then
        error_message+="Error: $name must be initialized to exactly one of the following values: $valid_values \n"
        return
    fi

    if ! [[ $valid_values =~ (^|[[:space:]])$value($|[[:space:]]) ]]; then
        error_message+="Error: $name must be initialized to one of the following values: $valid_values \n"
    fi
    echo $error_message
}


upload_to_ssm() {
    local ssm_path=$1
    local new_api_key=$2
    local old_value new_value

    old_value=$(aws ssm get-parameter --region $AWS_REGION --name "$ssm_path" --with-decryption --query "Parameter.Value" --output text)
    if [ $? -ne 0 ]; then
        echo "Failed to retrieve the current value of the SSM parameter: $ssm_path"
        return 1
    fi

    sidecar_service_upper=$(echo "$SIDECAR_SERVICE" | tr '[:lower:]' '[:upper:]')
    new_value=$(echo "$old_value" | sed -E "s/(${sidecar_service_upper}_API_KEY)[[:space:]]*=[[:space:]]*.*/\1 = $new_api_key/")


    # KMS_KEY_ARN may or may not be set
    if [ -n "$KMS_KEY_ARN" ]; then
        aws ssm put-parameter \
            --region "$AWS_REGION" \
            --name "$ssm_path" \
            --value "$new_value" \
            --type "SecureString" \
            --overwrite \
            --key-id "$KMS_KEY_ARN" > /dev/null 2>&1
    else
        aws ssm put-parameter \
            --region "$AWS_REGION" \
            --name "$ssm_path" \
            --value "$new_value" \
            --type "SecureString" \
            --overwrite > /dev/null 2>&1
    fi

    if [ $? -ne 0 ]; then
        echo "Failed to update the SSM parameter at $ssm_path"
        return 1
    else
        echo "Successfully updated the SSM parameter at $ssm_path with the new API key."
        return 0
    fi
}


create_new_key() {
    local project=$1
    local description=$2
    local prefix=$3
    local account=$4
    local email_contact=$5
    local ssm_path=$6

    {
        curl_output=$(curl -X POST -s -w "%{http_code}" -o >(cat) "$API_ENDPOINT" \
        -H "accept: application/json" \
        -H "x-admin-token: $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"owner\": \"$project\",
            \"description\": \"$description\",
            \"days_until_expiration\": $EXPIRATION_AGE,
            \"prefix\": \"$ENVIRONMENT\",
            \"allow_duplicate_owner\": true,
            \"additional_info\": {
                \"account\": \"$account\",
                \"email_contact\": \"$email_contact\",
                \"ssm-path\": \"$ssm_path\"
            }
            }")
        exit_code="${PIPESTATUS[0]}"
    }

    if [ "$exit_code" -eq 0 ]; then
        http_status="${curl_output: -3}"
        if [ "$http_status" -eq 201 ]; then
            api_response="${curl_output%???}"
            api_response="${api_response#\"}"
            api_response="${api_response%\"}"
            echo $api_response
            return 0
        else
            echo "Key creation API call failed with HTTP status code $http_status and response output $api_response"
            return 1
        fi
    else
        echo "Key creation curl command failed with exit code $exit_code"
        return 1
    fi
}


delete_key() {
    local key_id=$1

    if [[ "$key_id" == "null" ]]; then
        echo "Error: Key ID cannot be null. Unable to delete key"
        return 1
    fi

    echo "Deleting key with ID $key_id"
    echo
    key_endpoint="${API_ENDPOINT}/${key_id}"

    {
        curl_output=$(curl -X DELETE -s -w "%{http_code}" -o >(cat) $key_endpoint -H "x-admin-token: $ADMIN_TOKEN")
        exit_code="${PIPESTATUS[0]}"
    }
    if [ "$exit_code" -eq 0 ]; then
        http_status="${curl_output: -3}"
        api_response="${curl_output%???}"
        if [ "$http_status" -eq 204 ]; then
            echo "Token successfully deleted"
            return 0
        else
            echo "Key deletion API call failed with HTTP status code $http_status:"
            echo "$api_response"
            return 1
        fi
    else
        echo "Key creation curl command failed with exit code $exit_code"
        echo "$curl_output"
        return 1
	fi
}


# Initialize
error_message=$(check_value "$ENVIRONMENT" "$ACCEPTABLE_ENVIRONMENTS" "ENVIRONMENT")
error_message+=$(check_value "$SIDECAR_SERVICE" "$ACCEPTABLE_SIDECARS" "SIDECAR_SERVICE")
if [[ -z $ENVIRONMENT ]]; then
    error_message+="Error: env var ENVIRONMENT is not set \n"
fi
if [[ -z $SIDECAR_SERVICE ]]; then
    error_message+="Error: env var SIDECAR_SERVICE is not set \n"
fi
if [[ -z $ADMIN_TOKEN ]]; then
    error_message+="Error: env var ADMIN_TOKEN is not set \n"
fi
if [[ -n $error_message ]]; then
    echo -e "$error_message"
    exit 1
fi

# Query API for key data
env=$ENVIRONMENT
if [ "$env" == "prod" ]; then
    env=""
fi
API_ENDPOINT="https://$env$SIDECAR_SERVICE-sidecar.annalect.com/keys"
echo "Using API endpoint $API_ENDPOINT"
{
    curl_output=$(curl -s -w "$%{http_code}" -o >(cat) \
                    -X 'GET' "$API_ENDPOINT?limit=1000" \
                    -H "x-admin-token: $ADMIN_TOKEN" \
                    -H "accept: application/json" \
                    -H "Content-Type: application/json")
    exit_code="${PIPESTATUS[0]}"
}
http_status="${curl_output: -3}"
api_response="${curl_output%????}"
if [ "$exit_code" -eq 0 ]; then
    if [ "$http_status" -eq 200 ]; then
        keys_json=$(echo $api_response | jq)
    else
        echo "GET request to $API_ENDPOINT failed with error $http_status: $api_response"
        exit 1
    fi
else
    echo "Curl command failed with exit code $exit_code"
    exit 1
fi

# Only consider the key with the latest expiration date for any given set of keys that share the same owner and additional_info values
newest_keys=$(echo $keys_json | jq '[.[] |
    {owner, expiration_datetime, additional_info} |
    .additional_info |= fromjson] |
    group_by(.owner + .additional_info.account + .additonal_info.serveroverride) |
    map(max_by(.expiration_datetime))')
len=$(echo $newest_keys | jq length)

# Iterate over keys and update if necessary
for ((i=0; i<len; i++)); do
    key_id=$(echo $newest_keys | jq -r ".[$i].id")
    project=$(echo $newest_keys | jq -r ".[$i].owner")
    description=$(echo $newest_keys | jq -r ".[$i].description")
    additional_info=$(echo $newest_keys | jq -r ".[$i].additional_info")
    account=$(echo $additional_info | jq -r ".account")
    access_project=$(echo $additional_info | jq -r ".\"access-project\"")
    email_contact=$(echo $additional_info | jq -r ".\"email_contact\"")
    ssm_path=$(echo $newest_keys | jq -r ".[$i].additional_info" | jq -r ".\"ssm-path\"")
    creation_datetime=$(echo $newest_keys | jq -r ".[$i].creation_datetime")
    expiration_datetime=$(echo $newest_keys | jq -r ".[$i].expiration_datetime")

    # Calculate days until expiration
    current_time=$(date +%s)
    expiration_time=$(echo $expiration_datetime | cut -d '.' -f 1)  # Convert to integer (whole seconds)
    let "days_until_expiration = ($expiration_time - $current_time) / 86400" # 86400 seconds in a day

    if [[ "$days_until_expiration" -le "$ROTATION_DEADLINE" ]]; then
        echo "Key for project $project with SSM path $ssm_path is expiring in $days_until_expiration days and needs to be rotated"
        # Check for 'null' and handle accordingly
        if [[ "$project" == "null" || "$prefix" == "null" || "$account" == "null" || "$ssm_path" == "null" ]]; then
            echo "Error: One or more of the required parameters is 'null'. Unable to create new key."
            continue
        fi
        # Optional parameters get an empty string instead of "null"
        [[ "$description" == "null" ]] && description=""

        echo "Creating new key with values: Environment: $ENVIRONMENT; Endpoint: $API_ENDPOINT; Project: $project; Description: $description; Sidecar Service: $SIDECAR_SERVICE; Days Until Expiration: $EXPIRATION_AGE; Requesting Account: $account; Email Contact: $email_contact; SSM Path: $ssm_path"
        echo
        create_output=$(create_new_key "$project" "$description" "$ENVIRONMENT" "$account" "$email_contact" "$ssm_path")
        if [ $? -eq 0 ]; then
            new_api_key=$create_output
            echo "Token for project $project created successfully. Uploading to SSM at $ssm_path"
            upload_to_ssm $ssm_path $new_api_key
            if [ $? -eq 0 ]; then
                # TODO: Enable key deletion when API call is ready
                x=0
                #delete_key $key_id
            else
                echo "Error uploading to SSM - old key $key_id will not be deleted"
            fi
        else
            error=$create_output
            echo $error
            echo "Error creating new key; old key $key_id will not be deleted"
        fi
    else
        x=0
        echo "Key for project $project with SSM path $ssm_path does not expire for $days_until_expiration days and does not need to be rotated"
    fi
done
