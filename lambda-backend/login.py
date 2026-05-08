import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
TABLE_LOGIN = "login"

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    email = body.get('email', '').strip()
    password = body.get('password', '').strip()

    if not email or not password:
        return response(400, {'message': 'email or password is invalid'})

    table = dynamodb.Table(TABLE_LOGIN)

    result = table.get_item(Key={'email': email})
    user = result.get('Item')

    if not user or user.get('password') != password:
        return response(400, {'message': 'email or password is invalid'})

    return response(200, {
        # added success field - frontend login.js checks data.success to redirect - s3874656
        'success': True,
        'message': 'Login successful',
        # renamed to match frontend expectation - login.js stores data.username - s3874656
        'username': user.get('user_name'),
        'email': email
    })

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