#!/bin/bash

# ============================================
# MTA Streaming Pipeline - One-Click Deployment
# ============================================
# This script automates the entire deployment process
# Usage: ./deploy.sh <PROJECT_ID> <REGION>
# Example: ./deploy.sh my-gcp-project us-east1

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}▶ $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <PROJECT_ID> [REGION]"
    echo "Example: $0 my-gcp-project us-east1"
    exit 1
fi

PROJECT_ID=$1
REGION=${2:-"us-east1"}  # Default to us-east1 if not provided

print_step "Starting MTA Streaming Pipeline Deployment"
echo ""
print_info "Project ID: $PROJECT_ID"
print_info "Region: $REGION"
echo ""

# Confirm with user
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Deployment cancelled"
    exit 1
fi

# ============================================
# STEP 1: Enable Required APIs
# ============================================
print_step "Step 1/6: Enabling Required GCP APIs"

gcloud services enable \
  cloudresourcemanager.googleapis.com \
  cloudtasks.googleapis.com \
  pubsub.googleapis.com \
  iam.googleapis.com \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  cloudscheduler.googleapis.com \
  dataflow.googleapis.com \
  bigquery.googleapis.com \
  storage-component.googleapis.com \
  --project=$PROJECT_ID

print_success "APIs enabled"
echo ""

# ============================================
# STEP 2: Create Artifact Registry
# ============================================
print_step "Step 2/6: Creating Artifact Registry Repository"

# Check if repository already exists
if gcloud artifacts repositories describe streaming-systems-repo \
  --location=$REGION \
  --project=$PROJECT_ID &>/dev/null; then
  print_info "Artifact Registry repository already exists, skipping creation"
else
  gcloud artifacts repositories create streaming-systems-repo \
    --repository-format=docker \
    --location=$REGION \
    --project=$PROJECT_ID
  print_success "Artifact Registry repository created"
fi
echo ""

# ============================================
# STEP 3: Build and Push Container Images
# ============================================
print_step "Step 3/6: Building and Pushing Container Images"

print_info "Building mta-processor..."
cd 2-event-processor
gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/streaming-systems-repo/mta-processor \
  --project=$PROJECT_ID
print_success "mta-processor image built and pushed"

cd ..

print_info "Building event-task-enqueuer..."
cd 3-task-queue
gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/streaming-systems-repo/event-task-enqueuer \
  --project=$PROJECT_ID
print_success "event-task-enqueuer image built and pushed"

cd ..
echo ""

# ============================================
# STEP 4: Create Terraform Variables File
# ============================================
print_step "Step 4/6: Preparing Terraform Configuration"

cd 4-terraform

cat > terraform.tfvars <<EOF
# Storage module variables
bq_dataset_id   = "mta_updates"
bq_table_id     = "realtime_updates"
bq_table_schema = "schema.json"

# Project and region
project_id = "$PROJECT_ID"
region     = "$REGION"

# Cloud Run service variables
mta_subway_feed_url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"

mta_processor_endpoint_image = "${REGION}-docker.pkg.dev/${PROJECT_ID}/streaming-systems-repo/mta-processor"
event_task_enqueuer_image    = "${REGION}-docker.pkg.dev/${PROJECT_ID}/streaming-systems-repo/event-task-enqueuer"
EOF

print_success "Terraform variables configured"
echo ""

# ============================================
# STEP 5: Deploy Infrastructure with Terraform
# ============================================
print_step "Step 5/6: Deploying Infrastructure with Terraform"

terraform init
terraform apply -auto-approve

print_success "Infrastructure deployed"
print_info "Waiting 90 seconds for IAM permissions to propagate..."
sleep 90
print_success "IAM propagation complete"
echo ""

cd ..

# ============================================
# STEP 6: Deploy Dataflow Pipeline
# ============================================
print_step "Step 6/6: Deploying Dataflow Pipeline"

cd 1-dataflow

# Update project ID in dataflow script
./replace_project_id.sh $PROJECT_ID

print_info "Launching Dataflow job (this takes 3-5 minutes)..."
python dataflow.py

print_success "Dataflow pipeline deployed"
echo ""

cd ..

# ============================================
# Deployment Complete
# ============================================
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
print_info "Your MTA streaming pipeline is now active!"
echo ""
echo "📊 Monitor your deployment:"
echo "  • Dataflow Dashboard: https://console.cloud.google.com/dataflow/jobs?project=$PROJECT_ID"
echo "  • Cloud Run Services: https://console.cloud.google.com/run?project=$PROJECT_ID"
echo "  • BigQuery Dataset: https://console.cloud.google.com/bigquery?project=$PROJECT_ID"
echo "  • Cloud Scheduler: https://console.cloud.google.com/cloudscheduler?project=$PROJECT_ID"
echo ""
echo "🔍 Check logs:"
echo "  gcloud logging read 'resource.type=cloud_run_revision' --limit=20 --project=$PROJECT_ID"
echo ""
echo "⏱️  Note: It takes 3-5 minutes for Dataflow to fully initialize"
echo "📈 Data should start flowing into BigQuery within 5-10 minutes"
echo ""
