#!/bin/bash

echo "🚀 Starting update procedure..."

# 1. Download the latest version of the image from the Container Registry
echo "⬇️ Pulling new images..."
docker-compose pull

# 2. Recreate and restart the containers (only those where the image has changed)
echo "🔄 Recreating containers in the background..."
docker-compose up -d

# 3. Cleanup
# Removes old unnamed (dangling) images that take up gigabytes of precious space
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "✅ Update completed!"
echo "🔍 To see what's happening under the hood, use: docker-compose logs -f"