#!/bin/bash

# Wait for deployment
echo "Waiting for deployment to be ready..."
kubectl wait --for=condition=available deployment/python-webapp-python-webapp --timeout=300s

# Get service URL
SERVICE_URL=$(minikube service python-webapp-service --url)

# Test health endpoint
echo "Testing health endpoint..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${SERVICE_URL}/health)

if [ $HEALTH_STATUS -eq 200 ]; then
    echo "Health check passed"
    exit 0
else
    echo "Health check failed with status: $HEALTH_STATUS"
    exit 1
fi