#!/bin/bash
set -e

REPO="gcr.io/YOUR_PROJECT_ID"

# Build mta-processor image from 2-event-processor
echo "Building mta-processor image..."
if docker build -t "$REPO/mta-processor" ./2-event-processor; then
  echo "Successfully built $REPO/mta-processor"
else
  echo "Failed to build $REPO/mta-processor" >&2
  exit 1
fi

# Build event-task-enqueuer image from 3-task-queue
echo "Building event-task-enqueuer image..."
if docker build -t "$REPO/event-task-enqueuer" ./3-task-queue; then
  echo "Successfully built $REPO/event-task-enqueuer"
else
  echo "Failed to build $REPO/event-task-enqueuer" >&2
  exit 1
fi

echo "\nAll images built successfully:"
echo "- $REPO/mta-processor"
echo "- $REPO/event-task-enqueuer"
