"""
Load MTA Stops Reference Data to BigQuery
"""

from google.cloud import bigquery

# ============================================
# Configuration
# ============================================
PROJECT_ID = "streaming-systems-245"
DATASET_ID = "mta_historical"
TABLE_ID = "stops"
CSV_PATH = "4-terraform/modules/storage/stops.csv"

print("="*60)
print("Loading Stops Reference Data to BigQuery")
print("="*60)
print(f"Project: {PROJECT_ID}")
print(f"Dataset: {DATASET_ID}")
print(f"Table: {TABLE_ID}")
print(f"Source: {CSV_PATH}")
print("="*60 + "\n")

# Initialize client
bq_client = bigquery.Client(project=PROJECT_ID)

# Define schema based on CSV structure
schema = [
    bigquery.SchemaField("stop_id", "STRING", mode="REQUIRED", description="Unique identifier for the stop"),
    bigquery.SchemaField("stop_name", "STRING", mode="NULLABLE", description="Name of the subway stop"),
    bigquery.SchemaField("stop_lat", "FLOAT", mode="NULLABLE", description="Latitude coordinate of the stop"),
    bigquery.SchemaField("stop_lon", "FLOAT", mode="NULLABLE", description="Longitude coordinate of the stop"),
    bigquery.SchemaField("location_type", "INTEGER", mode="NULLABLE", description="Type of location (1=station, blank=platform)"),
    bigquery.SchemaField("parent_station", "STRING", mode="NULLABLE", description="Parent station ID if this is a platform"),
]

# Configure load job
table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
    schema=schema,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    allow_quoted_newlines=True,
)

print(f"Starting BigQuery load job...")

# Load from local file
with open(CSV_PATH, "rb") as source_file:
    load_job = bq_client.load_table_from_file(
        source_file,
        table_ref,
        job_config=job_config
    )

# Wait for job to complete
load_job.result()

print("="*60)
print("✓ Load complete!")
print("="*60)
print(f"Loaded {load_job.output_rows} rows")
print(f"Table: {table_ref}")
print("="*60)
