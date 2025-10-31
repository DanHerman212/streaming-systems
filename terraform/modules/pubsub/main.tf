resource "google_pubsub_topic" "main" {
  name    = var.topic_name
  project = var.project_id
}

resource "google_pubsub_subscription" "main" {
  name  = var.subscription_name
  topic = google_pubsub_topic.main.id
  project = var.project_id
}
