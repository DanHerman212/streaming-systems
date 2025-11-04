# Data source to get project number for service agent permissions
data "google_project" "project" {
  project_id = var.project_id
}

# Service Account: compute-engine-sa
resource "google_service_account" "compute_engine_sa" {
  account_id   = "compute-engine-sa"
  display_name = "Compute Engine Service Account"
}
resource "google_project_iam_member" "compute_engine_sa_roles" {
  for_each = toset([
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/editor"
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.compute_engine_sa.email}"
}

# Service Account: tasks-to-processor-sa
resource "google_service_account" "tasks_to_processor_sa" {
  account_id   = "tasks-to-processor-sa"
  display_name = "Tasks to Processor Service Account"
}
resource "google_project_iam_member" "tasks_to_processor_sa_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/cloudtasks.admin",
    "roles/run.invoker",
    "roles/pubsub.publisher"  # ADDED: Permission to publish to Pub/Sub
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.tasks_to_processor_sa.email}"
}
# Allow tasks-to-processor-sa to act as itself (needed for Cloud Run to use this SA to enqueue tasks)
resource "google_service_account_iam_member" "tasks_to_processor_sa_act_as" {
  service_account_id = google_service_account.tasks_to_processor_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.tasks_to_processor_sa.email}"
}

# Allow Cloud Tasks service agent to use tasks-to-processor-sa for OIDC token generation
resource "google_service_account_iam_member" "cloudtasks_sa_can_act_as_tasks_sa" {
  service_account_id = google_service_account.tasks_to_processor_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-cloudtasks.iam.gserviceaccount.com"
}

# Service Account: enqueuer-to-tasks-sa
resource "google_service_account" "enqueuer_to_tasks_sa" {
  account_id   = "enqueuer-to-tasks-sa"
  display_name = "Enqueuer to Tasks Service Account"
}
resource "google_project_iam_member" "enqueuer_to_tasks_sa_roles" {
  for_each = toset([
    "roles/run.invoker",
    "roles/cloudtasks.enqueuer",
    "roles/pubsub.publisher",
    "roles/iam.serviceAccountUser"
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.enqueuer_to_tasks_sa.email}"
}

# Service Account: scheduler-to-enqueuer-sa
resource "google_service_account" "scheduler_to_enqueuer_sa" {
  account_id   = "scheduler-to-enqueuer-sa"
  display_name = "Scheduler to Enqueuer Service Account"
}
resource "google_project_iam_member" "scheduler_to_enqueuer_sa_roles" {
  for_each = toset([
    "roles/run.invoker"
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.scheduler_to_enqueuer_sa.email}"
}
