#!/bin/bash
set -e

REGION=${AWS_DEPLOY_REGION:-"${AWS_REGION}"}

# Usage: ./sql_deploy.sh --deploy-type fargate|lambda|batch|local 
# Example: ./sql_deploy.sh --deploy-type local 

# Function implementation for Fargate deployment
function fargate() {

if [ -z "$ECS_CLUSTER" ]; then echo "Missing ECS_CLUSTER variable"; exit 1; else echo "ECS_CLUSTER=$ECS_CLUSTER";fi
if [ -z "$ECS_SERVICE_NAME" ]; then echo "Missing ECS_SERVICE_NAME variable"; exit 1; else echo "ECS_SERVICE_NAME=$ECS_SERVICE_NAME";fi
if [ -z "$DB_COMMAND" ]; then echo "Missing DB_COMMAND variable"; exit 1; else echo "DB_COMMAND=$DB_COMMAND";fi
if [ -z "$DEPLOY_ROLE" ]; then echo "Missing DEPLOY_ROLE variable"; exit 1; else echo "DEPLOY_ROLE=$DEPLOY_ROLE";fi

    . ./assume-role.sh --assume-role="${DEPLOY_ROLE}" --deploy-region="${REGION}"

    if [ "${SQL_DEPLOY}" = "true" ]; then echo "Performing database migration and deployment..."

cmd=$(cat <<EOF
{
  "containerOverrides": [
    {
      "name": "$ECS_SERVICE_NAME",
      "command": $DB_COMMAND,
      "environment": [{"name": "purpose", "value": "db-deploy"}]
    } 
  ] 
}
EOF
)


    taskDefinition=$( \
    aws ecs list-task-definitions  \
                                  --region $REGION \
                                  --family-prefix $ECS_SERVICE_NAME \
                                  --output text \
                                  | grep $ECS_SERVICE_NAME | tail -n1 | awk -F '/' '{print $NF}' \
    )

    networkConfig=$( \
    aws ecs describe-services \
        --services=${ECS_SERVICE_NAME} \
        --cluster=${ECS_CLUSTER}  \
        --region=${REGION} \
        --query 'services[0].deployments[0].networkConfiguration' \
        --output json | jq -c  \
    )


    echo "running database deployment/migration using '$taskDefinition' task definition"
    aws ecs run-task  \
                 --region $REGION \
                 --cluster $ECS_CLUSTER \
                 --network-configuration=$networkConfig \
                 --task-definition $taskDefinition \
                 --launch-type=FARGATE \
                 --overrides="$cmd"


        else
            echo "No database migration or deployment needed."
        fi
    }

# Lambda
function lambda() {
echo "Function implementation for Lambda deployment."
if [ -z "$APP_NAME" ]; then echo "Missing APP_NAME variable"; exit 1; else echo "APP_NAME=$APP_NAME";fi
if [ -z "$LAMBDA_FUNCTION_NAME" ]; then echo "Missing LAMBDA_FUNCTION_NAME variable"; exit 1; else echo "LAMBDA_FUNCTION_NAME=$LAMBDA_FUNCTION_NAME";fi
if [ -z "$DB_DEPLOY_URI" ]; then echo "Missing DB_DEPLOY_URI variable"; exit 1; else echo "DB_DEPLOY_URI=$DB_DEPLOY_URI";fi
if [ -z "$DEPLOY_ROLE" ]; then echo "Missing DEPLOY_ROLE variable"; exit 1; else echo "DEPLOY_ROLE=$DEPLOY_ROLE";fi

    . ./assume-role.sh --assume-role="${DEPLOY_ROLE}" --deploy-region="${REGION}"

    if [ "${SQL_DEPLOY}" = "true" ]; then echo "Performing database migration and deployment..."

        #Wait for lambda function to be available
        aws lambda wait function-updated --function-name ${LAMBDA_FUNCTION_NAME}

        # Fetching SQL Deploy Token Value from Shared account SSM parameter
        sqldeploytoken=$(aws ssm get-parameter --region ${REGION} --name /sql-deploy-token --with-decryption --query 'Parameter.Value' --output text)

        # CURL FLASK Endpoint
        echo "Getting current DB version"
        curl -s "https://devtidbits-api.annalect.com/infra/db/" | jq

        echo "Performing DB Migration"

        set +e
        response=$(curl -o - -s -w '%{http_code}' -H "x-token:$sqldeploytoken" "$DB_DEPLOY_URI")
        exit_status=$?
        echo "Exit status code is: $exit_status"
        HTTP_STATUS_CODE=${response: -3}
        echo "HTTP status code: $HTTP_STATUS_CODE"
        HTTP_BODY=${response%???}

        if [ ! $exit_status -eq 0 ]; then
            echo "API Request failed with exist stats $exit_status"
            echo "HTTP status: $HTTP_STATUS_CODE"
            echo "HTTP BODY: $HTTP_BODY"
        else
            if [ ! $HTTP_STATUS_CODE -eq 200  ]; then
                echo "Error HTTP status code: $HTTP_STATUS_CODE"
                echo "Error HTTP BODY: $HTTP_BODY"
                echo "Database migration failed. Starting the deployment rollback"
                #downgrade_output=$(curl -o - -s -w '%{http_code}' -H "x-token:$sqldeploytoken" "$DB_DEPLOY_URI/downgrade")
                # echo "DB Downgrade output is: $downgrade_output"
                # ./assume-role.sh --deploy-region="${REGION}"
                unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
                aws sts get-caller-identity
                ./codebuild-docker-image.sh undo_latest_push
                echo "Code Deployment rollback completed"
                ./codebuild-deployv1.sh --deploy-type=lambda --assume-role="${DEPLOY_ROLE}" --deploy-region="${AWS_DEFAULT_REGION}"
                echo "Rollback lambda update completed"
                exit 1
            else
                echo "HTTP status code: $HTTP_STATUS_CODE"
                echo "HTTP BODY: $HTTP_BODY"
                echo "Database migration completed"
            fi
        fi
        set -e
        
        echo "Getting current DB version"
        curl -s "https://devtidbits-api.annalect.com/infra/db/" | jq
        
    else
        echo "No database migration or deployment needed."
    fi
}

# Batch
function batch() {
  echo "Function implementation for Batch deployment."
    # ...
}

# Function implementation for local testing
function local_testing() {

ECS_CLUSTER="dev-1"
AWS_DEPLOY_REGION="us-east-1"
REGION=${AWS_DEPLOY_REGION:-"${AWS_REGION}"}
ECS_SERVICE_NAME="geolift"
SQL_DEPLOY="true"
command=${DB_COMMAND:-["echo","Hello","World"]}
profile="ann08dev"


if [ "${SQL_DEPLOY}" = "true" ]; then echo "Performing database migration and deployment..."

cmd=$(cat <<EOF
{"containerOverrides": [
    {
      "name": "$ECS_SERVICE_NAME",
      "command": ["$(echo "$command" | sed 's/,/","/g' | sed 's/^.\(.*\).$/\1/')"],
      "environment": [{"name": "purpose", "value": "db-deploy"}]
    } 
  ] 
}
EOF
)

taskDefinition=$( \
aws ecs list-task-definitions --profile $profile \
                              --region $REGION \
                              --family-prefix $ECS_SERVICE_NAME \
                              --output text \
                              | grep $ECS_SERVICE_NAME | tail -n1 | awk -F '/' '{print $NF}' \
)

networkConfig=$( \
aws ecs describe-services --profile $profile \
    --services=${ECS_SERVICE_NAME} \
    --cluster=${ECS_CLUSTER}  \
    --region=${REGION} \
    --query 'services[0].deployments[0].networkConfiguration' \
    --output json | jq -c  \
)


echo "running database deployment/migration using '$taskDefinition' task definition"
aws ecs run-task  --profile $profile \
             --region $REGION \
             --cluster $ECS_CLUSTER \
             --network-configuration=$networkConfig \
             --task-definition $taskDefinition \
             --launch-type=FARGATE \
             --overrides="$cmd"


    else
        echo "No database migration or deployment needed."
    fi
}


# Execute called function
case $1 in
    --deploy-type)
        shift
        case $1 in
            fargate)
                fargate
                ;;
            lambda)
                lambda
                ;;
            batch)
                batch
                ;;
            local)
                local_testing
                ;;
            # Add cases for other deployment types here
            *)
                echo "Unknown deployment type: $1"
                exit 1
                ;;
        esac
        ;;
    *)
        echo "Usage: $0 --deploy-type fargate|batch|lambda|local"
        exit 1
        ;;
esac
