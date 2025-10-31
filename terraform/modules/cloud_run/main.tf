# Cloud Run Service 1: mta-processor-endpoint
resource "google_cloud_run_service" "mta_processor_endpoint" {
  name     = "mta-processor-endpoint"
  location = var.region
  template {
    spec {
      service_account_name = var.tasks_sa_email
      containers {
        image = var.mta_processor_endpoint_image
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        env {
          name  = "NYC_SUBWAY_FEED_URL"
          value = var.mta_subway_feed_url
        }
        env {
          name  = "PUBSUB_TOPIC_ID"
          value = var.pubsub_topic_id
        }
      }
    }
  }
  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Cloud Run Service 2: event-task-enqueuer
resource "google_cloud_run_service" "event_task_enqueuer" {
  name     = "event-task-enqueuer"
  location = var.region
  template {
    spec {
      service_account_name = var.tasks_sa_email
      containers {
        image = var.event_task_enqueuer_image
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        env {
          name  = "REGION"
          value = var.region
        }
        env {
          name  = "TASK_QUEUE_NAME"
          value = var.task_queue_name
        }
        env {
          name  = "EVENT_FEED_PROCESSOR_SERVICE_URL"
          value = var.event_feed_processor_service_url
        }
        env {
          name  = "TASKS_SA_EMAIL"
          value = var.tasks_sa_email
        }
      }
    }
  }
  traffic {
    percent         = 100
    latest_revision = true
  }
}
