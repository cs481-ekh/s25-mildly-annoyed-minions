#!/bin/bash

IMAGE_NAME=mildly-annoyed-minion
CONTAINER_NAME=mildly-annoyed-minion

if [ ! -d "./output" ]; then
  mkdir output
fi

# Check if 'input' directory exists
if [ -d "./input" ]; then
  echo "✅ 'input' directory found. Proceeding to build and run the Docker container..."

  # Build the Docker image
  docker build -t $IMAGE_NAME .

  # Run the container in detached mode with volume mount
  docker run --user "$(id -u):$(id -g)"  --name $CONTAINER_NAME -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" $IMAGE_NAME

  echo "✅ Docker container has finished running."

  # Clean up: stop and remove the container
  docker stop $CONTAINER_NAME >/dev/null
  docker rm $CONTAINER_NAME >/dev/null

  echo "🧹 Container stopped and removed. Done."

else
  echo "❌ 'input' directory not found."
  echo "👉 Please create an 'input' directory and place your input PDF files there before running this script."
  exit 1
fi
