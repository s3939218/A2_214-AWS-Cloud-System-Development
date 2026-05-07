Backend API for the Music Subscription app built using Flask and boto3.

The app was deployed in two different ways:

EC2 — running directly on the EC2 instance using gunicorn on port 80
ECS Fargate — deployed as a container behind an Application Load Balancer 

# API Endpoints
Method	Endpoint	                     Description
GET	    /health	Simple                  health check
POST	/login	Checks                  user login details
POST	/register	                    Creates a new account
POST	/search          	            Searches the music catalogue
GET	    /subscriptions?user=<email>  	Returns user subscriptions
POST	/subscribe	                    Adds a subscription
DELETE	/remove	                        Removes a subscription


## Run locally 
python3 -m venv venv 
source venv/bin/activate

# Windows: 
venv\Scripts\activate
pip install -r requirements.txt

# Create a .env file:
AWS_REGION=us-east-1
LOGIN_TABLE=login
MUSIC_TABLE=music
S3_BUCKET=rmit-cc-a2-group214-music
PRESIGN_EXPIRY=3600

AWS credentials must be configured in ~/.aws/credentials.

## Deploy 
See DEPLOYMENT.md
