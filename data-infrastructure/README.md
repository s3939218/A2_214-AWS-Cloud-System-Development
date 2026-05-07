# Data Infrastructure Setup

Run these scripts once before starting any backend work. They set up all DynamoDB tables and the S3 bucket the app depends on.

## Prerequisites

- Python 3.x installed
- boto3 installed (`pip install boto3`)
- AWS Academy learner lab credentials configured in `~/.aws/credentials`

## AWS Credentials

Every time you start a new lab session, refresh your credentials:

1. Start the learner lab and wait for the green dot
2. Click **AWS Details → Show**
3. Copy the credentials block into `~/.aws/credentials`

## Run Order

Navigate into this folder first:

```bash
cd data-infrastructure
```

Then run the scripts in this exact order:

```bash
python create_login_table.py
python create_music_table.py
python load_songs.py
python upload_images.py
python create_subscription_table.py
```

Do not skip steps or run them out of order.

## What Each Script Does

| Script | What it creates |

| `create_login_table.py` | `login` DynamoDB table with 10 test users |
| `create_music_table.py` | `music` DynamoDB table with GSI and LSI |
| `load_songs.py` | Loads 137 songs from `2026a2_songs.json` into music table |
| `upload_images.py` | Downloads 71 artist images, uploads to S3, updates DynamoDB |
| `create_subscription_table.py` | `subscription` DynamoDB table for per-user song subscriptions |

## AWS Resources Created

- DynamoDB table: `login`
- DynamoDB table: `music`
- DynamoDB table: `subscription`
- S3 bucket: `rmit-cc-a2-group214-music` (private, public access blocked)

## Notes

- `2026a2_songs.json` must be in the same folder as the scripts
- Scripts are safe to re-run if a table already exists — they will skip creation
- Images are stored privately in S3 — the backend must generate pre-signed URLs to serve them
- Region: `us-east-1`