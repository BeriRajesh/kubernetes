import psycopg2
from psycopg2 import sql
import getpass
from getpass import getpass
import random
import string
import sys

#below code will create a new database, schema, readonly group, read write group and service user.

# NOTE: DB_NAME SHOULD BE ALREADY EXISTING DB
# NOTE: NEWDB_NAME SHOULD BE NEWLY CREATING DB NAME


def print_introduction():
        print("""
===============================================================================
            PostgreSQL DB Creation Script
===============================================================================

This script creates a new Database, schema, readonly group, read/write group, and service user.


You will be prompted to enter the following information:

              -Existing Database name (to connect to)
              -Existing Database Username and Password
              -Existing Database Hostname and Port
              -New Database Name

Your new database name will be used to generate your schema, group, and service user names in
the format of NEWDB_ro, NEWDB_rw, NEWDB_user.

Please be sure that your credentials have the necessary permissions to create a new database
before proceeding.

===============================================================================
              """)

def get_input(prompt: str) -> str:
    return input(prompt).strip()

def confirm_input(input_dict: dict) -> bool:
    print("\nPlease confirm your information is correct:")
    for key, value in input_dict.items():
        if key != 'DB_PASSWORD':
            print(f"{key}: {value}")

    while True:
        confirm = input("\nIs this information correct? (yes/no): ").lower()
        if confirm in ['yes', 'y']:
            return True
        elif confirm in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'.")

print_introduction()


# Enter your PostgreSQL connection details
user_input = {
        'DB_NAME': get_input("Enter existing DB name: "),
        'DB_USER': get_input("Enter existing DB Username: "),
        'DB_HOST': get_input("Enter existing DB connection address: "),  # or your host address
        'DB_PORT': get_input("Enter existing DB connection port (Default 5432): ") or "5432", # default PostgreSQL port

# New DB Name
'NEWDB_NAME': get_input("Enter NEW DB name: ")
}

# Get DB Password for existing DB
DB_PASSWORD = getpass("Enter existing DB Password: "),


if not confirm_input(user_input):
    print("Operation cancelled by user. Exiting script.")
    sys.exit()


# New DB Creation
def create_database():
    try:
        # Connect to the default database (postgres)
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )

        # Create a cursor object
        cur = conn.cursor()
        conn.autocommit = True
        # Create the database
        cur.execute(sql.SQL("CREATE DATABASE {};").format(sql.Identifier(NEWDB_NAME)))

        # Close communication with the PostgreSQL database server
        cur.close()

        # Commit the transaction
        conn.commit()
        conn.close()

        print("Database created successfully!")

    except psycopg2.Error as e:
        print("Error creating database:", e)

    finally:
        # Close the database connection
        if conn is not None:
            conn.close()


# Call the function to create the database
create_database()


def generate_custom_string():
    numbers = ''.join(random.choice(string.digits) for _ in range(8))
    small_letters = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
    capital_letters = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))

    # Combine all parts and shuffle
    combined_string = numbers + small_letters + capital_letters
    shuffled_string = ''.join(random.sample(combined_string, len(combined_string)))

    return shuffled_string


def create_schemagroups():
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname=NEWDB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )

        # Create a cursor object
        cur = conn.cursor()
        conn.autocommit = True
        PASSWORD = generate_custom_string()
        print(PASSWORD)
        # Define the schema name
        # schema_name = "your_schema_name"

        # Create the schema
        cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {};").format(sql.Identifier(SCHEMA_NAME)))
        #Create ReadOnly Group
        cur.execute(sql.SQL("CREATE ROLE {};").format(sql.Identifier(READONLY_GROUP)))
        cur.execute(sql.SQL("GRANT CONNECT ON DATABASE "+NEWDB_NAME+ " TO " +READONLY_GROUP +";"))
        cur.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {};").format(sql.Identifier(SCHEMA_NAME), sql.Identifier(READONLY_GROUP)))
        cur.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}").format(
            sql.Identifier(SCHEMA_NAME), sql.Identifier(READONLY_GROUP)))
        cur.execute(sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT SELECT ON TABLES TO {};").format(
            sql.Identifier(SCHEMA_NAME), sql.Identifier(READONLY_GROUP)))

        # Create Readwrite Group
        cur.execute(sql.SQL("CREATE ROLE {};").format(sql.Identifier(READWRITE_GROUP)))
        cur.execute(sql.SQL("GRANT CONNECT ON DATABASE "+NEWDB_NAME+" TO "+ READWRITE_GROUP+";"))
        cur.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {};").format(sql.Identifier(SCHEMA_NAME), sql.Identifier(READWRITE_GROUP)))
        # Grant SELECT privileges to the readonly group on all tables in the public schema
        cur.execute(sql.SQL("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {} TO {}").format(
            sql.Identifier(SCHEMA_NAME), sql.Identifier(READWRITE_GROUP)))
        cur.execute(sql.SQL(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {};").format(
            sql.Identifier(SCHEMA_NAME),sql.Identifier( READWRITE_GROUP)))
        # Create service user
        cur.execute(sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD '"+ PASSWORD+"';").format(sql.Identifier( SERVICE_USER)))
        cur.execute(sql.SQL("GRANT CONNECT ON DATABASE "+ NEWDB_NAME+" TO "+SERVICE_USER+";"))
        cur.execute(sql.SQL("GRANT {} TO {};").format(sql.Identifier(READWRITE_GROUP),sql.Identifier( SERVICE_USER)))
        cur.execute(sql.SQL("ALTER ROLE  {} WITH LOGIN;").format(sql.Identifier(SERVICE_USER)))
        cur.execute(sql.SQL("SET ROLE {};").format(sql.Identifier(SERVICE_USER)))
        cur.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES FOR role {} in SCHEMA {} GRANT SELECT ON tables TO GROUP {};").format(
                sql.Identifier(SERVICE_USER), sql.Identifier(SCHEMA_NAME), sql.Identifier(READONLY_GROUP)))
        cur.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES FOR role {} in SCHEMA {} GRANT ALL ON tables TO GROUP {};").format(
                sql.Identifier(SERVICE_USER), sql.Identifier(SCHEMA_NAME),sql.Identifier( READWRITE_GROUP)))

        # Commit the transaction
        conn.commit()
        if conn is not None:
            conn.close()
        print("schema,ReadOnly group, ReadWrite group and Service user created successfully!")

    except psycopg2.Error as e:
        print("Error creating the schema,ReadOnly group, ReadWrite group and Service user :", e)


# Call the function to create the schema,ReadOnly group, ReadWrite group and Service user
create_schemagroups()

