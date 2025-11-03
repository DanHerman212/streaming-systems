#!/bin/bash
set -e

REGION="YOUR_REGION"
PROJECT="YOUR_PROJECT_ID"
NAME="streaming-systems-repo"
REPO="$REGION-docker.pkg.dev/$PROJECT/$NAME"

# Build and push mta-processor image
echo "Building mta-processor image..."
if docker build -t "$REPO/mta-processor" ./2-event-processor; then
  echo "Successfully built $REPO/mta-processor"
  echo "Pushing $REPO/mta-processor to registry..."
  if docker push "$REPO/mta-processor"; then
    echo "Successfully pushed $REPO/mta-processor"
  else
    echo "Failed to push $REPO/mta-processor" >&2
    exit 1
  fi
else
  echo "Failed to build $REPO/mta-processor" >&2
  exit 1
fi

# Build and push event-task-enqueuer image
echo "Building event-task-enqueuer image..."
if docker build -t "$REPO/event-task-enqueuer" ./3-task-queue; then
  echo "Successfully built $REPO/event-task-enqueuer"
  echo "Pushing $REPO/event-task-enqueuer to registry..."
  if docker push "$REPO/event-task-enqueuer"; then
    echo "Successfully pushed $REPO/event-task-enqueuer"
  else
    echo "Failed to push $REPO/event-task-enqueuer" >&2
    exit 1
  fi
else
  echo "Failed to build $REPO/event-task-enqueuer" >&2
  exit 1
fi

echo ""
echo "All images built and pushed successfully:"
echo "- $REPO/mta-processor"
echo "- $REPO/event-task-enqueuer"