variable "task_queue_name" {
  description = "Cloud Tasks queue name"
  type        = string
}

variable "mta_processor_endpoint_image" {
  description = "Container image for mta-processor-endpoint"
  type        = string
}

variable "event_task_enqueuer_image" {
  description = "Container image for event-task-enqueuer"
  type        = string
}
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "mta_subway_feed_url" {
  description = "NYC Subway Feed URL"
  type        = string
}

variable "pubsub_topic_id" {
  description = "Pub/Sub Topic ID"
  type        = string
}

variable "event_feed_processor_service_url" {
  description = "URL of the mta-processor-endpoint Cloud Run service"
  type        = string
}

variable "tasks_sa_email" {
  description = "Tasks to Processor Service Account Email"
  type        = string
}
