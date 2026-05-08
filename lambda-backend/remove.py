import json
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
# switched to subscription table - login table should not store subscriptions - s3874656
TABLE_SUBSCRIPTION = 'subscription'

def lambda_handler(event, context):
    body  = json.loads(event.get('body', '{}'))
    email = body.get('email', '').strip()
    # frontend sends song as a nested object - s3874656
    song   = body.get('song', {})
    title  = song.get('title', '').strip()
    artist = song.get('artist', '').strip()
    year   = song.get('year', '').strip()

    if not email or not title or not artist:
        return response(400, {'message': 'Missing required fields'})

    # reconstruct compound sort key to target the exact subscription - s3874656
    title_artist = f"{title}#{artist}#{year}"

    table  = dynamodb.Table(TABLE_SUBSCRIPTION)
    result = table.get_item(Key={'email': email, 'title_artist': title_artist})

    if not result.get('Item'):
        return response(404, {'message': 'Subscription not found'})

    # delete_item targets exact key - s3874656
    table.delete_item(Key={'email': email, 'title_artist': title_artist})

    return response(200, {'message': 'Removed successfully'})


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