import boto3
import pandas as pd
from datetime import datetime, timedelta
from botocore.exceptions import ProfileNotFound
import os

# Function to list available AWS profiles
def list_profiles():
    try:
        session = boto3.Session()
        profiles = session.available_profiles
        return profiles
    except ProfileNotFound:
        print("No AWS profiles found.")
        return []

# Function to fetch data from DynamoDB
def fetch_dynamodb_data(profile, table_name):
    session = boto3.Session(profile_name=profile)
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    response = table.scan()
    items = response.get('Items', [])
    return items

# Function to convert epoch to human-readable date
def convert_epoch(epoch_time):
    if pd.notnull(epoch_time):
        return datetime.utcfromtimestamp(float(epoch_time)).strftime('%Y-%m-%d %H:%M:%S')
    return ''

# Main function
def main():
    table_name = 'gaiconversation'
    output_file = 'output_file.xlsx'
    
    # Get available AWS profiles
    profiles = list_profiles()
    if not profiles:
        print("No AWS profiles available.")
        return
    
    print("Available AWS Profiles:")
    for i, profile in enumerate(profiles):
        print(f"{i + 1}. {profile}")
    
    selected_profiles = input("Enter the numbers of the profiles you want to use (comma-separated): ")
    selected_profiles = [profiles[int(i) - 1] for i in selected_profiles.split(',')]

    # Create a Pandas Excel writer object to save multiple sheets
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        
        # Fetch data from DynamoDB for each selected profile and create separate sheets
        for profile in selected_profiles:
            print(f"Fetching data from profile: {profile}")
            data = fetch_dynamodb_data(profile, table_name)
            
            if not data:
                print(f"No data found for profile: {profile}")
                continue
            
            # Convert data to a Pandas DataFrame
            df = pd.DataFrame(data)
            
            if 'expiration_datetime' in df.columns:
                # Convert epoch to human-readable date
                df['expiration_datetime_human'] = df['expiration_datetime'].apply(convert_epoch)
                
                # Get the current time and calculate the expiration threshold (2 weeks from today)
                current_time = datetime.utcnow()
                two_weeks_from_now = current_time + timedelta(weeks=2)

                # Create DataFrames for rows expiring within 2 weeks and already expired
                expiring_soon_df = df[df['expiration_datetime'].apply(
                    lambda x: current_time <= datetime.utcfromtimestamp(float(x)) <= two_weeks_from_now
                )]
                
                expired_df = df[df['expiration_datetime'].apply(
                    lambda x: datetime.utcfromtimestamp(float(x)) < current_time
                )]
                
                # Save data in separate sheets for each profile
                df.to_excel(writer, index=False, sheet_name=f'{profile}_All Data')
                expiring_soon_df.to_excel(writer, index=False, sheet_name=f'{profile}_Expiring in 2 Weeks')
                expired_df.to_excel(writer, index=False, sheet_name=f'{profile}_Already Expired')

            else:
                print(f"'expiration_datetime' column not found in profile: {profile}")

    print(f"Data fetched and saved to {output_file} with separate sheets for each account.")

if __name__ == "__main__":
    main()
