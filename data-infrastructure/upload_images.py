"""
Downloads artist images from URLs in 2026a2_songs.json,
uploads them to S3, and updates DynamoDB image_url with S3 keys.
Run after load_songs.py.
"""

import json
import urllib.request
from urllib.parse import urlparse
import boto3
from botocore.exceptions import ClientError

# same setup as lab - boto3 client for S3, resource for DynamoDB
REGION      = 'us-east-1'
BUCKET_NAME = 'rmit-cc-a2-group214-music'
TABLE_NAME  = 'music'
JSON_FILE   = '2026a2_songs.json'
S3_PREFIX   = 'artist-images/'

s3_client = boto3.client('s3', region_name=REGION)
dynamodb  = boto3.resource('dynamodb', region_name=REGION)


def create_bucket():
    # us-east-1 does not need CreateBucketConfiguration - other regions do
    # ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/create_bucket.html
    try:
        s3_client.create_bucket(Bucket=BUCKET_NAME)
        print(f"Bucket '{BUCKET_NAME}' created.")
    except ClientError as e:
        # ClientError is Python equivalent of AmazonServiceException from Week 5 Java lab
        # ref: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/error-handling.html
        code = e.response['Error']['Code']
        if code in ('BucketAlreadyOwnedByYou', 'BucketAlreadyExists'):
            print(f"Bucket '{BUCKET_NAME}' already exists, continuing.")
        else:
            raise

    # block all public access - S3 security best practice covered in Week 5
    # images are served via pre-signed URLs from the backend instead
    # ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_public_access_block.html
    s3_client.put_public_access_block(
        Bucket=BUCKET_NAME,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls':       True,
            'IgnorePublicAcls':      True,
            'BlockPublicPolicy':     True,
            'RestrictPublicBuckets': True
        }
    )
    print(f"Public access blocked on '{BUCKET_NAME}'.")


def get_unique_images(songs):
    # build a mapping of original URL to S3 key - 71 unique artists = 71 images
    # ref: https://docs.python.org/3/library/urllib.parse.html
    url_to_key = {}
    for song in songs:
        url = song['img_url']
        if url not in url_to_key:
            filename = urlparse(url).path.split('/')[-1]
            url_to_key[url] = f"{S3_PREFIX}{filename}"
    return url_to_key


def download_and_upload(url_to_key):
    total   = len(url_to_key)
    success = 0

    for i, (url, s3_key) in enumerate(url_to_key.items(), 1):
        filename = s3_key.split('/')[-1]
        try:
            print(f"[{i}/{total}] Downloading {filename}...")

            # urllib.request is a built-in Python library for HTTP requests, not covered in class
            # ref: https://docs.python.org/3/library/urllib.request.html
            with urllib.request.urlopen(url) as response:
                image_data = response.read()

            # put_object uploads bytes directly to S3
            # Python equivalent of Java putObject from Week 5 lab
            # ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=image_data,
                ContentType='image/jpeg'
            )
            success += 1

        except Exception as e:
            print(f"Failed to process {filename}: {e}")

    print(f"\nUploaded {success}/{total} images to S3.")


def update_dynamodb(url_to_key):
    table = dynamodb.Table(TABLE_NAME)

    # scan to get all items - needed here since we're updating every record
    # scan covered in Week 6 lectorial as a full-table read operation
    response = table.scan()
    items    = response['Items']

    # handle pagination - scan returns max 1MB per call
    # ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/scan.html
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])

    updated = 0
    for item in items:
        old_url = item.get('image_url', '')
        new_key = url_to_key.get(old_url)

        if new_key:
            # update_item with UpdateExpression - same pattern from Week 6 lab
            table.update_item(
                Key={
                    'title':  item['title'],
                    'artist': item['artist']
                },
                UpdateExpression='SET image_url = :new_val',
                ExpressionAttributeValues={':new_val': new_key}
            )
            updated += 1

    print(f"Updated {updated}/{len(items)} DynamoDB records with S3 keys.")


def verify_upload(url_to_key):
    # list_objects_v2 to confirm all images landed in the bucket, not covered in class
    # ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/list_objects_v2.html
    response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=S3_PREFIX)
    count    = len(response.get('Contents', []))
    expected = len(url_to_key)
    status   = 'OK' if count == expected else f'ERROR - expected {expected}'
    print(f"Verification: {count} images in S3 - {status}")


if __name__ == '__main__':
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    songs = data['songs']

    url_to_key = get_unique_images(songs)
    print(f"Found {len(url_to_key)} unique images to upload.")

    create_bucket()
    download_and_upload(url_to_key)
    update_dynamodb(url_to_key)
    verify_upload(url_to_key)

    print(f"\nDone. Images stored at s3://{BUCKET_NAME}/{S3_PREFIX}")