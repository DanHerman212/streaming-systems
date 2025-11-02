variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "service_url" {
  description = "Cloud Run service URL to trigger"
  type        = string
}

variable "service_account_email" {
  description = "Service account email for OIDC auth"
  type        = string
}
