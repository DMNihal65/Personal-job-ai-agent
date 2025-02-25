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

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 8080 (Cloud Run prefers this port)
EXPOSE 8080

# Create a wrapper script to replace environment variables in the nginx config
RUN echo '#!/bin/sh\n\
if [ -z "$BACKEND_URL" ]; then\n\
  echo "Warning: BACKEND_URL environment variable is not set. Using default value."\n\
  export BACKEND_URL="http://localhost:8000"\n\
fi\n\
echo "Using backend URL: $BACKEND_URL"\n\
sed -i "s|BACKEND_URL_PLACEHOLDER|$BACKEND_URL|g" /etc/nginx/conf.d/default.conf\n\
echo "Nginx configuration:"\n\
cat /etc/nginx/conf.d/default.conf\n\
echo "Starting nginx..."\n\
nginx -g "daemon off;"' > /docker-entrypoint.sh && \
chmod +x /docker-entrypoint.sh

# Make sure nginx listens on port 8080
RUN sed -i 's/listen\s*80;/listen 8080;/g' /etc/nginx/conf.d/default.conf

# Start Nginx server with the wrapper script
CMD ["/docker-entrypoint.sh"] 