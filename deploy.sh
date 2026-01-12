#!/bin/bash

echo "Building Docker image..."
docker build -t aixdb:latest .

echo ""
echo "Starting Docker container..."
docker-compose up -d

echo ""
echo "=" * 50
echo "Deployment complete!"
echo "=" * 50
echo "Access the application at: http://localhost:5000"
echo ""
echo "Useful commands:"
echo "  docker-compose logs -f    # View logs"
echo "  docker-compose down       # Stop container"
echo "  docker-compose restart    # Restart container"
echo "=" * 50
