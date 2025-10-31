output "topic_id" {
  value = google_pubsub_topic.main.id
}

output "subscription_id" {
  value = google_pubsub_subscription.main.id
}
