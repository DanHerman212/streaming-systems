variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "bq_dataset_id" {
  description = "BigQuery dataset ID"
  type        = string
  default     = "my_dataset"
}

variable "bq_table_id" {
  description = "BigQuery table ID"
  type        = string
  default     = "my_table"
}

variable "bq_table_schema" {
  description = "Path to BigQuery table schema JSON file"
  type        = string
  default     = "schema.json"
}
