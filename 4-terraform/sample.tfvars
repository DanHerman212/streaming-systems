# Storage module variables
bq_dataset_id   = "mta_updates"
bq_table_id     = "realtime_updates"
bq_table_schema = "schema.json"
project_id = "your-project-id"
region     = "us-east1" # Update your region if required

# Cloud Run service variables
mta_subway_feed_url          = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"
mta_processor_endpoint_image = "gcr.io/your-project-id/mta-processor"
event_task_enqueuer_image    = "gcr.io/your-project-id/event-task-enqueuer"