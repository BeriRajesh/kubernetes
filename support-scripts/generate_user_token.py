#!/usr/bin/env python3
import re
import requests


def get_valid_input(prompt, choices=None, validator=None, lowercase=False):
    while True:
        user_input = input(prompt)
        if lowercase:
            user_input = user_input.lower()
        if choices and user_input in choices:
            return user_input
        elif validator and validator(user_input):
            return user_input
        else:
            print("Invalid input, please try again.")


def validate_application_name(name):
    return len(name) < 64 and bool(re.match(r'^[a-zA-Z0-9\-_\.\@]+$', name))


def validate_email(email):
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))


def validate_password(password):
    val = True
    symbols = '!@#$%^&*()-_[]'
    if not len(password) >= 16 and len(password) <= 64:
        print("Password must be between 16 and 64 characters")
        val = False
    if not any(char.isdigit() for char in password):
        print ("Password must contain at least one number")
        val = False
    if not any(char.islower() for char in password):
        print ("Password must contain at least one lowercase character")
        val = False
    if not any(char.isupper() for char in password):
        print ("Password must contain at least one uppercase character")
        val = False
    if not any(char in list(symbols) for char in password):
        print(f'Password should have at least one of the following symbols: {symbols}')
        val = False
    return val


def confirm_inputs(endpoint, user_type, payload):
    obscured_password = '*' * len(payload['password'])
    if user_type == 'standard':
        object = 'user'
    else:
        object = 'token'
    print(f"\nYou are about to create a {object} with the following inputs:")
    print(f"API Endpoint: {endpoint}")
    print(f"User Type: {user_type}")
    if user_type == 'admin':
        print(f"Username: {payload['username']}")
    else:  # standard user
        print(f"Application Name: {payload['username']}")
        print(f"Email: {payload['email']}")
        print(f"Write Access (super user): {payload['is_superuser']}")
    print(f"Password: {obscured_password}")

    confirmation = input("Do you want to continue? [Y/n] ").strip().lower()
    return confirmation in ['y', 'yes']


environment = get_valid_input("Please enter the environment in which to create the user. Valid choices are:\ndev\nqa\nstg\nprod\n", choices=['dev', 'qa', 'stg', 'prod'])
service = get_valid_input("Please enter the name of the service. Valid choices are:\nconversation\ndictionary\norchestration\n", choices=['conversation', 'dictionary', 'orchestration'])
api_key = input(f"Please enter API key for {service} service:\n")
user_type = get_valid_input("Please enter the type of user to create. Valid choices are\nadmin\nstandard\n", choices=['admin', 'standard'])

if user_type == 'standard':
    route = 'create-user'
    username = get_valid_input("Please enter the name of the application, e.g. `campaign`:\n", validator=validate_application_name)
    password = get_valid_input("Please enter a password for the new user. Password requirements:\n- Between 16 and 64 characters\n- At least one uppercase char\n- At least one lowercase char\n- At least one number\n- At least one of the following symbols: !@#$%^&*()-_[]\n", validator=validate_password)    
    email = get_valid_input("Please enter email address for token owner:\n", validator=validate_email)
    is_superuser_input = get_valid_input("Enable write access (a.k.a. superuser)? (Y/N)\n", choices=['y', 'n', 'yes', 'no'], lowercase=True)
    is_superuser = is_superuser_input.lower() in ['y', 'yes']
else:
    route = 'create-token'
    username = input("Enter username for existing user:\n")
    password = input("Enter password:\n")

if environment == 'prod':
    env = ''
else:
    env = environment
endpoint = f"https://{env}{service}-api.annalect.com/api/v1/omni-admin/{route}/"
headers = { 'x-api-key': api_key }
payload = {
    "username": username,
    "password": password,
}
if user_type == 'standard':
    payload.update({
        "email": email,
        "is_superuser": is_superuser
    })


if confirm_inputs(endpoint, user_type, payload):
    api_response = requests.post(
        url=endpoint,
        data=payload,
        headers=headers)
    print("API response:")
    print(api_response.json())
else:
    print("Exiting without making API request.")
