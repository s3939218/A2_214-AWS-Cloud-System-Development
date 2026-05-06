"""
load_songs.py
=============
COSC2626/2640 Cloud Computing — Assignment 2
Person 1: Data & Infrastructure Lead

Reads all songs from 2026a2_songs.json and loads them into the 'music'
DynamoDB table. Handles all duplicate (title, artist) pairs correctly
using a compound sort key to ensure a lossless, zero-overwrite import.

Key decisions:
    - Sort key 'artist' stores '{artist_name}#{year}' to differentiate
      songs with identical title and artist but different albums/years.
      (e.g. 'Delicate' by Taylor Swift appears in 2017 and 2018)
    - 'artist_name' is stored as a plain separate attribute for GSI queries.
    - JSON field 'img_url' is normalised to 'image_url' per assignment spec.

Run this script after create_music_table.py.
Requires AWS credentials configured in ~/.aws/credentials (AWS Academy default).
"""

import json
import boto3
from botocore.exceptions import ClientError

# ── Configuration ──────────────────────────────────────────────────────────────
REGION     = 'us-east-1'
TABLE_NAME = 'music'
JSON_FILE  = '2026a2_songs.json'   # must be in the same directory as this script

# ── Boto3 resource ─────────────────────────────────────────────────────────────
dynamodb = boto3.resource('dynamodb', region_name=REGION)


def load_songs():
    """
    Read songs from the JSON file and insert them all into the music table.

    For each song:
        title       → partition key (stored as-is)
        artist      → sort key, stored as '{artist_name}#{year}' compound
        artist_name → plain artist name, stored as a separate attribute for GSI
        year        → release year
        album       → album name
        image_url   → S3 key or URL (normalised from 'img_url' in the JSON)

    Uses batch_writer() for efficiency — Boto3 automatically batches writes
    in groups of 25 (the DynamoDB maximum per batch) and handles retries.
    """
    # Load JSON data
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    songs = data['songs']
    print(f"[INFO] Loaded {len(songs)} songs from '{JSON_FILE}'.")

    table = dynamodb.Table(TABLE_NAME)

    # Track duplicates for verification
    seen_keys = {}
    duplicate_count = 0

    print(f"[INFO] Writing songs to '{TABLE_NAME}'...")

    with table.batch_writer() as batch:
        for song in songs:
            artist_name = song['artist']
            year        = song['year']

            # Compound sort key: guarantees uniqueness for all 137 songs
            # even where (title, artist) alone would collide
            compound_artist = f"{artist_name}#{year}"

            # Check for any remaining collisions (safety net)
            key = (song['title'], compound_artist)
            if key in seen_keys:
                duplicate_count += 1
                print(f"[WARN] Duplicate key detected: title='{song['title']}' "
                      f"artist='{compound_artist}' — will overwrite previous entry.")
            seen_keys[key] = True

            item = {
                'title':       song['title'],        # partition key
                'artist':      compound_artist,       # sort key (compound)
                'artist_name': artist_name,           # plain name for GSI
                'year':        year,
                'album':       song['album'],
                'image_url':   song['img_url'],       # normalised from img_url
            }

            batch.put_item(Item=item)

    print(f"[INFO] Successfully wrote {len(songs)} songs to '{TABLE_NAME}'.")

    if duplicate_count == 0:
        print("[INFO] No key collisions detected — import is lossless. ✓")
    else:
        print(f"[WARN] {duplicate_count} collision(s) detected — review compound key logic.")


def verify_load():
    """
    Quick sanity check — scan the table and count total items.
    Expected: 137
    """
    table = dynamodb.Table(TABLE_NAME)

    # Scan is appropriate here — this is a one-time verification of a small
    # dataset during initialisation, not a production query pattern
    response = table.scan(Select='COUNT')
    count = response['Count']

    # Handle pagination if needed (scan returns max 1MB per call)
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            Select='COUNT',
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        count += response['Count']

    print(f"[INFO] Verification: {count} items found in '{TABLE_NAME}'. "
          f"{'✓' if count == 137 else '✗ Expected 137 — check for issues.'}")


def main():
    load_songs()
    verify_load()
    print("\n[DONE] Song data load complete.")
    print("       Run upload_images.py next to upload artist images to S3.")


if __name__ == '__main__':
    main()