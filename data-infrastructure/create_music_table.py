"""
create_music_table.py
=====================
COSC2626/2640 Cloud Computing — Assignment 2
Person 1: Data & Infrastructure Lead

Creates the 'music' DynamoDB table with a carefully designed key schema,
one Local Secondary Index (LSI), and one Global Secondary Index (GSI).

Schema rationale:
    The dataset contains 137 songs across 71 artists. Analysis of the raw
    JSON revealed that 'title' alone is not a unique identifier (6 titles
    appear under multiple artists), and critically, 'title + artist' is also
    not always unique — 4 songs share the same title and artist but appear
    on different albums/years (e.g. 'Delicate' by Taylor Swift in 2017 and 2018).

    The combination of title + artist + year is always unique across the dataset.
    Since DynamoDB supports only a two-part primary key (partition + sort), the
    sort key stores a compound value '{artist}#{year}' to guarantee uniqueness
    while keeping 'artist' and 'year' as separate queryable attributes.

Run this script once before loading song data.
Requires AWS credentials configured in ~/.aws/credentials (AWS Academy default).
"""

import boto3
from botocore.exceptions import ClientError

# ── Configuration ──────────────────────────────────────────────────────────────
REGION     = 'us-east-1'
TABLE_NAME = 'music'

# ── Boto3 resource ─────────────────────────────────────────────────────────────
dynamodb = boto3.resource('dynamodb', region_name=REGION)


def create_music_table():
    """
    Create the music table in DynamoDB.

    Primary Key:
        Partition key : title (String)
            — The song title. Chosen as PK because the most common entry point
              for a query is searching by or displaying a song title.

        Sort key      : artist (String) — stored as '{artist_name}#{year}'
            — A compound value that guarantees uniqueness across all 137 songs.
              Raw artist name alone is insufficient because 4 (title, artist)
              pairs are duplicated across different albums and years.
              Storing '{artist}#{year}' as the sort key resolves all collisions
              while keeping the key semantically meaningful.

    Local Secondary Index (LSI) — 'title-year-index':
        PK  : title (same as base table — required for all LSIs)
        SK  : year (String)
        Use : Efficiently retrieve all versions of a given song title filtered
              or sorted by release year. LSI shares the base table's throughput
              and must be defined at table creation time.

    Global Secondary Index (GSI) — 'artist-year-index':
        PK  : artist_name (String)
        SK  : year (String)
        Use : Efficiently query all songs by a specific artist, optionally
              filtered by year. This directly supports the demo query patterns:
              'Find all songs by Taylor Swift in Fearless' and
              'Find all songs by Jimmy Buffett in 1974'.
              Without this GSI, artist queries would require a full table Scan.

    Note: 'artist_name' is stored as a separate plain-text attribute alongside
    the compound sort key so that the GSI can index on the pure artist name.
    """
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'title',  'KeyType': 'HASH'},   # partition key
                {'AttributeName': 'artist', 'KeyType': 'RANGE'},  # sort key (compound)
            ],
            AttributeDefinitions=[
                {'AttributeName': 'title',       'AttributeType': 'S'},
                {'AttributeName': 'artist',      'AttributeType': 'S'},
                {'AttributeName': 'year',        'AttributeType': 'S'},
                {'AttributeName': 'artist_name', 'AttributeType': 'S'},
            ],
            LocalSecondaryIndexes=[
                {
                    'IndexName': 'title-year-index',
                    'KeySchema': [
                        {'AttributeName': 'title', 'KeyType': 'HASH'},  # same as base
                        {'AttributeName': 'year',  'KeyType': 'RANGE'},
                    ],
                    # ALL projection — include every attribute in query results
                    # so the backend never needs a separate GetItem call
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'artist-year-index',
                    'KeySchema': [
                        {'AttributeName': 'artist_name', 'KeyType': 'HASH'},
                        {'AttributeName': 'year',        'KeyType': 'RANGE'},
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        print(f"[INFO] Creating table '{TABLE_NAME}'...")
        table.wait_until_exists()
        print(f"[INFO] Table '{TABLE_NAME}' is now ACTIVE.")
        return table

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceInUseException':
            print(f"[INFO] Table '{TABLE_NAME}' already exists. Using existing table.")
            return dynamodb.Table(TABLE_NAME)
        raise


def main():
    create_music_table()
    print("\n[DONE] Music table initialisation complete.")
    print("       Run load_songs.py next to populate the table.")


if __name__ == '__main__':
    main()