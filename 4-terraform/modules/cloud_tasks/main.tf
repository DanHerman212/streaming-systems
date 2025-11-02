resource "random_id" "queue_suffix" {
  byte_length = 2 # 4 hex digits
}

resource "google_cloud_tasks_queue" "event_feed_queue" {
  name     = "event-feed-queue-${random_id.queue_suffix.hex}"
  project  = var.project_id
  location = var.region
}
