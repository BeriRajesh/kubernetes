#  Manage Secrets using AWS SSM Parameter Store

##  Simple Secrets Management via AWS’ EC2 Parameter Store for keeping secrets in a structured way

##  Organizing Parameters into Hierarchies
Parameter Store allows to organize parameters in a hierarchical manner to represent common groups, such as environments (e.g., dev/qa/prod), or applications. Following this will be easy to provide only fine-grained access to particular application or container task.

##  Hierarchical Parameters - Naming Convention
* <env>.<app>.redshift.<dbname>.user
* <env>.<app>.redshift.<dbname>.pass
* <env>.<app>.mysql.<dbname>.user
* <env>.<app>.mysql.<dbname>.pass
* <env>.<app>.postgresql.<dbname>.user
* <env>.<app>.postgresql.<dbname>.pass


##  Examples of Hierarchical Parameters:
* prod.journey.redshift.dsdk.user
* prod.journey.redshift.dsdk.pass
* prod.journey.mysql.adedb.user
* prod.journey.mysql.adedb.pass
* prod.journey.postgresql.abdb.user
* prod.journey.postgresql.abdb.pass


##  Create the parameters using CLI
Create the configuration parameters using the AWS CLI or AWS Management Console. For example, the CLI command to create the API key parameter is:

`aws ssm put-parameter --name "prod.journey.db.dsdk-user" --type "String" --value "dsdkappuser"`

`aws ssm put-parameter --name "prod.journey.db.dsdk-pass" --type "SecureString" --value "Password123"`

##  Update/Overrite the parameter using CLI
`aws ssm put-parameter --name "prod.journey.db.dsdk-pass --type "SecureString" --value "Pa55w0rd4"  --overwrite`


##  Retrieve your application configuration parameters using CLI
`aws ssm get-parameters --region us-east-1 --names "/prod/redshift/dsdk-v0p1-annalect/dsdkadmin" --with-decryption --query "Parameters[0].Value" --output text`

##  Retrieve credentials using python
- Python module: getParameterSecrets.py
- Usage example: (see getPass.py)

```python
from getParameterSecrets import getCredentials
dsdk_username, dsdk_password  = getCredentials('dev.apps.redshift.dsdk.user','dev.apps.redshift.dsdk.pass')
```

## Fetching all parameters
Useful to fetch a parameter name that we don't remember correctly:

`aws ssm describe-parameters`

# Examples
(full updated code in original file)

`getParameterSecrets.py`
```python
import boto3

# Credential module name: getParameterSecrets.py
#Usage example:
#from getParameterSecrets import getCredentials
#dsdk_username, dsdk_password  = getCredentials('dev.apps.redshift.dsdk.user','dev.apps.redshift.dsdk.pass')

def getCredentials(*param_name):
    """
    This function reads a secure parameter from AWS' SSM service.
    The request must be passed a valid parameter name, as well as
    temporary credentials which can be used to access the parameter.
    The parameter's value is returned.
    """
    # Create the SSM Client
    ssm = boto3.client('ssm',
        region_name='us-east-1'
    )

    # Get the requested parameter
    response = ssm.get_parameters(
        Names=list(param_name),
        WithDecryption=True
    )

    # Check for Invalid Parameters
    if response['InvalidParameters']:
        raise Exception("InvalidParameters: " + str(response['InvalidParameters']))

    credentials = []

    # Store the credentials in a variable
    for name in param_name:
         for secret in response['Parameters']:
            if name == secret['Name']:
                 credentials.append(secret['Value'])


    return tuple(credentials)
```

`getPass.py`
```python
import boto3
from getParameterSecrets import getCredentials
dsdk_username, dsdk_password  = getCredentials('dev.app.redshift.dsdk.user','dev.app.redshift.dsdk.pass')

print 'dsdk_password  =', dsdk_password
print 'dsdk_username  =', dsdk_username
```