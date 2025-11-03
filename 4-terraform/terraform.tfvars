# Storage module variables
bq_dataset_id   = "streaming-systems"
bq_table_id     = "realtime-updates"
bq_table_schema = "schema.json"
project_id = "your-gcp-project-id"
region     = "us-east1"

# Cloud Run service variables
mta_subway_feed_url          = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"
mta_processor_endpoint_image = "gcr.io/your-project/mta-processor"
event_task_enqueuer_image    = "gcr.io/your-project/event-task-enqueuer"