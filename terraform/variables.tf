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
    "run.googleapis.com",
    "pubsub.googleapis.com",
    "cloudscheduler.googleapis.com"
  ]
}
