"""
Reads all songs from 2026a2_songs.json and loads them into the music table.
Run after create_music_table.py.
"""

import json
import boto3

# same setup as lab - boto3 resource for DynamoDB
REGION     = 'us-east-1'
TABLE_NAME = 'music'
JSON_FILE  = '2026a2_songs.json'

dynamodb = boto3.resource('dynamodb', region_name=REGION)


def load_songs():
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    songs = data['songs']
    table = dynamodb.Table(TABLE_NAME)

    # track seen keys to catch any collisions before they silently overwrite
    seen_keys = {}

    for song in songs:
        artist_name = song['artist']
        year        = song['year']

        # compound sort key - artist#year ensures uniqueness across all 137 songs
        # needed because title+artist alone has 4 duplicate pairs in the dataset
        compound_artist = f"{artist_name}#{year}"

        key = (song['title'], compound_artist)
        if key in seen_keys:
            print(f"Warning: duplicate key found for '{song['title']}' by '{artist_name}'")
        seen_keys[key] = True

        # img_url in JSON normalised to image_url per assignment spec
        item = {
            'title':       song['title'],
            'artist':      compound_artist,   # sort key (compound)
            'artist_name': artist_name,        # plain name stored separately for GSI
            'year':        year,
            'album':       song['album'],
            'image_url':   song['img_url'],
        }

        # put_item for each song, same pattern used in lab
        table.put_item(Item=item)

    print(f"Loaded {len(songs)} songs into '{TABLE_NAME}'.")


def verify_load():
    table = dynamodb.Table(TABLE_NAME)

    # scan to count all items - covered in Week 6 lectorial
    # appropriate here since we need a full count across all partitions
    response = table.scan(Select='COUNT')
    count = response['Count']

    # handle pagination - scan returns max 1MB per call
    # ref: boto3 docs - use LastEvaluatedKey to continue scanning
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            Select='COUNT',
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        count += response['Count']

    expected = 137
    status = 'OK' if count == expected else f'ERROR - expected {expected}'
    print(f"Verification: {count} items in '{TABLE_NAME}' - {status}")


if __name__ == '__main__':
    load_songs()
    verify_load()
    print("Done. Run upload_images.py next.")