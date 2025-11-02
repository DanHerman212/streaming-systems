output "mta_processor_endpoint_url" {
  value = google_cloud_run_service.mta_processor_endpoint.status[0].url
}

output "event_task_enqueuer_url" {
  value = google_cloud_run_service.event_task_enqueuer.status[0].url
}
