# Wells Fargo DCM and DS3 file upload

## DCM files

### Requirements

* Python3
* Boto3: `pip install boto3`

### Parameters

- `<DATE_YYYYMMDD>` : subsitute with the date to be synchronized in a YYYYMMDD format, for example 20190123 corresponds to January 23rd, 2019
- `<TYPE>` : substitute with IMPRESSION, MATCH, ACTIVITY or ALL. This depends on the type of files that need to be synchonized

### Example command:

```
devops/lambda-deployments (release)$ python3.6 launch-lambda.py \
--name  'annalect_job_submit' \
--qualifier 'production' \
--payload '{
    "annalect_type": "cloudWatchEvent",
    "appName": "prod_generic",
    "jobName": "adhoc-WellsFargo-dcm-python3",
    "jobQueue": "CustomJobQueue",
    "jobDefinition": "CustomJobQueueMultiClientDataFeedJobDef-python3",
    "timeout": 18000,
    "environment": [
        {
            "name": "NOTIFY_ON_SUCCESS",
            "value": "1"
        },
        {
            "name": "NOVALIDATION",
            "value": "1"
        }
    ],
    "jobCommand": [
        "/src/execute.sh",
        "wfDCM",
        "python",
        "dcmFileProcess-new.py",
        "dcm_account6049",
        "<DATE_YYYYMMDD>",
        "<TYPE>"
    ]
}'
```



## DS3 files

### Parameters

- `<DATE_YYYY-MM-DD>` : subsitute with the date to be synchronized in a YYYY-MM-DD format, for example 2019-01-23 corresponds to January 23rd, 2019
- `<TYPE>` : You can specify one, two or three types in the same run. The possibles values are `keyword`, `conversion` or `visit`. This depends on the type of files that need to be synchonized.

NOTE: If `<DATE>` or `<TYPE>` are not specified, the script will run for all 3 types for the previous day. However it is *strongly* encouraged to use at least the `<DATE>` parameter.


## Example command

```
devops/lambda-deployments (release)$ python3.6 launch-lambda.py \
--name  'annalect_job_submit' \
--qualifier 'production' \
--payload '{
    "annalect_type": "cloudWatchEvent",
    "appName": "prod_generic",
    "jobName": "adhoc-WellsFargo-ds3-new",
    "environment": [
        {
            "name": "NOVALIDATION",
            "value": "1"
        },
        {
            "name": "NOTIFY_ON_SUCCESS",
            "value": "1"
        }
    ],
    "jobCommand": [
        "/src/execute.sh",
        "ds3",
        "python",
        "daemon-ds3-new.py",
        "-d",
        "<DATE_YYYY-MM-DD>",
        "-q",
        "<TYPE>",
        "-q",
        "<TYPE>",
        "-q",
        "<TYPE>"
    ]
}'
```
