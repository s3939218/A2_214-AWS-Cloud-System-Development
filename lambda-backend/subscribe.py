import json
import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
# switched to subscription table - login table should not store subscriptions - s3874656
TABLE_SUBSCRIPTION = 'subscription'
TABLE_MUSIC        = 'music'

def lambda_handler(event, context):
    body  = json.loads(event.get('body', '{}'))
    email = body.get('email', '').strip()
    # frontend sends song as a nested object - s3874656
    song  = body.get('song', {})
    title  = song.get('title', '').strip()
    artist = song.get('artist', '').strip()
    year   = song.get('year', '').strip()
    album  = song.get('album', '').strip()

    if not email or not title or not artist:
        return response(400, {'message': 'Missing required fields'})

    # compound sort key uniquely identifies the song version - s3874656
    title_artist = f"{title}#{artist}#{year}"

    table  = dynamodb.Table(TABLE_SUBSCRIPTION)
    result = table.get_item(Key={'email': email, 'title_artist': title_artist})

    if result.get('Item'):
        return response(400, {'message': 'Already subscribed'})

    # fetch S3 key from music table so pre-signed URLs can be generated when listing - s3874656
    music_table  = dynamodb.Table(TABLE_MUSIC)
    music_result = music_table.scan(
        FilterExpression=Attr('title').eq(title) & Attr('artist_name').eq(artist)
    )
    music_items = music_result.get('Items', [])
    image_url   = music_items[0].get('image_url', '') if music_items else ''

    table.put_item(Item={
        'email':        email,
        'title_artist': title_artist,
        'title':        title,
        'artist_name':  artist,
        'year':         year,
        'album':        album,
        'image_url':    image_url
    })

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