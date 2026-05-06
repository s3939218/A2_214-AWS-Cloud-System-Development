"""
upload_images.py
================
COSC2626/2640 Cloud Computing — Assignment 2
Person 1: Data & Infrastructure Lead

1. Creates a private S3 bucket with all public access blocked.
2. Downloads all 71 unique artist images from the URLs in 2026a2_songs.json.
3. Uploads each image to S3 under the key 'artist-images/{filename}'.
4. Updates every DynamoDB music record so 'image_url' stores the S3 object
   key rather than the original GitHub URL.

Security design:
    The bucket is kept fully private — no public access of any kind.
    The application backend generates short-lived pre-signed URLs at request
    time to serve images securely to the frontend. This means raw S3 URLs
    are never exposed, and access is controlled entirely through IAM (LabRole).
    This follows AWS security best practice for S3 object access.

Run this script after load_songs.py.
Requires AWS credentials configured in ~/.aws/credentials (AWS Academy default).
"""

import json
import urllib.request
from urllib.parse import urlparse
import boto3
from botocore.exceptions import ClientError

# ── Configuration ──────────────────────────────────────────────────────────────
REGION      = 'us-east-1'
BUCKET_NAME = 'rmit-cc-a2-group214-music'
TABLE_NAME  = 'music'
JSON_FILE   = '2026a2_songs.json'
S3_PREFIX   = 'artist-images/'    # logical folder inside the bucket

# ── Boto3 clients ──────────────────────────────────────────────────────────────
s3_client = boto3.client('s3', region_name=REGION)
dynamodb  = boto3.resource('dynamodb', region_name=REGION)


# ── Step 1: Create S3 bucket ───────────────────────────────────────────────────

def create_bucket():
    """
    Create the S3 bucket and block all public access.

    Note: us-east-1 is the default AWS region — creating a bucket here does
    NOT require a LocationConstraint in the request. Any other region would.

    Public access is fully blocked so images are never directly accessible
    via URL. The backend uses pre-signed URLs to serve images securely.
    """
    try:
        # us-east-1: no CreateBucketConfiguration needed
        s3_client.create_bucket(Bucket=BUCKET_NAME)
        print(f"[INFO] Bucket '{BUCKET_NAME}' created.")

    except ClientError as e:
        code = e.response['Error']['Code']
        if code in ('BucketAlreadyOwnedByYou', 'BucketAlreadyExists'):
            print(f"[INFO] Bucket '{BUCKET_NAME}' already exists. Continuing.")
        else:
            raise

    # Block all public access — security best practice
    s3_client.put_public_access_block(
        Bucket=BUCKET_NAME,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls':       True,
            'IgnorePublicAcls':      True,
            'BlockPublicPolicy':     True,
            'RestrictPublicBuckets': True
        }
    )
    print(f"[INFO] Public access fully blocked on '{BUCKET_NAME}'.")


# ── Step 2: Download and upload images ────────────────────────────────────────

def get_unique_images(songs):
    """
    Extract all unique image URLs from the songs list.
    71 unique artists = 71 unique images.
    Returns a dict mapping: original_url → s3_object_key
    """
    url_to_key = {}
    for song in songs:
        url = song['img_url']
        if url not in url_to_key:
            # Extract filename from URL (e.g. 'TaylorSwift.jpg')
            filename = urlparse(url).path.split('/')[-1]
            s3_key   = f"{S3_PREFIX}{filename}"
            url_to_key[url] = s3_key
    return url_to_key


def download_and_upload(url_to_key):
    """
    For each unique image URL, download the image and upload it to S3.
    Uses urllib (built-in) — no extra dependencies needed.
    """
    total   = len(url_to_key)
    success = 0

    for i, (url, s3_key) in enumerate(url_to_key.items(), 1):
        filename = s3_key.split('/')[-1]
        try:
            print(f"[{i}/{total}] Downloading {filename}...")

            # Download image bytes from GitHub
            with urllib.request.urlopen(url) as response:
                image_data = response.read()

            # Upload directly to S3 from memory — no temp file needed
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=image_data,
                ContentType='image/jpeg'
            )
            success += 1

        except Exception as e:
            print(f"[ERROR] Failed to process {filename}: {e}")

    print(f"\n[INFO] Uploaded {success}/{total} images to S3.")
    return success


# ── Step 3: Update DynamoDB with S3 keys ─────────────────────────────────────

def update_dynamodb(url_to_key):
    """
    Update all 137 DynamoDB music records so that 'image_url' stores the
    S3 object key instead of the original GitHub URL.

    The backend will use these keys to generate pre-signed URLs at request time.

    Scan is used here because we need to update every item in the table —
    there is no key-based way to target all items at once.
    """
    table = dynamodb.Table(TABLE_NAME)

    # Scan all items to retrieve their primary keys
    response = table.scan()
    items    = response['Items']

    # Handle pagination — scan returns max 1MB per call
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])

    print(f"[INFO] Updating {len(items)} DynamoDB records with S3 keys...")

    updated = 0
    for item in items:
        old_url = item.get('image_url', '')
        new_key = url_to_key.get(old_url)

        if new_key:
            table.update_item(
                Key={
                    'title':  item['title'],   # partition key
                    'artist': item['artist']   # sort key (compound)
                },
                UpdateExpression='SET image_url = :new_val',
                ExpressionAttributeValues={':new_val': new_key}
            )
            updated += 1

    print(f"[INFO] Updated {updated}/{len(items)} records successfully.")


# ── Step 4: Verify ────────────────────────────────────────────────────────────

def verify_upload(url_to_key):
    """
    List objects in the S3 bucket and confirm all 71 images are present.
    """
    response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=S3_PREFIX)
    uploaded = response.get('Contents', [])
    count    = len(uploaded)

    expected = len(url_to_key)
    status   = '✓' if count == expected else f'✗ Expected {expected}'
    print(f"[INFO] Verification: {count} images found in S3. {status}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Load JSON
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    songs = data['songs']

    # Build URL → S3 key mapping
    url_to_key = get_unique_images(songs)
    print(f"[INFO] Found {len(url_to_key)} unique artist images to upload.")

    # Step 1 — create bucket
    create_bucket()

    # Step 2 — download and upload images
    download_and_upload(url_to_key)

    # Step 3 — update DynamoDB records with S3 keys
    update_dynamodb(url_to_key)

    # Step 4 — verify
    verify_upload(url_to_key)

    print("\n[DONE] Image upload complete.")
    print(f"       Images stored at s3://{BUCKET_NAME}/{S3_PREFIX}")
    print("       The backend should generate pre-signed URLs to serve these securely.")


if __name__ == '__main__':
    main()