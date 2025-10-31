project_id = "your-gcp-project-id"
# region     = "us-east1"
# apis = ["run.googleapis.com", "pubsub.googleapis.com", "cloudscheduler.googleapis.com"]
region     = "us-east1"

# Cloud Run service variables
mta_subway_feed_url          = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"
pubsub_topic_id              = module.pubsub.topic_id
pubsub_subscription_id       = module.pubsub.subscription_id
mta_processor_endpoint_image = "gcr.io/your-project/mta-processor"
event_task_enqueuer_image    = "gcr.io/your-project/event-task-enqueuer"