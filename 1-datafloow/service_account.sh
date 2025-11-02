#!/bin/bash

# Usage:
#   ./grant_dataflow_service_agent_role.sh <PROJECT_ID> <WORKER_SERVICE_ACCOUNT_EMAIL>
#   ./grant_dataflow_service_agent_role.sh <PROJECT_ID> --print-default-sa
# Example:
#   ./grant_dataflow_service_agent_role.sh streaming-systems-245 1234567890-compute@developer.gserviceaccount.com
#   ./grant_dataflow_service_agent_role.sh streaming-systems-245 --print-default-sa

set -e


print_default_sa() {
  local project_id="$1"
  local project_number=$(gcloud projects describe "$project_id" --format='value(projectNumber)')
  echo "${project_number}-compute@developer.gserviceaccount.com"
}

if [ "$#" -eq 2 ] && [ "$2" = "--print-default-sa" ]; then
  print_default_sa "$1"
  exit 0
fi

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <PROJECT_ID> <WORKER_SERVICE_ACCOUNT_EMAIL>"
  echo "       $0 <PROJECT_ID> --print-default-sa"
  exit 1
fi

PROJECT_ID="$1"
WORKER_SA="$2"

# Get the project number
echo "Fetching project number for $PROJECT_ID..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')

# Dataflow service agent principal
DATAFLOW_AGENT="service-${PROJECT_NUMBER}@dataflow-service-producer-prod.iam.gserviceaccount.com"

# Grant the Cloud Dataflow Service Agent role to the Dataflow service agent on the worker service account
echo "Granting roles/iam.serviceAccountUser to $DATAFLOW_AGENT on $WORKER_SA..."
gcloud iam service-accounts add-iam-policy-binding "$WORKER_SA" \
  --project="$PROJECT_ID" \
  --member="serviceAccount:$DATAFLOW_AGENT" \
  --role="roles/iam.serviceAccountUser"

echo "Granting roles/dataflow.serviceAgent to $DATAFLOW_AGENT at project level..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$DATAFLOW_AGENT" \
  --role="roles/dataflow.serviceAgent"

echo "Done."
