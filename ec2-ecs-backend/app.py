import os
import boto3
from flask import Flask, request, jsonify
from flask_cors import CORS
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

app = Flask(__name__)
CORS(app)

REGION         = os.environ.get('AWS_REGION', 'us-east-1')
TABLE_LOGIN    = os.environ.get('LOGIN_TABLE', 'login')
TABLE_MUSIC    = os.environ.get('MUSIC_TABLE', 'music')
TABLE_SUBSCRIPTION = os.environ.get('SUBSCRIPTION_TABLE', 'subscription')
S3_BUCKET      = os.environ.get('S3_BUCKET', 'rmit-cc-a2-group214-music')
PRESIGN_EXPIRY = int(os.environ.get('PRESIGN_EXPIRY', '3600'))

dynamodb = boto3.resource('dynamodb', region_name=REGION)
s3       = boto3.client('s3', region_name=REGION)


def presign(key):
    if not key:
        return ''
    try:
        return s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': key},
            ExpiresIn=PRESIGN_EXPIRY,
        )
    except ClientError:
        return ''


def scan_all(table, **kwargs):
    resp  = table.scan(**kwargs)
    items = resp.get('Items', [])
    while 'LastEvaluatedKey' in resp:
        resp = table.scan(ExclusiveStartKey=resp['LastEvaluatedKey'], **kwargs)
        items.extend(resp.get('Items', []))
    return items


# health 

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


# login 

@app.route('/login', methods=['POST'])
def login():
    body     = request.get_json(force=True) or {}
    email    = body.get('email', '').strip()
    password = body.get('password', '').strip()

    if not email or not password:
        return jsonify({'success': False, 'message': 'email or password is invalid'}), 400

    table  = dynamodb.Table(TABLE_LOGIN)
    result = table.get_item(Key={'email': email})
    user   = result.get('Item')

    if not user or user.get('password') != password:
        return jsonify({'success': False, 'message': 'email or password is invalid'}), 400

    return jsonify({'success': True, 'username': user['user_name'], 'email': email})


# register

@app.route('/register', methods=['POST'])
def register():
    body     = request.get_json(force=True) or {}
    email    = body.get('email', '').strip()
    username = body.get('username', '').strip()
    password = body.get('password', '').strip()

    if not email or not username or not password:
        return jsonify({'exists': False, 'message': 'All fields are required'}), 400

    table  = dynamodb.Table(TABLE_LOGIN)
    result = table.get_item(Key={'email': email})

    if result.get('Item'):
        return jsonify({'exists': True, 'message': 'The email already exists'})

    table.put_item(Item={'email': email, 'user_name': username, 'password': password})
    return jsonify({'exists': False, 'message': 'Registration successful'})


# search 

@app.route('/search', methods=['POST'])
def search():
    body   = request.get_json(force=True) or {}
    title  = body.get('title', '').strip()
    artist = body.get('artist', '').strip()
    year   = body.get('year', '').strip()
    album  = body.get('album', '').strip()

    if not any([title, artist, year, album]):
        return jsonify({'message': 'At least one search field is required'}), 400

    table = dynamodb.Table(TABLE_MUSIC)

    if artist:
        # Query GSI artist-year-index - efficient for artist-based searches
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

        response = table.query(**query_kwargs)
        items    = response.get('Items', [])

    elif title:
        # Query base table by title partition key
        filter_exprs = []
        if year:
            filter_exprs.append(Attr('year').eq(year))
        if album:
            filter_exprs.append(Attr('album').eq(album))

        query_kwargs = {
            'KeyConditionExpression': Key('title').eq(title)
        }
        if filter_exprs:
            expr = filter_exprs[0]
            for f in filter_exprs[1:]:
                expr = expr & f
            query_kwargs['FilterExpression'] = expr

        response = table.query(**query_kwargs)
        items    = response.get('Items', [])

    else:
        # Scan - only when searching by year or album alone with no key available
        filter_exprs = []
        if year:
            filter_exprs.append(Attr('year').eq(year))
        if album:
            filter_exprs.append(Attr('album').eq(album))

        expr = filter_exprs[0]
        for f in filter_exprs[1:]:
            expr = expr & f

        items = scan_all(table, FilterExpression=expr)

    return jsonify([
        {
            'title':     item['title'],
            'artist':    item['artist_name'],
            'year':      item.get('year', ''),
            'album':     item.get('album', ''),
            'image_url': presign(item.get('image_url', '')),
        }
        for item in items
    ])


# subscriptions 

@app.route('/subscriptions', methods=['GET'])
def list_subscriptions():
    email = request.args.get('email', '').strip()

    if not email:
        return jsonify([])

    # query subscription table by email - efficient partition key lookup
    table    = dynamodb.Table(TABLE_SUBSCRIPTION)
    response = table.query(
        KeyConditionExpression=Key('email').eq(email)
    )
    items = response.get('Items', [])

    return jsonify([
        {
            'title':     item.get('title'),
            'artist':    item.get('artist_name'),
            'year':      item.get('year', ''),
            'album':     item.get('album', ''),
            'image_url': presign(item.get('image_url', ''))
        }
        for item in items
    ])


# subscribe 

@app.route('/subscribe', methods=['POST'])
def subscribe():
    body   = request.get_json(force=True) or {}
    email  = body.get('email', '').strip()
    song   = body.get('song', {})
    title  = song.get('title', '').strip()
    artist = song.get('artist', '').strip()
    year   = song.get('year', '').strip()
    album  = song.get('album', '').strip()

    if not email or not title or not artist:
        return jsonify({'message': 'Missing required fields'}), 400

    # sort key uniquely identifies the song version
    title_artist = f"{title}#{artist}#{year}"

    table  = dynamodb.Table(TABLE_SUBSCRIPTION)
    result = table.get_item(Key={'email': email, 'title_artist': title_artist})

    if result.get('Item'):
        return jsonify({'message': 'Already subscribed'}), 400

    # fetch S3 key from music table for pre-signed URL generation later
    music_items = scan_all(
        dynamodb.Table(TABLE_MUSIC),
        FilterExpression=Attr('title').eq(title) & Attr('artist_name').eq(artist)
    )
    image_url = music_items[0].get('image_url', '') if music_items else ''

    table.put_item(Item={
        'email':       email,
        'title_artist': title_artist,
        'title':       title,
        'artist_name': artist,
        'year':        year,
        'album':       album,
        'image_url':   image_url
    })

    return jsonify({'message': 'Subscribed successfully'})


# remove 

@app.route('/remove', methods=['DELETE'])
def remove():
    body   = request.get_json(force=True) or {}
    email  = body.get('email', '').strip()
    song   = body.get('song', {})
    title  = song.get('title', '').strip()
    artist = song.get('artist', '').strip()
    year   = song.get('year', '').strip()

    if not email or not title or not artist:
        return jsonify({'message': 'Missing required fields'}), 400

    # reconstruct sort key to target exact item
    title_artist = f"{title}#{artist}#{year}"

    table  = dynamodb.Table(TABLE_SUBSCRIPTION)
    result = table.get_item(Key={'email': email, 'title_artist': title_artist})

    if not result.get('Item'):
        return jsonify({'message': 'Subscription not found'}), 404

    table.delete_item(Key={'email': email, 'title_artist': title_artist})
    return jsonify({'message': 'Removed successfully'})


# entry point 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
