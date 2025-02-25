# Deploying Job Application Assistant to AWS EC2

This guide provides step-by-step instructions for deploying the Job Application Assistant to AWS EC2.

## Prerequisites

- AWS account with access to EC2, ECR, and IAM
- AWS CLI installed and configured on your local machine
- Docker and Docker Compose installed on your local machine

## Step 1: Set Up AWS Resources

### Create ECR Repositories

1. Create a repository for the backend:
```bash
aws ecr create-repository --repository-name resume-agent-backend
```

2. Create a repository for the frontend:
```bash
aws ecr create-repository --repository-name resume-agent-frontend
```

### Launch an EC2 Instance

1. Go to the AWS EC2 console
2. Click "Launch Instance"
3. Choose an Amazon Machine Image (AMI) - Ubuntu Server 22.04 LTS is recommended
4. Select an instance type (t2.medium or better recommended)
5. Configure instance details:
   - Network: Your VPC
   - Subnet: A public subnet
   - Auto-assign Public IP: Enable
6. Add storage (at least 20GB recommended)
7. Add tags (optional)
8. Configure security group:
   - Allow SSH (port 22) from your IP
   - Allow HTTP (port 80) from anywhere
   - Allow HTTPS (port 443) from anywhere
9. Review and launch
10. Create or select an existing key pair for SSH access

### Create an IAM Role for EC2

1. Go to the IAM console
2. Create a new role for EC2
3. Attach the `AmazonECR-ReadOnly` policy
4. Name the role (e.g., `EC2ECRReadOnly`)
5. Attach the role to your EC2 instance:
   - Select your instance in the EC2 console
   - Actions > Security > Modify IAM Role
   - Select the role you created
   - Save

## Step 2: Set Up the EC2 Instance

1. SSH into your EC2 instance:
```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

2. Copy the setup script to the instance:
```bash
scp -i your-key.pem scripts/setup_ec2.sh ubuntu@your-ec2-public-ip:~/
```

3. Make the script executable and run it:
```bash
chmod +x ~/setup_ec2.sh
~/setup_ec2.sh
```

4. Log out and log back in for the Docker group membership to take effect:
```bash
exit
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

## Step 3: Build and Push Docker Images

1. Build the Docker images locally:
```bash
docker build -t resume-agent-backend ./Backend
docker build -t resume-agent-frontend ./Frontend/job_assistant
```

2. Get the ECR login command:
```bash
aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com
```

3. Tag and push the images:
```bash
docker tag resume-agent-backend your-account-id.dkr.ecr.your-region.amazonaws.com/resume-agent-backend:latest
docker tag resume-agent-frontend your-account-id.dkr.ecr.your-region.amazonaws.com/resume-agent-frontend:latest
docker push your-account-id.dkr.ecr.your-region.amazonaws.com/resume-agent-backend:latest
docker push your-account-id.dkr.ecr.your-region.amazonaws.com/resume-agent-frontend:latest
```

## Step 4: Deploy the Application

1. SSH into your EC2 instance:
```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

2. Log in to ECR:
```bash
aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com
```

3. Create a `.env` file:
```bash
echo "GEMINI_API_KEY=your-gemini-api-key" > ~/resume-agent/.env
```

4. Create a `docker-compose.yml` file:
```bash
cat > ~/resume-agent/docker-compose.yml << 'EOL'
version: '3.8'

services:
  backend:
    image: your-account-id.dkr.ecr.your-region.amazonaws.com/resume-agent-backend:latest
    container_name: resume-agent-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./personal_resume_data.json:/app/personal_resume_data.json
    networks:
      - resume-agent-network

  frontend:
    image: your-account-id.dkr.ecr.your-region.amazonaws.com/resume-agent-frontend:latest
    container_name: resume-agent-frontend
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - resume-agent-network

networks:
  resume-agent-network:
    driver: bridge
EOL
```

5. Start the application:
```bash
cd ~/resume-agent
docker-compose up -d
```

6. Verify the application is running:
```bash
docker-compose ps
```

## Step 5: Set Up a Domain Name (Optional)

1. Register a domain name with AWS Route 53 or another domain registrar
2. Create a DNS A record pointing to your EC2 instance's public IP
3. Set up SSL with Let's Encrypt:
```bash
sudo apt update
sudo apt install -y certbot
sudo certbot certonly --standalone -d your-domain.com
```

4. Update your nginx configuration to use SSL

## Step 6: Set Up CI/CD with GitHub Actions (Optional)

1. Push your code to a GitHub repository
2. Set up GitHub Actions secrets:
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - AWS_REGION
   - EC2_HOST
   - EC2_USERNAME
   - EC2_SSH_KEY
   - GEMINI_API_KEY
3. Push to the main branch to trigger the deployment

## Troubleshooting

### Application Not Accessible

1. Check if the containers are running:
```bash
docker ps
```

2. Check the container logs:
```bash
docker logs resume-agent-backend
docker logs resume-agent-frontend
```

3. Verify the security group allows traffic on ports 80 and 8000

### Backend API Not Working

1. Check if the backend container is running:
```bash
docker ps | grep resume-agent-backend
```

2. Check the backend logs:
```bash
docker logs resume-agent-backend
```

3. Verify the GEMINI_API_KEY is set correctly in the .env file

### Frontend Not Connecting to Backend

1. Check the nginx configuration in the frontend container
2. Verify the backend URL in the frontend code
3. Check if the backend is accessible from the frontend container:
```bash
docker exec resume-agent-frontend curl -I http://backend:8000
```

## Maintenance

### Updating the Application

1. Build and push new Docker images
2. SSH into your EC2 instance
3. Pull the new images:
```bash
cd ~/resume-agent
docker-compose pull
docker-compose up -d
```

### Backing Up Data

1. Back up the personal_resume_data.json file:
```bash
scp -i your-key.pem ubuntu@your-ec2-public-ip:~/resume-agent/personal_resume_data.json ./backup/
```

### Monitoring

1. Check container resource usage:
```bash
docker stats
```

2. Set up CloudWatch monitoring for your EC2 instance 