module "pubsub" {
  source            = "./modules/pubsub"
  project_id        = var.project_id
  topic_name        = "mta-gtfs-ace"
  subscription_name = "mta-gtfs-ace-sub"
}
module "cloud_run" {
  source      = "./modules/cloud_run"
  project_id  = var.project_id
  region      = var.region
  mta_subway_feed_url = var.mta_subway_feed_url
  pubsub_topic_id     = var.pubsub_topic_id
  event_feed_processor_service_url = module.cloud_run.mta_processor_endpoint_url
  tasks_sa_email      = module.service_accounts.tasks_to_processor_sa_email
  mta_processor_endpoint_image = var.mta_processor_endpoint_image
  event_task_enqueuer_image    = var.event_task_enqueuer_image
  task_queue_name              = module.cloud_tasks.event_feed_queue_name
}
terraform {
  required_version = ">= 1.0.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "apis" {
  source     = "./modules/apis"
  project_id = var.project_id
  apis       = var.apis
}

module "service_accounts" {
  source     = "./modules/service_accounts"
  project_id = var.project_id
}

module "cloud_tasks" {
  source     = "./modules/cloud_tasks"
  project_id = var.project_id
  region     = var.region
}
