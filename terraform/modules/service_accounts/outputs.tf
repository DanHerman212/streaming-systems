output "compute_engine_sa_email" {
  value = google_service_account.compute_engine_sa.email
}
output "tasks_to_processor_sa_email" {
  value = google_service_account.tasks_to_processor_sa.email
}
output "enqueuer_to_tasks_sa_email" {
  value = google_service_account.enqueuer_to_tasks_sa.email
}
