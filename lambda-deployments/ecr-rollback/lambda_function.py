"""
This Lambda function lives in devops repository.
Modifications made here might be overwritten and **lost forever** without notice.

You can easily upload a new version by executing

    cd <path/to/devopsrepository>
    cd lambda-deployments/ecr-rollback

    ./build_lambda.sh
"""
import json
import rollback_deployments

def lambda_handler(event, context):
    """ Handler that takes care of all specific logic regarding event"""

    try:
        response = rollback_deployments.rollback_deployments(event)
        exit_code = 200
    except Exception as error:
        exit_code = 503
        response = str(error)

    return {
        'statusCode': exit_code,
        'body': json.dumps(response, default=str),
        'headers': {
            'Content-Type': 'application/json',
        },
    }
