FROM node:20-alpine as build

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the application
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy the build output to replace the default nginx contents
COPY --from=build /app/dist /usr/share/nginx/html

# Remove default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Create a simple nginx configuration that listens on port 8080
RUN echo 'server {\n\
    listen 8080;\n\
    listen [::]:8080;\n\
    server_name _;\n\
    \n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    \n\
    # Handle React routing\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
    \n\
    # Proxy API requests to the backend\n\
    location /api/ {\n\
        proxy_pass BACKEND_URL_PLACEHOLDER/;\n\
        proxy_http_version 1.1;\n\
        proxy_set_header Upgrade $http_upgrade;\n\
        proxy_set_header Connection "upgrade";\n\
        proxy_set_header Host $host;\n\
        proxy_cache_bypass $http_upgrade;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto $scheme;\n\
    }\n\
}' > /etc/nginx/conf.d/app.conf

# Create a simple entrypoint script
RUN echo '#!/bin/sh\n\
if [ -z "$BACKEND_URL" ]; then\n\
  echo "Warning: BACKEND_URL environment variable is not set. Using default value."\n\
  export BACKEND_URL="http://localhost:8000"\n\
fi\n\
echo "Using backend URL: $BACKEND_URL"\n\
sed -i "s|BACKEND_URL_PLACEHOLDER|$BACKEND_URL|g" /etc/nginx/conf.d/app.conf\n\
echo "Nginx configuration:"\n\
cat /etc/nginx/conf.d/app.conf\n\
echo "Starting nginx..."\n\
exec nginx -g "daemon off;"' > /docker-entrypoint.sh && \
chmod +x /docker-entrypoint.sh

# Make sure nginx.conf is using port 8080
RUN sed -i 's/80;/8080;/g' /etc/nginx/nginx.conf

# Expose port 8080
EXPOSE 8080

# Start Nginx server with the wrapper script
CMD ["/docker-entrypoint.sh"] 