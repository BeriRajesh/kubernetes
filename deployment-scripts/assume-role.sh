#!/bin/bash
set -e


# Usage: ./assume-role.sh --assume-role=${DEPLOY_ROLE} --deploy-region=${AWS_DEFAULT_REGION}


for i in "$@"; do
  case $i in
    -a=*|--assume-role=*)
      role="${i#*=}"
      shift # past argument=value
      ;;
    -r=*|--deploy-region=*)
      region="${i#*=}"
      shift # past argument=value
      ;;
    # --default)
    #   DEFAULT=YES
    #   shift # past argument with no value
    #   ;;
    -*|--*)
      echo "Unknown option $i"
      exit 1
      ;;
    *)
      ;;
  esac
done

AWS_DEPLOY_REGION=${region:-"${AWS_DEFAULT_REGION}"}

function assume_role() {

    if [ ! -z "${role}" ]; then
        role=$(aws sts assume-role --role-arn "${role}" --role-session-name deployer-session --duration-seconds 3600)
        KEY=$(echo $role | jq ".Credentials.AccessKeyId" --raw-output)
        SECRET=$(echo $role | jq ".Credentials.SecretAccessKey" --raw-output)
        TOKEN=$(echo $role | jq ".Credentials.SessionToken" --raw-output)
        export AWS_ACCESS_KEY_ID=$KEY
        export AWS_SECRET_ACCESS_KEY=$SECRET
        export AWS_SESSION_TOKEN=$TOKEN
        export AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION

        aws sts get-caller-identity

    else
        unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
        aws sts get-caller-identity
    fi
}

# Excute called function
assume_role

