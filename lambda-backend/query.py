import json
import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
# updated bucket name from placeholder to actual bucket - s3874656
S3_BUCKET  = 'rmit-cc-a2-group214-music'
TABLE_MUSIC = 'music'

s3 = boto3.client('s3', region_name='us-east-1')


def presign(key):
    # generate pre-signed URL - bucket is private so direct S3 URLs won't work - s3874656
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
    body   = json.loads(event.get('body', '{}'))
    title  = body.get('title', '').strip()
    artist = body.get('artist', '').strip()
    year   = body.get('year', '').strip()
    album  = body.get('album', '').strip()

    if not any([title, artist, year, album]):
        return response(400, {'message': 'At least one search field is required'})

    table = dynamodb.Table(TABLE_MUSIC)

    if artist:
        # Query GSI artist-year-index instead of scan - efficient for artist searches - s3874656
        key_expr = Key('artist_name').eq(artist)
        if year:
            key_expr = key_expr & Key('year').eq(year)

        filter_exprs = []
        if title:
            filter_exprs.append(Attr('title').eq(title))
        if album:
            filter_exprs.append(Attr('album').eq(album))

        query_kwargs = {
            'IndexName': 'artist-year-index',
            'KeyConditionExpression': key_expr
        }
        if filter_exprs:
            expr = filter_exprs[0]
            for f in filter_exprs[1:]:
                expr = expr & f
            query_kwargs['FilterExpression'] = expr

        result = table.query(**query_kwargs)
        songs  = result.get('Items', [])

    elif title:
        # Query base table by title partition key - s3874656
        filter_exprs = []
        if year:
            filter_exprs.append(Attr('year').eq(year))
        if album:
            filter_exprs.append(Attr('album').eq(album))

        query_kwargs = {'KeyConditionExpression': Key('title').eq(title)}
        if filter_exprs:
            expr = filter_exprs[0]
            for f in filter_exprs[1:]:
                expr = expr & f
            query_kwargs['FilterExpression'] = expr

        result = table.query(**query_kwargs)
        songs  = result.get('Items', [])

    else:
        # Scan only as last resort when no key attribute is available - s3874656
        filter_exprs = []
        if year:
            filter_exprs.append(Attr('year').eq(year))
        if album:
            filter_exprs.append(Attr('album').eq(album))

        expr = filter_exprs[0]
        for f in filter_exprs[1:]:
            expr = expr & f

        result = table.scan(FilterExpression=expr)
        songs  = result.get('Items', [])

    if not songs:
        # return empty array - frontend checks data.length === 0 - s3874656
        return response(200, [])

    formatted = []
    for song in songs:
        formatted.append({
            'title':     song.get('title'),
            # use artist_name not artist - artist field stores compound sort key - s3874656
            'artist':    song.get('artist_name'),
            'year':      song.get('year', ''),
            'album':     song.get('album', ''),
            # generate pre-signed URL from S3 key stored in DynamoDB - s3874656
            'image_url': presign(song.get('image_url', ''))
        })

    # return plain array - frontend does data.forEach() expecting array not object - s3874656
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