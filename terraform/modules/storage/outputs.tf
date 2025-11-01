output "enrichment_bucket_name" {
  value = google_storage_bucket.enrichment.name
}

output "stops_csv_url" {
  value = google_storage_bucket_object.stops_csv.self_link
}
output "bq_dataset_id" {
  value = google_bigquery_dataset.main.dataset_id
}

output "bq_table_id" {
  value = google_bigquery_table.main.table_id
}

output "staging_bucket_name" {
  value = google_storage_bucket.staging.name
}

output "temp_bucket_name" {
  value = google_storage_bucket.temp.name
}
