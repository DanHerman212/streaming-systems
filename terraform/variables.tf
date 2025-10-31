variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "apis" {
  description = "List of APIs to enable"
  type        = list(string)
  default     = [
    "bigquery.googleapis.com",           # BigQuery API
    "dataflow.googleapis.com",           # Dataflow API
    "monitoring.googleapis.com",         # Cloud Monitoring API
    "pubsub.googleapis.com",             # Cloud Pub/Sub API
    "logging.googleapis.com",            # Cloud Logging API
    "cloudtasks.googleapis.com",         # Cloud Tasks API
    "compute.googleapis.com",            # Compute Engine API
    "aiplatform.googleapis.com",         # Gemini for Google Cloud API (uses AI Platform)
    "run.googleapis.com",                # Cloud Run Admin API
    "cloudscheduler.googleapis.com",     # Cloud Scheduler API
    "cloudbuild.googleapis.com",         # Cloud Build API
    "dataplex.googleapis.com"            # Cloud Dataplex API
  ]
}
