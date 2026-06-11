import configparser
import requests
import json
import sys

from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

def getConfig():
    """
        Returns a configuration object from a serveroverride.cfg
        todo: possibly merge serverbase and serveroverride

    """

    config = configparser.ConfigParser()
    config.read('serveroverride.cfg')

    return config


def submit_job(arguments={}, **kwargs):
    """ Submits asynchronous job to Batch/ECS environment.

    Example:
        This command would launch a container identified as kates_container,
        with the command `python3 my_script.py '{"name": "jane doe"}'`

        To recover the argument, the script should run
            ```
            import json
            import sys
            my_parameter_dictionary = json.loads(sys.argv[0])
            ```
        import annalect_helper as ah

        ah.submit_job(
            appName="kates_container"),
            jobCommand="python3 my_script.py"
            payload=json.dumps({"name": "jane doe"}),
            jobName="intuit-generating-images-101010"
        )



    The module extracts other needed information from `serveroverride.cfg`.

    This function only has keyword arguments:

    Keyword Arguments:
        appName (str): Required. Corresponds to the identifier of the job/container needed to be launched.

        jobCommand (str): Required. Command to send to the docker container.

        arguments (str): Optional. JSON encoded dictionary passed to the command as a first parameter.

        jobName (str): Optional. Human readable identifier for the job being submitted. Ideally unique.


    """

    # get the configuration
    config = getConfig()

    appName = kwargs["appName"]
    jobName = kwargs["jobName"]
    jobCommand = kwargs["jobCommand"]
    arguments = arguments

    region = "us-east-1"
    endPoint = config['AsyncJobs']['endpoint']
    apiKey = config['AsyncJobs']['apiKey']
    host = config['AsyncJobs']['host']
    auth = None

    auth = BotoAWSRequestsAuth(
        aws_host=host,
        aws_region=region,
        aws_service = 'execute-api'
    )


    payload = {
        "appName": appName,
        "jobCommand": jobCommand,
        "arguments": arguments,
        "jobName": jobName,
    }

    headers = {"x-api-key": apiKey, "Host": host}
    payload_json = json.dumps(payload)

    # print(f"endp: {endPoint}")
    # print(f"endpheaders: {headers}")
    # print(f"auth: {auth}")
    # print(f"payload: {json.dumps(payload)}")
    # sys.exit()

    req = requests.post(
        endPoint,
        headers=headers,
        json=payload,
        auth=auth,
    )
    return req
