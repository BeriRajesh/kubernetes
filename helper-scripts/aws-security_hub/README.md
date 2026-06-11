# Helper Scripts - AWS- Security Hub
This folder has been set up to programmatically fetch all security hub findings in an account. Following the instructions below will ensure that you can run the python script (security_hub.py) in this folder.

## 1. Install requirements
To run the python script, you need to install the requirements contained herein by running:

```bash
$ pip3 install -r requirements.txt
```

## 2. Configure your AWS profile
This is a 2-step procedure.

### a. Ensure you have run your MFA refresh or pokta
To ensure that we can communicate with the account for which you want to fetch findings from, you need to either run the refresh MFA or run pokta. See this article for how to refresh MFA: [Refresh MFA](https://annalect.atlassian.net/wiki/spaces/AIO/pages/20282736701/How+to+Refresh+MFA?search_id=938368cd-0f73-4c88-a495-2502ab481e22)

### b. Include the profile you're using in settings.yaml
On line 3 of the **settings.yaml**, indicate the AWS profile you want to use.

## 3. Run!
Run the security_hub script by inputting this command:
```bash
python3 security_hub.py
```

Running this command will automatically generate a CSV file in your current working directory, and in this file you can see all the findings returned

*Enjoy!*
