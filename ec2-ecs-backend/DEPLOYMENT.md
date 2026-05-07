# Deployment Guide

This guide explains how to deploy the Flask backend using AWS Academy in the us-east-1 region with LabRole.

The backend container runs on port 80 for both EC2 and ECS deployments.

Before starting, Gazi needs to run these scripts in order in the same lab session:

create_music_table.py
create_login_table.py
load_songs.py
upload_images.py

## Part A — EC2

### 1. Launch instance (AWS Console)
Launch an EC2 Instance in the AWS Console:

AMI: Ubuntu Server 24.04 LTS
Instance type: t3.micro
Key pair: vockey
Security group rules:
SSH (port 22) → My IP
HTTP (port 80) → Anywhere (0.0.0.0/0)
Under Advanced Details:
IAM instance profile → LabRole

### 2. Connect to the instance
On the Windows PowerShell run this once to fix permissions
icacls "labsuser.pem" /inheritancelevel:r /grant:r "$($env:USERNAME):R"
ssh -i labsuser.pem ubuntu@<EC2_PUBLIC_IP>


### 3. Install dependencies
sudo apt update
sudo apt update && sudo apt install -y python3-pip python3-venv git


### 4. Copy code to instance
git clone https://github.com/s3939218/A2_214-AWS-Cloud-System-Development.git app
cd app/ec2-ecs-backend

### 5. Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt


### 6. Create .env file
AWS_REGION=us-east-1
LOGIN_TABLE=login
MUSIC_TABLE=music
S3_BUCKET=rmit-cc-a2-group214-music
PRESIGN_EXPIRY=3600


 ### 7. Set up and start the service

sudo tee /etc/systemd/system/flask-app.service << 'EOF'
[Unit]
Description=Music Subscription Flask Backend
After=network.target

[Service]
User=root
WorkingDirectory=/home/ubuntu/app/ec2-ecs-backend
EnvironmentFile=/home/ubuntu/app/ec2-ecs-backend/.env
ExecStart=/home/ubuntu/app/ec2-ecs-backend/venv/bin/gunicorn -b 0.0.0.0:80 -w 2 --access-logfile - app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable flask-app
sudo systemctl start flask-app

### 8. Test

sudo systemctl status flask-app
curl http://localhost/health
Expected: {"status":"ok"}

Test from browser: http://<EC2_PUBLIC_IP>/health

Part B — ECS Fargate
### 1. Fix ECS service-linked role (AWS CloudShell)
Open CloudShell from the AWS Console footer and run:


aws iam create-service-linked-role --aws-service-name ecs.amazonaws.com
Ignore "role name has been taken" — means it already exists.

### 2. Create ECR repository (AWS Console)
ECR → Create repository:

Visibility: Private
Name: music-backend
Copy the repository URI shown after creation.

### 3. Install Docker and AWS CLI on EC2

sudo apt install -y docker.io unzip
sudo systemctl start docker

curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

### 4. Build and push Docker image (on EC2)

cd /home/ubuntu/app/ec2-ecs-backend
sudo docker build -t music-backend .

aws ecr get-login-password --region us-east-1 | 
  sudo docker login --username AWS --password-stdin 
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

sudo docker tag music-backend:latest 
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/music-backend:latest

sudo docker push 
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/music-backend:latest

### 5. Create security group (AWS Console)
EC2 → Security Groups → Create security group:

Name: sgMusicBackend
Inbound: Custom TCP, port 80, source Anywhere (0.0.0.0/0)

### 6. Create ALB + target group (AWS Console)
EC2 → Load Balancers → Create → Application Load Balancer:

Name: music-backend-alb
Scheme: Internet-facing
Select at least 2 AZs (e.g. us-east-1a and us-east-1b)
Security group: sgMusicBackend
Listener port: 80
 Create target group:
Type: IP addresses
Name: music-backend-tg
Port: 80
Health check path: /health
Next → Create target group
Back in ALB: select music-backend-tg → Create load balancer

### 7. Create ECS cluster (AWS Console)
ECS → Clusters → Create cluster:

Name: music-cluster
Infrastructure: Fargate only

### 8. Create task definition (AWS Console)
ECS → Task Definitions → Create new task definition:

Family: music-backend-task
Launch type: Fargate
Task role: LabRole | Task execution role: LabRole
CPU: 0.25 vCPU | Memory: 0.5 GB
Add container:

Name: music-backend
Image: <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/music-backend:latest
Port: 80
Environment variables:
Key	Value
AWS_REGION	us-east-1
LOGIN_TABLE	login
MUSIC_TABLE	music
S3_BUCKET	rmit-cc-a2-group214-music
PRESIGN_EXPIRY	3600

### 9. Create ECS service (AWS Console)
ECS → music-cluster → Services → Create:

Launch type: Fargate
Task definition: music-backend-task (latest)
Service name: music-backend-svc
Desired tasks: 1
VPC: default, select all subnets
Security group: sgMusicBackend
Load balancer: music-backend-alb | Listener: HTTP:80
Target group: music-backend-tg
Health check grace period: 30 seconds
Create

### 10. Test
Wait 3 minutes. Check EC2 → Target Groups → music-backend-tg → Targets tab for Healthy status.


curl http://<ALB_DNS_NAME>/health
Expected: {"status":"ok"}

ALB DNS name is shown on the Load Balancers page.