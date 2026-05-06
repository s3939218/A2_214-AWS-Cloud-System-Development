import json
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
TABLE_LOGIN = "login"

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    email = body.get('email', '').strip()
    title = body.get('title', '').strip()
    artist = body.get('artist', '').strip()

    if not email or not title or not artist:
        return response(400, {'message': 'Missing required fields'})

    table = dynamodb.Table(TABLE_LOGIN)

    # Get current user
    result = table.get_item(Key={'email': email})
    user = result.get('Item')

    if not user:
        return response(404, {'message': 'User not found'})

    # Filter out the song to remove
    subscriptions = user.get('subscriptions', [])
    updated = [s for s in subscriptions if not (s.get('title') == title and s.get('artist') == artist)]

    if len(updated) == len(subscriptions):
        return response(404, {'message': 'Subscription not found'})

    # Save updated subscriptions
    table.update_item(
        Key={'email': email},
        UpdateExpression='SET subscriptions = :s',
        ExpressionAttributeValues={':s': updated}
    )

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
