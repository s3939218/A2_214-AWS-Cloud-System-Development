"""
Creates the 'music' DynamoDB table with GSI and LSI.
Run once before loading song data.
"""

import boto3

# same setup as lab - boto3 resource for DynamoDB
REGION     = 'us-east-1'
TABLE_NAME = 'music'

dynamodb = boto3.resource('dynamodb', region_name=REGION)


def create_music_table():
    # title as partition key, artist (compound artist#year) as sort key
    # compound sort key needed because title+artist alone is not always unique
    # e.g. 'Delicate' by Taylor Swift exists in 2017 and 2018
    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {'AttributeName': 'title',  'KeyType': 'HASH'},
            {'AttributeName': 'artist', 'KeyType': 'RANGE'},
        ],
        AttributeDefinitions=[
            {'AttributeName': 'title',       'AttributeType': 'S'},
            {'AttributeName': 'artist',      'AttributeType': 'S'},
            {'AttributeName': 'year',        'AttributeType': 'S'},
            {'AttributeName': 'artist_name', 'AttributeType': 'S'},
        ],
        LocalSecondaryIndexes=[
            {
                # LSI - same partition key (title), sort by year
                # LSI concept covered in Week 6
                'IndexName': 'title-year-index',
                'KeySchema': [
                    {'AttributeName': 'title', 'KeyType': 'HASH'},
                    {'AttributeName': 'year',  'KeyType': 'RANGE'},
                ],
                # ALL projection so queries return full items without extra lookups
                # ref: boto3 docs - ProjectionType options: ALL, KEYS_ONLY, INCLUDE
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        GlobalSecondaryIndexes=[
            {
                # GSI - query by artist_name and year
                # GSI concept covered in Week 6 lectorial - own partition key, own throughput
                # supports queries like 'all songs by Taylor Swift' or 'Jimmy Buffett in 1974'
                # without this, artist queries would need a full table scan
                'IndexName': 'artist-year-index',
                'KeySchema': [
                    {'AttributeName': 'artist_name', 'KeyType': 'HASH'},
                    {'AttributeName': 'year',        'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
                # GSI needs its own throughput, separate from the base table
                # ref: boto3 docs - GSIs require ProvisionedThroughput when base table uses provisioned mode
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            }
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
    create_music_table()
    print("Done. Run load_songs.py next.")