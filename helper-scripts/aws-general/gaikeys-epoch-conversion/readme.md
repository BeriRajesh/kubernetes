# DynamoDB Expiration Data Fetcher

This Python script retrieves data from the `gaiconversation` DynamoDB table across multiple AWS accounts, checks for expiration dates (within 2 weeks and already expired), and exports the results into an Excel file. Each AWS account has its own separate sheet in the output file.

## Features

- Fetches data from the `gaiconversation` DynamoDB table in multiple AWS accounts.
- Checks for items expiring within 2 weeks and already expired.
- Converts epoch time to human-readable date.
- Outputs results to an Excel file with separate sheets for each account.

## Requirements

- **Python 3.6+**
- **AWS CLI** installed and configured with multiple profiles in `~/.aws/credentials`.

### Python Libraries

You need to install the following Python libraries:

```bash
pip install boto3 pandas openpyxl

#### IMP Note ###
~/.aws/credential file should contain following profiles

[ann08]
role_arn = arn:aws:iam::408764662748:role/admin/ann08-dev-devops
source_profile = default
region = us-east-1

[ann29]
role_arn = arn:aws:iam::735627737612:role/admin/ann29-qa-shared-devops
source_profile = default
region = us-east-1

[ann30]
role_arn = arn:aws:iam::650804731315:role/admin/ann30-stg-shared-devops
source_profile = default
region = us-east-1

[ann31]
role_arn = arn:aws:iam::405264803242:role/admin/ann31-prod-shared-devops
source_profile = default
region = us-east-1