output "pubsub_topic_id" {
  value = module.pubsub.topic_id
}

output "pubsub_subscription_id" {
  value = module.pubsub.subscription_id
}
output "enabled_apis" {
  value = module.apis.enabled_apis
}

output "compute_engine_sa_email" {
  value = module.service_accounts.compute_engine_sa_email
}
output "tasks_to_processor_sa_email" {
  value = module.service_accounts.tasks_to_processor_sa_email
}
output "enqueuer_to_tasks_sa_email" {
  value = module.service_accounts.enqueuer_to_tasks_sa_email
}

output "event_feed_queue_name" {
  value = module.cloud_tasks.event_feed_queue_name
}
