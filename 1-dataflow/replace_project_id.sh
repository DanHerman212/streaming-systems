#!/bin/bash
# Usage: ./replace_project_id.sh YOUR_PROJECT_ID

if [ $# -ne 1 ]; then
  echo "Usage: $0 YOUR_PROJECT_ID"
  exit 1
fi

PROJECT_ID="$1"

sed -i.bak "s|<your-project-id>|$PROJECT_ID|g" dataflow.py

echo "Replaced <your-project-id> with $PROJECT_ID in dataflow.py"