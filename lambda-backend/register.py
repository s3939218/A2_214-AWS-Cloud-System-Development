import json
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
TABLE_LOGIN = "login"

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    email = body.get('email', '').strip()
    user_name = body.get('user_name', '').strip()
    password = body.get('password', '').strip()

    if not email or not user_name or not password:
        return response(400, {'message': 'All fields are required'})

    table = dynamodb.Table(TABLE_LOGIN)

    # Check existing email
    result = table.get_item(Key={'email': email})
    if result.get('Item'):
        return response(400, {'message': 'The email already exists'})

    # Save new user
    table.put_item(Item={
        'email': email,
        'user_name': user_name,
        'password': password
    })

    return response(200, {'message': 'Registration successful'})

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
