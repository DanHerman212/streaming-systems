#!/bin/bash
set -e

# Grant BigQuery Data Editor role
gcloud projects add-iam-policy-binding streaming-systems-245 \
  --member="serviceAccount:355263607075-compute@developer.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

# Grant BigQuery Job User role
gcloud projects add-iam-policy-binding streaming-systems-245 \
  --member="serviceAccount:355263607075-compute@developer.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

echo "Roles granted successfully."