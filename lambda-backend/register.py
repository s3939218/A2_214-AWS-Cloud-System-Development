import json
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
TABLE_LOGIN = "login"

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    email = body.get('email', '').strip()
    # changed user_name to username to match field name sent by frontend register.js - s3874656
    user_name = body.get('username', '').strip()
    password = body.get('password', '').strip()

    if not email or not user_name or not password:
        return response(400, {'message': 'All fields are required'})

    table = dynamodb.Table(TABLE_LOGIN)

    result = table.get_item(Key={'email': email})
    if result.get('Item'):
        # added exists field - frontend register.js checks data.exists to show duplicate email error - s3874656
        return response(200, {'exists': True, 'message': 'The email already exists'})

    table.put_item(Item={
        'email': email,
        'user_name': user_name,
        'password': password
    })

    return response(200, {'exists': False, 'message': 'Registration successful'})

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