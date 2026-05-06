import json
import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
TABLE_MUSIC = "music"
S3_BUCKET = "your-bucket-name"  # placeholder
S3_REGION = "us-east-1"

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    title = body.get('title', '').strip()
    artist = body.get('artist', '').strip()
    year = body.get('year', '').strip()
    album = body.get('album', '').strip()

    # At least one field must be provided
    if not any([title, artist, year, album]):
        return response(400, {'message': 'At least one search field is required'})

    table = dynamodb.Table(TABLE_MUSIC)

    # Build and filter expression dynamically
    filters = []
    if title:
        filters.append(Attr('title').eq(title))
    if artist:
        filters.append(Attr('artist').eq(artist))
    if year:
        filters.append(Attr('year').eq(year))
    if album:
        filters.append(Attr('album').eq(album))

    filter_expression = filters[0]
    for f in filters[1:]:
        filter_expression = filter_expression & f

    result = table.scan(FilterExpression=filter_expression)
    songs = result.get('Items', [])

    if not songs:
        return response(200, {'message': 'No result is retrieved. Please query again', 'songs': []})

    # Attach S3 image URL to each song
    for song in songs:
        artist_name = song.get('artist', '').replace(' ', '')
        song['image_url'] = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{artist_name}.jpg"

    return response(200, {'message': 'success', 'songs': songs})

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
