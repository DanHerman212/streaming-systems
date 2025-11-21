#!/usr/bin/env python3
"""
Load Historical MTA Data to BigQuery - Month by Month
Uses new year-month folder structure in GCS
Provides detailed progress and error reporting per month
"""

from google.cloud import bigquery
from google.cloud import storage
import json
from datetime import datetime

# ============================================
# Configuration
# ============================================
PROJECT_ID = "time-series-478616"
DATASET_ID = "mta_historical"
TABLE_ID = "sensor_data"
BUCKET_NAME = f"{PROJECT_ID}-historical-data"
PREFIX = "decompressed/"

# Date range to load
START_YEAR = 2021
START_MONTH = 4
END_YEAR = 2025
END_MONTH = 11

print("="*70)
print("Loading Historical Data to BigQuery - Month by Month")
print("="*70)
print(f"Project: {PROJECT_ID}")
print(f"Dataset: {DATASET_ID}")
print(f"Table: {TABLE_ID}")
print(f"Bucket: gs://{BUCKET_NAME}/{PREFIX}")
print(f"Date Range: {START_YEAR}-{START_MONTH:02d} to {END_YEAR}-{END_MONTH:02d}")
print("="*70 + "\n")

# Initialize clients
bq_client = bigquery.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)

# Load schema
schema_file = 'schema_historical_sensor_data.json'
print(f"Loading schema from {schema_file}...")

with open(schema_file, 'r') as f:
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

print(f"Schema loaded: {len(schema)} fields\n")

# Generate list of year-months to process
months_to_process = []
for year in range(START_YEAR, END_YEAR + 1):
    start_m = START_MONTH if year == START_YEAR else 1
    end_m = END_MONTH if year == END_YEAR else 12
    
    for month in range(start_m, end_m + 1):
        months_to_process.append(f"{year}-{month:02d}")

print(f"Processing {len(months_to_process)} months\n")
print("="*70)

# Track results
results = {
    "success": [],
    "failed": [],
    "empty": [],
    "total_rows": 0
}

# Configure load job (common for all months)
table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# Process each month
for idx, year_month in enumerate(months_to_process, 1):
    print(f"\n[{idx}/{len(months_to_process)}] Processing {year_month}...")
    print("-" * 70)
    
    # Check if files exist for this month
    bucket = storage_client.bucket(BUCKET_NAME)
    month_prefix = f"{PREFIX}{year_month}/"
    blobs = list(bucket.list_blobs(prefix=month_prefix))
    csv_blobs = [blob for blob in blobs if blob.name.endswith('.csv')]
    
    if not csv_blobs:
        print(f"⚠ No CSV files found for {year_month}")
        results["empty"].append(year_month)
        continue
    
    print(f"  Found {len(csv_blobs)} CSV files")
    
    # Build GCS URI pattern for this month
    csv_pattern = f"gs://{BUCKET_NAME}/{month_prefix}*.csv"
    
    try:
        # Configure job for this month
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            schema=schema,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,  # Append to existing table
            allow_jagged_rows=True,
            max_bad_records=1000,
            ignore_unknown_values=True
        )
        
        # Load data
        print(f"  Loading: {csv_pattern}")
        load_job = bq_client.load_table_from_uri(
            csv_pattern,
            table_ref,
            job_config=job_config
        )
        
        # Wait for completion
        load_job.result()
        
        # Get stats
        rows_loaded = load_job.output_rows or 0
        results["total_rows"] += rows_loaded
        results["success"].append(year_month)
        
        print(f"  ✓ Success: {rows_loaded:,} rows loaded")
        
        if load_job.errors:
            print(f"  ⚠ Warnings: {len(load_job.errors)} errors encountered (but job succeeded)")
        
    except Exception as e:
        print(f"  ✗ Failed: {str(e)}")
        results["failed"].append(year_month)

# Final Summary
print("\n" + "="*70)
print("FINAL SUMMARY")
print("="*70)
print(f"✓ Successful months: {len(results['success'])}")
print(f"✗ Failed months: {len(results['failed'])}")
print(f"⚠ Empty months: {len(results['empty'])}")
print(f"\nTotal rows loaded: {results['total_rows']:,}")

if results["success"]:
    print(f"\nSuccessful: {', '.join(results['success'])}")

if results["failed"]:
    print(f"\nFailed: {', '.join(results['failed'])}")
    print("  → Retry these months individually to see detailed errors")

if results["empty"]:
    print(f"\nEmpty (no files): {', '.join(results['empty'])}")
    print("  → Run download script to fetch these months")

print("\n" + "="*70)
print(f"Table: {table_ref}")
print(f"Location: https://console.cloud.google.com/bigquery?project={PROJECT_ID}&p={PROJECT_ID}&d={DATASET_ID}&t={TABLE_ID}&page=table")
print("="*70)

# Query to verify data by month
print("\nVerify data loaded with this query:")
print(f"""
SELECT 
  EXTRACT(YEAR FROM arrival_time) as year,
  EXTRACT(MONTH FROM arrival_time) as month,
  COUNT(*) as records
FROM `{table_ref}`
GROUP BY year, month
ORDER BY year, month
""")
