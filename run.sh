#!/bin/bash

set -euo pipefail

echo "Starting deployment at $(date)"

# Create .env file with environment variables
cat > .env <<EOF
SUPABASE_URL=${SUPABASE_URL}
SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
JWT_SECRET=${JWT_SECRET}
EOF

chmod 600 .env
echo "Environment file created"

# Stop existing containers
echo "Stopping existing containers..."
docker-compose down || true

# Remove old images to save space
echo "Cleaning up old images..."
docker system prune -f || true

# Build and start new containers
echo "Building and starting containers..."
docker-compose up --build -d

echo "Deployment completed successfully at $(date)"

# Show running containers
docker-compose ps