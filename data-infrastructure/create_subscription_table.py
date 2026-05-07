"""
Creates the 'subscription' DynamoDB table.
Run once before starting the app.
"""

import boto3

# same setup as lab - boto3 resource for DynamoDB
REGION     = 'us-east-1'
TABLE_NAME = 'subscription'

dynamodb = boto3.resource('dynamodb', region_name=REGION)


def create_subscription_table():
    # email as partition key - one partition per user, matches login table
    # sort key is title#artist (compound) - uniquely identifies a subscribed song
    # e.g. 'Delicate#Taylor Swift#2017' prevents duplicate subscriptions
    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {'AttributeName': 'email',        'KeyType': 'HASH'},
            {'AttributeName': 'title_artist',  'KeyType': 'RANGE'},
        ],
        AttributeDefinitions=[
            {'AttributeName': 'email',        'AttributeType': 'S'},
            {'AttributeName': 'title_artist',  'AttributeType': 'S'},
        ],
        # provisioned throughput as used in Week 6 lab (10 read, 10 write)
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )

    print(f"Creating table '{TABLE_NAME}'...")
    table.wait_until_exists()
    print(f"Table '{TABLE_NAME}' is active.")
    return table


if __name__ == '__main__':
    create_subscription_table()
    print("Done.")