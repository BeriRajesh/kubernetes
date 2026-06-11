## Access AWS Management Console via OMC Central (Okta):
1. Sign-in to [OMC Central](https://omnicomgroup.okta.com). ([help?](https://s3-eu-west-1.amazonaws.com/static.annalect.com/howto/SignInOmcCentralOktaDashboard.pdf))
2. Select an AWS chicklet **OMG-Annalect-AWS** from the dashboard.
3. Choose the role from the presented list. Users holding multiple-roles will see the list of roles to choose from. 
4. Be sure that you select the correct region.

## Access AWS Management Console via CLI (Okta):

Package to ease configuration of Okta CLI for Omnicom users on Windows, Mac and Linux users.

### Prerequisites:

* python3
* pip3
* git
* MFA is enforced here, you need to set up multifactor authentication at [omc central](https://omnicomgroup.okta.com/signin/enroll)

### Installation

* Install/Upgrade the python package from BitBucket:
  
```
pip3 install git+ssh://git@bitbucket.org/annalect/anlct_okta@release --upgrade --user
```
OR

```

pip3 install git+https://<user_name>@bitbucket.org/annalect/anlct_okta.git@release --upgrade --user

```

### Configuration
​
Run the command:

```
anlct_okta_setup
```

## Usage

* Get your Okta credentials by running command:

```
anlct_okta
```

* See your available roles by running:

```
anlct_okta --action-list-roles
```

* Use one of your roles with the AWS CLI as, e.g.:

```
aws --profile My-Role-Name s3 ls s3://mybucket/folder/
```

* Command to check keys are expired or not:

```
aws --profile <role-name> sts get-caller-identity

```
* Temporary AWS access,secret key and token, these will be written to **~/.aws/credentials**.

**Note** : Key is valid for 12hours,once expired repeat same command ( anlct_okta ) to get new keys.

[Reference](https://bitbucket.org/annalect/anlct_okta/src/21a5bc50295e/?at=release) 

Please contact [DevOps](mailto:devops@annalect.com?subject=Trouble accessing AWS Okata CLI), in case of any issues.