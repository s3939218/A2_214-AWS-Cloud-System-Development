import json
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
TABLE_LOGIN = "login"

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    email = body.get('email', '').strip()
    title = body.get('title', '').strip()
    artist = body.get('artist', '').strip()
    year = body.get('year', '').strip()
    album = body.get('album', '').strip()

    if not email or not title or not artist:
        return response(400, {'message': 'Missing required fields'})

    table = dynamodb.Table(TABLE_LOGIN)

    # Get current user
    result = table.get_item(Key={'email': email})
    user = result.get('Item')

    if not user:
        return response(404, {'message': 'User not found'})

    # Get existing subscriptions or start empty list
    subscriptions = user.get('subscriptions', [])

    # Check subscription already exists
    for sub in subscriptions:
        if sub.get('title') == title and sub.get('artist') == artist:
            return response(400, {'message': 'Already subscribed'})

    # Add new subscription
    subscriptions.append({
        'title': title,
        'artist': artist,
        'year': year,
        'album': album
    })

    # Update user record
    table.update_item(
        Key={'email': email},
        UpdateExpression='SET subscriptions = :s',
        ExpressionAttributeValues={':s': subscriptions}
    )

    return response(200, {'message': 'Subscribed successfully'})

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
