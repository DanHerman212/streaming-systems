resource "google_bigquery_dataset" "main" {
  dataset_id = var.bq_dataset_id
  project    = var.project_id
  location   = var.region
}

resource "google_bigquery_table" "main" {
  dataset_id = google_bigquery_dataset.main.dataset_id
  table_id   = var.bq_table_id
  project    = var.project_id
  schema     = file(var.bq_table_schema)
}

resource "google_storage_bucket" "staging" {
  name          = "${var.project_id}-dataflow-staging"
  location      = var.region
  force_destroy = true
}

resource "google_storage_bucket" "temp" {
  name          = "${var.project_id}-dataflow-temp"
  location      = var.region
  force_destroy = true
}

# Enrichment bucket
resource "google_storage_bucket" "enrichment" {
  name          = "${var.project_id}-enrichment"
  location      = var.region
  force_destroy = true
}

# Upload stops.csv to enrichment bucket
resource "google_storage_bucket_object" "stops_csv" {
  name   = "stops.csv"
  bucket = google_storage_bucket.enrichment.name
  source = "${path.module}/../../../stops.csv"
}
