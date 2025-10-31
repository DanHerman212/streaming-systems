# For Cloud Run services
variable "mta_subway_feed_url" {
  description = "NYC Subway Feed URL"
  type        = string
  default     = ""
}

variable "pubsub_topic_id" {
  description = "Pub/Sub Topic ID"
  type        = string
  default     = ""
}

variable "mta_processor_endpoint_image" {
  description = "Container image for mta-processor-endpoint"
  type        = string
  default     = ""
}

variable "event_task_enqueuer_image" {
  description = "Container image for event-task-enqueuer"
  type        = string
  default     = ""
}
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
