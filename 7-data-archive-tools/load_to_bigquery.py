"""
Load Historical MTA Data to BigQuery
Handles multiple CSV files across subdirectories
"""

from google.cloud import bigquery
from google.cloud import storage
import json

# ============================================
# Configuration
# ============================================
PROJECT_ID = "streaming-systems-245"
DATASET_ID = "mta_historical"
TABLE_ID = "sensor_data"
BUCKET_NAME = f"{PROJECT_ID}-historical-data"
PREFIX = "decompressed/"

print("="*60)
print("Loading Historical Data to BigQuery")
print("="*60)
print(f"Project: {PROJECT_ID}")
print(f"Dataset: {DATASET_ID}")
print(f"Table: {TABLE_ID}")
print("="*60 + "\n")

# Initialize clients
bq_client = bigquery.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)

# Get list of all CSV files
bucket = storage_client.bucket(BUCKET_NAME)
blobs = list(bucket.list_blobs(prefix=PREFIX))
csv_files = [f"gs://{BUCKET_NAME}/{blob.name}" for blob in blobs if blob.name.endswith('.csv')]

print(f"Found {len(csv_files)} CSV files to load\n")

if not csv_files:
    print("No CSV files found!")
    exit(1)

# Show sample files
print("Sample files:")
for uri in csv_files[:5]:
    print(f"  - {uri}")
if len(csv_files) > 5:
    print(f"  ... and {len(csv_files) - 5} more\n")

# Load schema
with open('schema_historical_sensor_data.json', 'r') as f:
    schema_json = json.load(f)
    schema = [
        bigquery.SchemaField(
            name=field['name'],
            field_type=field['type'],
            mode=field['mode'],
            description=field.get('description', '')
        )
        for field in schema_json
    ]

# Configure load job
table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
    schema=schema,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # Change to WRITE_APPEND if adding to existing table
)

print(f"Starting BigQuery load job...")
print(f"Loading {len(csv_files)} files to {table_ref}\n")

# Load all files at once
load_job = bq_client.load_table_from_uri(
    csv_files,
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
