#!/bin/bash
set -e
function application() {
 #Define functions to get endpoints
  get_endpoint() {
    case "$1" in
      "dev")
        echo "https://dev$2-sidecar.annalect.com/v1/keys"
        ;;
      "qa")
        echo "https://qa$2-sidecar.annalect.com/v1/keys"
        ;;
      "stg")
        echo "https://stg$2-sidecar.annalect.com/v1/keys"
        ;;
      "prod")
        echo "https://$2-sidecar.annalect.com/v1/keys"
        ;;
      *)
        echo "Invalid environment"
        exit 1
        ;;
    esac
  }


  # Define a list of valid environments
  environment_options=("dev" "qa" "stg" "prod")

  # Prompt the user to select an environment from the list
  PS3="Select environment from the list: "
  select env in "${environment_options[@]}"; do
    case $env in
      "dev"|"qa"|"stg"|"prod")
        break
        ;;
      *)
        echo "Invalid choice. Please select an environment from the list."
        ;;
    esac
  done

  echo -e "\n"

#   # Define a list of side-car options
#   sidecar_options=("conversation" "orchestration" "dictionary")
    side_car=conversation   

#   # Present a menu of side-car choices to the user
#   PS3="Choose a side-car name from the list: "
#   select side_car in "${sidecar_options[@]}"; do
#     case $side_car in
#       "conversation"|"orchestration"|"dictionary")
#         break
#         ;;
#       *)
#         echo "Invalid choice. Please select a side-car from the list."
#         ;;
#     esac
#   done

  # Get the endpoint based on the selected environment and side-car
  endpoint=$(get_endpoint "$env" "$side_car")


  # Get the application_name name
  echo "Please enter the name of the application (e.g. 'campaign'):"
  while true; do
    read application_name
    if [[ -n $application_name ]]; then
      if [[ ${#application_name} -gt 64 ]]; then
          echo "Error: Input exceeds 64 characters."
      elif [[ ! $application_name =~ ^[a-zA-Z0-9_.-]{1,64}$ ]]; then
          echo 'Error: Input contains invalid characters. Valid characters are letters, numbers and the symbols `_` `-` `.`'
      else
        break
      fi
    else
      echo "application_name field is mandatory. Please enter a value."
    fi
  done

  echo "Please enter the name of the owner (e.g. 'John'):"
  while true; do
    read owner_name
    if [[ -n $owner_name ]]; then
      if [[ ${#owner_name} -gt 64 ]]; then
          echo "Error: Input exceeds 64 characters."
      elif [[ ! $owner_name =~ ^[a-zA-Z0-9_.\ -]{1,64}$ ]]; then
          echo 'Error: Input contains invalid characters. Valid characters are letters, numbers and the symbols `_` `-` `.`'
      else
        break
      fi
    else
      echo "owner_name field is mandatory. Please enter a value."
    fi
  done

  # Prompt for email contact
  while true; do
    read -p "Enter email address for project/owner contact: " owner_email
    if [[ -n $owner_email ]]; then
      if [[ $owner_email =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$ ]]; then
        break
      else
        echo "Invalid email address. Please enter a valid email address."
      fi
    else
      echo "Email contact is mandatory. Please enter an email address."
    fi
  done

  while true; do
    read -p "Enter description (e.g., API Key for project XYZ): " description
    if [[ -n $description ]]; then
      break
    else
      echo "Description is mandatory. Please enter a value."
    fi
  done


  while true; do
    # Provide an example in the prompt message for days_until_expiration
    read -p "Enter number of days after which the script will get expired (default is 90 days, e.g., 90): " days_until_expiration

    # Set the default value to 30 if the input is empty
    days_until_expiration="${days_until_expiration:-90}"

    # Check if the input is a number between 1 and 365
    if [[ $days_until_expiration =~ ^[1-9][0-9]{0,2}$ && $days_until_expiration -le 365 ]]; then
      break
    else
      echo "Invalid input. Please enter a number between 1 and 365."
    fi
  done

  # Prompt for account number
  while true; do
      read -p "Please enter the account number for the requesting account: " account
      # Validate that input is a 12-digit number
      if [[ $account =~ ^[0-9]{12}$ ]]; then
          break
      else
          echo "Invalid account number. It must be a 12-digit number."
      fi
  done

  # Prompt for agency name
  while true; do
      read -p "Please enter the agency name:  " agency_name
      # Validate that input is a 12-digit number
      if [[ $agency_name =~ ^[a-zA-Z0-9/_-]+$ ]]; then
          agency=$agency_name
          break
      else
          echo "Invalid input. agency name can only contain alphanumeric characters and the special characters -, _, or /"
      fi
  done

  while true; do
      read -p "Please provide the user load:  " user_load
      # Validate that input is a 12-digit number
      if [[ "$user_load" =~ ^[0-9]+$ ]] && (( user_load >= 0 && user_load <= 1000 )); then
          break
      else
          echo "Invalid user load."
      fi
  done
  

  # Define a list of valid environments
  model_plan_options=("Tier 1" "Tier 2" "Tier 3")
  # Prompt for model_plan
  PS3="Select model plan from the list: "
  select model_plan in "${model_plan_options[@]}"; do
    case $model_plan in
      "Tier 1"|"Tier 2"|"Tier 3")
        break
        ;;
      *)
        echo "Invalid choice. Please select a model plan from the list."
        ;;
    esac
  done


  # Construct or capture the SSM path
  ssm_path="/${env}/${application_name}/serveroverride"
  while true; do
      echo "The constructed SSM parameter path is: $ssm_path"
      read -p "Do you want to accept this SSM parameter path? (y/n): " choice

      case $choice in
          [Yy]* )
              break
              ;;
          [Nn]* )
              while true; do
                  read -p "Enter your own ssm_path: " user_ssm_path
                  # Validate user input
                  if [[ $user_ssm_path =~ ^[a-zA-Z0-9/_-]+$ ]]; then
                      ssm_path=$user_ssm_path
                      break
                  else
                      echo "Invalid input. ssm_path can only contain alphanumeric characters and the special characters -, _, or /"
                  fi
              done
              break
              ;;
          * )
              echo "Please answer y or n."
              ;;
      esac
  done


  # Prompt the user to enter the admin token
  while true; do
    read -s -p "Enter the admin token (e.g., YourAdminToken123 - input will be hidden): " admin_token
    if [[ -n $admin_token && ${#admin_token} -ge 32 ]]; then
      break
    else
      echo "Admin token is mandatory and should be greater than or equal to 32 characters. Please enter a valid value."
    fi
  done


  echo -e "\nValues entered by the user are:"
  echo "Environment: $env"
  echo "Endpoint: $endpoint"
  echo "application_name: $application_name"
  echo "Owner Name: $owner_name"
  echo "owner/project Email Contact:" $owner_email
  echo "Description: $description"
  echo "Side-Car Name: $side_car"
  echo "Days Until Expiration: $days_until_expiration"
  echo "Agency Name: $agency_name"
  echo "User Load: $user_load"
  echo "Model Plan: $model_plan"
  echo "Requesting Account: $account"
  echo "SSM Parameter Path: $ssm_path"

  echo -e "\n"

  # Accept "yes" or "y" as valid input for confirmation
  read -p "If these are the correct values entered, then enter yes (y) to continue; otherwise, enter no: " yes_or_no

  echo -e "\n"

  if [[ $yes_or_no == "yes" || $yes_or_no == "y" ]]; then
    echo "Sending API request to $endpoint"
    {
      curl_output=$(curl -X POST -s -w "%{http_code}" -o >(cat) "$endpoint" \
      -H "accept: application/json" \
      -H "x-admin-token: $admin_token" \
      -H "Content-Type: application/json" \
      -d "{
            \"owner_name\": \"$owner_name\",
            \"description\": \"$description\",
            \"model_plan\": \"$model_plan\",
            \"user_load\": \"$user_load\",
            \"owner_email\": \"$owner_email\",
            \"agency\": \"$agency\",
            \"token_type\": \"application\",
            \"application_name\": \"$application_name\",
            \"days_until_expiration\": \"$days_until_expiration\",
            \"prefix\": \"$env\",
            \"allow_duplicate_owner\": \"true\",
            \"ssm_path\": \"$ssm_path\",
            \"account\": \"$account\",
            \"threshold_action\": \"notify\"
            }")
      exit_code="${PIPESTATUS[0]}"
    }

    if [ "$exit_code" -eq 0 ]; then
      http_status="${curl_output: -3}"
      api_response="${curl_output%???}"
      if [ "$http_status" -eq 201 ]; then
        echo "Token created successfully. Here's the API Token for $project that you can share securely via SecureShare, or add to SSM at $ssm_path: $api_response"
      else
        echo "API call failed with HTTP status code $http_status and response output $api_response. Please connect with DevOps to investigate the issue."
      fi
    else
      echo "Curl command failed with exit code $exit_code. Please connect with DevOps to investigate the issue."
    fi
  fi
  }

##AOK
function user() {
  # Define functions to get endpoints
  get_endpoint() {
    case "$1" in
      "dev")
        echo "https://dev$2-sidecar.annalect.com/v1/keys"
        ;;
      "qa")
        echo "https://qa$2-sidecar.annalect.com/v1/keys"
        ;;
      "stg")
        echo "https://stg$2-sidecar.annalect.com/v1/keys"
        ;;
      "prod")
        echo "https://$2-sidecar.annalect.comv1/keys"
        ;;
      *)
        echo "Invalid environment"
        exit 1
        ;;
    esac
  }

  # Define a list of valid environments
  environment_options=("dev" "qa" "stg" "prod")

  # Prompt the user to select an environment from the list
  PS3="Select environment from the list: "
  select env in "${environment_options[@]}"; do
    case $env in
      "dev"|"qa"|"stg"|"prod")
        break
        ;;
      *)
        echo "Invalid choice. Please select an environment from the list."
        ;;
    esac
  done

  echo -e "\n"

  side_car=conversation 

#   # Define a list of side-car options
#   sidecar_options=("conversation" "orchestration" "dictionary")

#   # Present a menu of side-car choices to the user
#   PS3="Choose a side-car name from the list: "
#   select side_car in "${sidecar_options[@]}"; do
#     case $side_car in
#       "conversation"|"orchestration"|"dictionary")
#         break
#         ;;
#       *)
#         echo "Invalid choice. Please select a side-car from the list."
#         ;;
#     esac
#   done


#   echo -e "\n"

#   # Get the endpoint based on the selected environment and side-car
  endpoint=$(get_endpoint "$env" "$side_car")

  # Get the application_name name
  echo "Please enter the name of the application (e.g. 'campaign'):"
  while true; do
    read application_name
    if [[ -n $application_name ]]; then
      if [[ ${#application_name} -gt 64 ]]; then
          echo "Error: Input exceeds 64 characters."
      elif [[ ! $application_name =~ ^[a-zA-Z0-9_.-]{1,64}$ ]]; then
          echo 'Error: Input contains invalid characters. Valid characters are letters, numbers and the symbols `_` `-` `.`'
      else
        break
      fi
    else
      echo "application_name field is mandatory. Please enter a value."
    fi
  done

  echo "Please enter the name of the owner (e.g. 'John'):"
  while true; do
    read owner_name
    if [[ -n $owner_name ]]; then
      if [[ ${#owner_name} -gt 64 ]]; then
          echo "Error: Input exceeds 64 characters."
      elif [[ ! $owner_name =~ ^[a-zA-Z0-9_.\ -]{1,64}$ ]]; then
          echo 'Error: Input contains invalid characters. Valid characters are letters, numbers and the symbols `_` `-` `.`'
      else
        break
      fi
    else
      echo "owner_name field is mandatory. Please enter a value."
    fi
  done

  # Prompt for email contact
  while true; do
    read -p "Enter email address for owner contact: " owner_email
    if [[ -n $owner_email ]]; then
      if [[ $owner_email =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$ ]]; then
        break
      else
        echo "Invalid email address. Please enter a valid email address."
      fi
    else
      echo "Email contact is mandatory. Please enter an email address."
    fi
  done

  # Make the "description" field mandatory
  while true; do
    read -p "Enter description (e.g., API Key for project XYZ): " description
    if [[ -n $description ]]; then
      break
    else
      echo "Description is mandatory. Please enter a value."
    fi
  done

  while true; do
    # Provide an example in the prompt message for days_until_expiration
    read -p "Enter number of days after which the script will get expired (default is 90 days, e.g., 90): " days_until_expiration

    # Set the default value to 30 if the input is empty
    days_until_expiration="${days_until_expiration:-90}"

    # Check if the input is a number between 1 and 365
    if [[ $days_until_expiration =~ ^[1-9][0-9]{0,2}$ && $days_until_expiration -le 365 ]]; then
      break
    else
      echo "Invalid input. Please enter a number between 1 and 365."
    fi
  done


  # Prompt for agency name
  while true; do
      read -p "Please enter the agency name:  " agency_name
      # Validate that input is a 12-digit number
      if [[ $agency_name =~ ^[a-zA-Z0-9/_-]+$ ]]; then
          agency=$agency_name
          break
      else
          echo "Invalid input. agency name can only contain alphanumeric characters and the special characters -, _, or /"
      fi
  done

  # while true; do
  #     read -p "Please provide the user load:  " user_load
  #     # Validate that input is a 12-digit number
  #     if [[ "$user_load" =~ ^[0-9]+$ ]] && (( user_load >= 0 && user_load <= 1000 )); then
  #         break
  #     else
  #         echo "Invalid user load."
  #     fi
  # done

  # # Define a list of valid environments
  # model_plan_options=("Tier 1" "Tier 2" "Tier 3")
  # # Prompt for model_plan
  # PS3="Select model plan from the list: "
  # select model_plan in "${model_plan_options[@]}"; do
  #   case $model_plan in
  #     "Tier 1"|"Tier 2"|"Tier 3")
  #       break
  #       ;;
  #     *)
  #       echo "Invalid choice. Please select a model plan from the list."
  #       ;;
  #   esac
  # done


  # Prompt the user to enter the admin token
  while true; do
    read -p "Enter the admin token (e.g., YourAdminToken123): " admin_token
    if [[ -n $admin_token && ${#admin_token} -ge 32 ]]; then
      break
    else
      echo "Admin token is mandatory and should be greater than or equal to 32 characters. Please enter a valid value."
    fi
  done


  echo -e "\nValues entered by the user are:"
  echo "Environment: $env"
  echo "Endpoint: $endpoint"
  echo "application_name: $application_name"
  echo "Owner Name: $owner_name"
  echo "owner/project Email Contact:" $owner_email
  echo "Description: $description"
  echo "Side-Car Name: $side_car"
  echo "Days Until Expiration: $days_until_expiration"
  echo "Agency Name: $agency_name"

  echo -e "\n"

  # Accept "yes" or "y" as valid input for confirmation
  read -p "If these are the correct values entered, then enter yes (y) to continue; otherwise, enter no: " yes_or_no

  echo -e "\n"

  if [[ $yes_or_no == "yes" || $yes_or_no == "y" ]]; then
  # Make the API request and capture the output
  api_response=$(curl -s -X POST "$endpoint" \
    -H "accept: application/json" \
    -H "x-admin-token: $admin_token" \
    -H "Content-Type: application/json" \
    -d "{
          \"owner_name\": \"$owner_name\",
          \"description\": \"$description\",
          \"model_plan\": \"Tier 1\",
          \"user_load\": \"15\",
          \"owner_email\": \"$owner_email\",
          \"agency\": \"$agency\",
          \"token_type\": \"user\",
          \"application_name\": \"$application_name\",
          \"days_until_expiration\": \"$days_until_expiration\",
          \"prefix\": \"$env\",
          \"allow_duplicate_owner\": \"true\",
          \"threshold_action\": \"notify\"
        }")
    if [[ $? -eq 0 ]]; then
      echo "API request successful."
      echo "Here's the API Token for $owner that you can share securely via SecureShare: $api_response"
    else
      echo "API request failed. Please connect with DevOps to investigate the issues."
    fi
  fi
  }
# Excute called function
$1
