import boto3
import json
import re
import sys


def main():
    user_types = [ 'user','vendor','service' ]
    print("Welcome to new IAM Account creation process\n")
    print("\t Please Select the type of IAM Account you want to create\n")
    selection = make_choice(user_types)
    print('\nSelected IAM Account Type : ' + selection )
    confirmation=yes_or_no('Do you wish to proceed ')

    if confirmation is True:
        if selection is 'user' :
            user_name = input_email()
            user_email= user_name
        else:
            user_name = input('Enter the prefered name of IAM Account  : ')
            user_email= input_email()

        response=creating_account(selection,user_name, user_email)
        print(response)
    else:
        print('See you later .. Bye...')


def make_choice(options_array):
    try:
        options_length=len(options_array)
        for option in options_array:
            print('\t\t\t'+str(options_array.index(option)+1)+'. '+option)
    
        choice = int(input("\nPlease enter your Choice : "))
        while choice not in range(1, options_length+1): 
            choice=int(input("\nYou have not made a proper Selectionion !! - \nAllowed Choices are between 1 - " + str(options_length) + ' : '))
    except ValueError:
        print ("\nYou have not entered a Number !! - \n\tAllowed Choices are between 1 - " + str(options_length) + ' : ')
        make_choice(options_array)

    return options_array[choice-1]

def yes_or_no(question):
    reply = str(input(question+' Enter (y/n): ')).lower().strip()
    if reply == 'y':
        return True
    if reply == 'n':
        return False
    else:
        return yes_or_no("Uhhhh... please enter ")

def creating_account(user_type, user_name, user_email): 
    client = boto3.client('iam')
    response = client.create_user(
        Path='/',
        UserName=user_name,
        Tags=[
                    {
                        'Key': 'user-type',
                        'Value': user_type
                    },
                    {
                        'Key': 'contact-email',
                        'Value': user_email
                    }
                ]
            )
    
    keys = client.create_access_key(UserName=user_name)
    
    print('\nSuccessfully Created new IAM Account of user type : ' + user_type + '\n\t See below the details' + '\n\t\t\t Username :  ' + response['User']['UserName'] + '\n\t\t\t AccessKeys :  ' + keys['AccessKey']['AccessKeyId'] + '\n\t\t\t Secret Keys :  ' + keys['AccessKey']['SecretAccessKey'] )
    print ('\n Job Done Successfully ... ok  Bye ...  \n')

def input_email():
    email_regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    email = input('Enter the Email id of the User  : ')
    while email is "" or not re.search(email_regex,email):
        email = input('You have not entered a  valid Email \n\t Please enter the Email id of the User  : ')
    return email





# def common_actions():
#     print(common-actions)


if __name__ == "__main__":
    # execute only if run as a script
    main()
