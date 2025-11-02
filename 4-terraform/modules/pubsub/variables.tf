variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "topic_name" {
  description = "Pub/Sub topic name"
  type        = string
  default     = "mta-gtfs-ace"
}

variable "subscription_name" {
  description = "Pub/Sub subscription name"
  type        = string
  default     = "mta-gtfs-ace-sub"
}
