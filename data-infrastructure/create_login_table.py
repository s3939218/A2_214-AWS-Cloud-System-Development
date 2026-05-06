"""
create_login_table.py
=====================
COSC2626/2640 Cloud Computing — Assignment 2
Person 1: Data & Infrastructure Lead

Creates the 'login' DynamoDB table and populates it with 10 user records
following the assignment spec format.

Run this script once to initialise the login table before starting the app.
Requires AWS credentials configured in ~/.aws/credentials (AWS Academy default).
"""

import boto3
from botocore.exceptions import ClientError

# ── Configuration ──────────────────────────────────────────────────────────────
REGION       = 'us-east-1'
TABLE_NAME   = 'login'
STUDENT_ID   = 's3874656'          # RMIT student ID (without the trailing digit)
STUDENT_NAME = 'GaziMohaimenulHoque'  # FirstnameLastname — no spaces, per spec


# ── Boto3 resource (uses credentials from ~/.aws/credentials automatically) ───
dynamodb = boto3.resource('dynamodb', region_name=REGION)


def create_login_table():
    """
    Create the login table in DynamoDB.

    Schema:
        Partition key: email (String)  — globally unique per user, natural lookup key
        No sort key needed             — each user has exactly one email

    If the table already exists (e.g. running the script a second time),
    we skip creation and return a reference to the existing table.
    """
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'email', 'KeyType': 'HASH'},  # partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'email', 'AttributeType': 'S'},
            ],
            BillingMode='PAY_PER_REQUEST'  # on-demand — no capacity planning needed
        )

        print(f"[INFO] Creating table '{TABLE_NAME}'...")
        # Block until DynamoDB reports the table as ACTIVE
        table.wait_until_exists()
        print(f"[INFO] Table '{TABLE_NAME}' is now ACTIVE.")
        return table

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceInUseException':
            # Table already exists — safe to continue
            print(f"[INFO] Table '{TABLE_NAME}' already exists. Using existing table.")
            return dynamodb.Table(TABLE_NAME)
        # Any other error is unexpected — re-raise
        raise


def generate_users():
    """
    Generate the 10 login records following the assignment spec:

        email     : s3874656{i}@student.rmit.edu.au
        user_name : GaziMohaimenulHoque{i}
        password  : 6 consecutive digits starting at i, wrapping mod 10

    Password examples:
        i=0 → '012345'
        i=1 → '123456'
        i=9 → '901234'

    NOTE: Storing passwords in plain text is permitted for this assignment only.
    In any real production system, passwords must be salted and hashed (e.g. bcrypt).
    """
    users = []
    for i in range(10):
        # Build password: 6 consecutive digits starting at i, each wrapping mod 10
        password = ''.join(str((i + offset) % 10) for offset in range(6))

        users.append({
            'email':     f'{STUDENT_ID}{i}@student.rmit.edu.au',
            'user_name': f'{STUDENT_NAME}{i}',
            'password':  password
        })
    return users


def load_users(table):
    """
    Insert all 10 generated users into the login table.
    Uses batch_writer for efficiency (fewer API round-trips).
    """
    users = generate_users()

    print(f"\n[INFO] Loading {len(users)} users into '{TABLE_NAME}'...")

    with table.batch_writer() as batch:
        for user in users:
            batch.put_item(Item=user)

    # Print a confirmation table
    print(f"\n{'Email':<45} {'Username':<25} {'Password'}")
    print('-' * 80)
    for u in users:
        print(f"{u['email']:<45} {u['user_name']:<25} {u['password']}")

    print(f"\n[INFO] Successfully loaded {len(users)} users.")


def main():
    table = create_login_table()
    load_users(table)
    print("\n[DONE] Login table initialisation complete.")


if __name__ == '__main__':
    main()