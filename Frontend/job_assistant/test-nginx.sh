#!/bin/bash

# Build the Docker image
docker build -t frontend-test .

# Run the container with the test environment variable
docker run -d -p 8080:8080 -e BACKEND_URL=http://test-backend:8000 --name frontend-test frontend-test

# Wait for the container to start
sleep 5

# Check if nginx is running and listening on port 8080
docker exec frontend-test ps aux | grep nginx

# Check the nginx configuration
docker exec frontend-test cat /etc/nginx/conf.d/default.conf

# Check if the port is correctly configured
docker exec frontend-test netstat -tulpn | grep 8080

# Clean up
docker stop frontend-test
docker rm frontend-test 