import boto3
import os

"""
Credential module name: getParameterSecrets.py

The module received a list of parameters names and returns the value for them.

- If the parameter name is found as an environment variable, then the value of
    the env. variable is returned.
- If not, then the module tries to fetch the secret value from SSM.

* Usage example 1:
   ```
   from getParameterSecrets import getCredentials
   dsdk_username, dsdk_password  = getCredentials('dev.apps.redshift.dsdk.user','dev.apps.redshift.dsdk.pass')
   ```

* Usage example 2:
```
# it returns the value of the PATH variable
path = getParameterSecrets.getCredentials('PATH')
```
"""

def getCredentials(*requested_param_name):
    """
    Reads a secure parameter from AWS' SSM service.
    The request must be passed a valid parameter name, as well as
    temporary credentials which can be used to access the parameter.
    The parameter's value is returned.
    """

    # returned credentials are saved here
    credentials = []

    # here we store credentials not found in environment
    param_name = []

    for name in requested_param_name:
        # if variable exists in the environment, return this variable
        try:
            credentials.append(os.environ[name])
        except KeyError:
            param_name.append(name)

    if param_name == []:
        return tuple(credentials)

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


    # Store the credentials in a variable
    for name in param_name:
         for secret in response['Parameters']:
            if name == secret['Name']:
                 credentials.append(secret['Value'])


    return tuple(credentials)
