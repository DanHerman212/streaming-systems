resource "google_cloud_scheduler_job" "trigger_event_task_enqueuer" {
  name        = "trigger-event-task-enqueuer"
  project     = var.project_id
  region      = var.region
  schedule    = "* * * * *" # every minute
  time_zone   = "Etc/UTC"
  http_target {
    http_method = "POST"
    uri         = var.service_url
    oidc_token {
      service_account_email = var.service_account_email
    }
  }
}
