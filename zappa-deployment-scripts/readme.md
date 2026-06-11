# Zappa Deployments

# Requirements to run `zappa-deploy.sh`

- The project to deploy needs to be a repository in the projects/ folder
- The configuration files for the project need to be places in s3://annalect-annalect-zappa/projects-conf
    - with name: zappa_settings-<repo name>_<branch_name>.json
- The virtual environment must be named 'venv' and added to .gitigore file
- There should be one configuration file per project deployed
- The name of this file must be: `zappa_settings-${STAGE}.json` where $STAGE=<project_name>_<branch_name>[_<suffix>].
- Also the script only does a `zappa update`, meaning that a first manual deployment must already have been made for the STAGE.
    - When deploying a lambda function for first time, one has to configure a VPC, Subnets and security group. For initial deployments (default values are on the zappa_settings template)
        - VPC:
            -`vpc-41948723 (10.5.224.0/20) | Annalect-US-VPC`
        - Subnets:
            - `subnet-cd5b25e5 (10.5.226.128/25) | us-east-1a DEV-1-PRIMARY-PRIVATE`
            - `subnet-f81b268c (10.5.227.128/25) | us-east-1b DEV-1-FAILOVER-PRIVATE`
        - Security Group:
            - `sg-c752958d (zappa-lambda-rds) | zappa-lambda-rds`
- The configuration file of the project (`zappa_settings.json`) looks like like copied below, but there is a template file in `s3://annalect-annalect-zappa/general-conf/zappa_settings-STAGE.sample.json`

** Please notice**
*) the `bucket_name` is the same among all zappa deployed projects
*) the `role_name` is the same among all zappa deployed projects
*) the `project_name` is the same among all zappa deployed projects
*) You can add `slim_handler` option to manage projects greated than 50Mb.
*) `profile_name` corresponds to the role assumed by zappa when deploying, is the same among all zappa deployed projects
*) subnets and security groups can be configured on a per-project basis

Please refer to `https://github.com/Miserlou/Zappa` for additional documentation.

```
{
    "<repo name>_<branch>[_<optional suffix>]": {
        "app_function": "src.server.app",
        "aws_region": "us-east-1",
        "profile_name": "service.zappa_deployments",
        "project_name": "zappa",
        "runtime": "PYTHON_VERSION",
        "s3_bucket": "annalect-annalect-zappa",
        "manage_roles": false,
        "keep_warm": true,
        "role_name": "zappa-execution-role",
        "vpc_config": {
            "SubnetIds": [
                "subnet-cd5b25e5",
                "subnet-f81b268c"
            ],
            "SecurityGroupIds": [
                "sg-c752958d"
            ]
        },
        "memory_size": 128,
        "aws_environment_variables": {
            "no_relevant_key": "novalue"
        }
    }
}
```

# Deployments

The script `zappa-deploy.sh` updates an already deployes project doing a `zappa update STAGE`

A command like `$ zappa-deploy.sh dev audience_builder devui` would deploy the latest commit of dev environmemt version of the audience_builder repo at branch devui.

Basically the script:
- Resets the git repo
- Pulls the branch
- Activates virtual environment
- If requirements.txt has changed, it recreates the virtual environment
- Copies files from S3
- Decrypts the serveroverride file
- Does `zappa update`
- Deletes serveroverride
- Deactivates virtualenvironment


# Commands of Zappa

## zappa deploy

In the project's path, after activating the virtual environment, the command `$ zappa deploy <stage>`:

Creates:
- CloudFormation Stack
- S3 bucket
- Api Gateway endpoint
- Lambda function


## zappa undeploy

The command
```
$ zappa undeploy <stage>
```

Deletes all resources created by the deploy. It doesn´t remove:
- S3 bucket


## zappa update

The command
```
$ zappa update <stage>
```

1. Updates the lambda function with the new code present in the directory were the command is executed.


# Deployment policy, execution role and execution role trus relationship

To review the configuration of the IAM roles and policies, please refer to the files:
- zappa-conf/zappa-deployments-policy.json
- zappa-conf/zappa-execution-role-trust-relationship.json
- zappa-conf/zappa-execution-policy.json