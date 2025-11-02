output "scheduler_job_name" {
  value = google_cloud_scheduler_job.trigger_event_task_enqueuer.name
}
