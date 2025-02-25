#!/bin/bash

# Exit on error
set -e

# Update system packages
echo "Updating system packages..."
sudo apt update -y
sudo apt upgrade -y

# Install Docker
echo "Installing Docker..."
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update -y
sudo apt install -y docker-ce
sudo systemctl enable --now docker

# Add current user to docker group
echo "Adding user to docker group..."
sudo usermod -aG docker $USER

# Install Docker Compose
echo "Installing Docker Compose..."
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install AWS CLI
echo "Installing AWS CLI..."
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
sudo apt install -y unzip
unzip awscliv2.zip
sudo ./aws/install
rm -rf aws awscliv2.zip

# Create directory for application
echo "Creating application directory..."
mkdir -p ~/resume-agent
cd ~/resume-agent

# Create empty personal_resume_data.json file
echo "Creating empty personal_resume_data.json file..."
echo "{}" > personal_resume_data.json

echo "Setup complete! Please log out and log back in for the docker group membership to take effect."
echo "Next steps:"
echo "1. Configure AWS CLI with 'aws configure'"
echo "2. Set up your .env file with your GEMINI_API_KEY"
echo "3. Pull your Docker images from ECR and run the application" 