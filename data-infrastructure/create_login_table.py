"""
Creates the 'login' DynamoDB table and loads 10 user records.
Run once before starting the app.
"""

import boto3

# same setup as lab - boto3 resource for DynamoDB
REGION       = 'us-east-1'
TABLE_NAME   = 'login'
STUDENT_ID   = 's3874656'
STUDENT_NAME = 'GaziMohaimenulHoque'

dynamodb = boto3.resource('dynamodb', region_name=REGION)


def create_login_table():
    # create table with email as partition key, no sort key needed
    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {'AttributeName': 'email', 'KeyType': 'HASH'},
        ],
        AttributeDefinitions=[
            {'AttributeName': 'email', 'AttributeType': 'S'},
        ],
        # using provisioned throughput as shown in lab
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    print(f"Creating table '{TABLE_NAME}'...")
    table.wait_until_exists()
    print(f"Table '{TABLE_NAME}' is active.")
    return table


def load_users(table):
    # plain text passwords permitted for this assignment only
    # in production, passwords must be salted and hashed
    users = []
    for i in range(10):
        # rolling 6-digit password e.g. i=0 → '012345', i=9 → '901234'
        password = ''.join(str((i + offset) % 10) for offset in range(6))
        users.append({
            'email':     f'{STUDENT_ID}{i}@student.rmit.edu.au',
            'user_name': f'{STUDENT_NAME}{i}',
            'password':  password
        })

    # put_item for each user, same pattern used in lab
    for user in users:
        table.put_item(Item=user)
        print(f"Inserted: {user['email']}")

    print(f"\nLoaded {len(users)} users into '{TABLE_NAME}'.")


if __name__ == '__main__':
    table = create_login_table()
    load_users(table)
    print("Done.")