import json
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
TABLE_SUBSCRIPTION = 'subscription'
S3_BUCKET          = 'rmit-cc-a2-group214-music'

s3 = boto3.client('s3', region_name='us-east-1')


def presign(key):
    if not key:
        return ''
    try:
        return s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': key},
            ExpiresIn=3600
        )
    except ClientError:
        return ''


def lambda_handler(event, context):
    params = event.get('queryStringParameters') or {}
    email  = params.get('email', '').strip()

    if not email:
        return response(400, [])

    table  = dynamodb.Table(TABLE_SUBSCRIPTION)
    result = table.query(
        KeyConditionExpression=Key('email').eq(email)
    )
    items = result.get('Items', [])

    formatted = []
    for item in items:
        formatted.append({
            'title':     item.get('title'),
            'artist':    item.get('artist_name'),
            'year':      item.get('year', ''),
            'album':     item.get('album', ''),
            'image_url': presign(item.get('image_url', ''))
        })

    return response(200, formatted)


def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }