"""
Historical MTA Sensor Data Download Script
Downloads compressed CSV files from subwaydata.nyc for the last 12 months
Decompresses .tar.xz files, extracts CSVs, and uploads to GCS
Automatically cleans up compressed files after successful extraction
"""

import requests
from google.cloud import storage
import concurrent.futures
from datetime import datetime, timedelta
import os
import tarfile
import lzma
import tempfile
import shutil

# ============================================
# Configuration
# ============================================
PROJECT_ID = "<your-project-id>"
GCS_BUCKET_NAME = f"{PROJECT_ID}-historical-data"
GCS_RAW_PREFIX = "raw/"  # Temporary folder for compressed files (will be deleted)
GCS_DECOMPRESSED_PREFIX = "decompressed/"  # Final folder for CSV files
BASE_URL = "https://subwaydata.nyc/data"
MAX_WORKERS = 10  # Number of parallel downloads
DECOMPRESS_WORKERS = 5  # Number of parallel decompression tasks

# Date range: Last 12 months from today (2025-11-07)
END_DATE = datetime(2025, 11, 7)
START_DATE = END_DATE - timedelta(days=365)  # Approximately 12 months

print(f"Downloading data from {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
print(f"Total days to process: {(END_DATE - START_DATE).days + 1}")

# ============================================
# Download and Upload Function
# ============================================
def download_and_upload(date):
    """
    Download MTA sensor data for a specific date and upload to GCS.
    
    Args:
        date: datetime object representing the date to download
    
    Returns:
        Tuple of (date_str, status, message, compressed_gcs_path)
    """
    date_str = date.strftime('%Y-%m-%d')
    file_name = f"subwaydatanyc_{date_str}_csv.tar.xz"
    url = f"{BASE_URL}/{file_name}"
    gcs_compressed_path = f"{GCS_RAW_PREFIX}{file_name}"
    
    try:
        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        # Check if decompressed CSVs already exist (final state)
        decompressed_prefix = f"{GCS_DECOMPRESSED_PREFIX}{date_str}/"
        blobs = list(bucket.list_blobs(prefix=decompressed_prefix, max_results=1))
        if blobs:
            return (date_str, "SKIPPED", "CSVs already decompressed in GCS", None)
        
        # Download file from subwaydata.nyc
        response = requests.get(url, timeout=120, stream=True)
        
        if response.status_code == 200:
            # Upload compressed file to GCS temporarily
            blob = bucket.blob(gcs_compressed_path)
            blob.upload_from_string(response.content, content_type='application/x-xz')
            file_size_mb = len(response.content) / (1024 * 1024)
            return (date_str, "SUCCESS", f"Downloaded {file_size_mb:.2f} MB", gcs_compressed_path)
        elif response.status_code == 404:
            return (date_str, "NOT_FOUND", "No data available for this date", None)
        else:
            return (date_str, "ERROR", f"HTTP {response.status_code}", None)
            
    except Exception as e:
        return (date_str, "ERROR", str(e), None)

# ============================================
# Decompression Function
# ============================================
def decompress_and_upload(compressed_gcs_path):
    """
    Download compressed file from GCS, decompress .tar.xz, extract CSVs,
    upload CSVs back to GCS, and delete the compressed file.
    
    Args:
        compressed_gcs_path: GCS path to the compressed file (e.g., "raw/subwaydatanyc_2024-11-07_csv.tar.xz")
    
    Returns:
        Tuple of (date_str, status, message)
    """
    try:
        # Extract date from filename
        file_name = os.path.basename(compressed_gcs_path)
        date_str = file_name.replace("subwaydatanyc_", "").replace("_csv.tar.xz", "")
        
        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        # Download compressed file to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            local_compressed_path = os.path.join(temp_dir, file_name)
            blob = bucket.blob(compressed_gcs_path)
            blob.download_to_filename(local_compressed_path)
            
            # Decompress .tar.xz file
            # Step 1: Decompress .xz to .tar
            tar_path = local_compressed_path.replace('.tar.xz', '.tar')
            with lzma.open(local_compressed_path, 'rb') as f_in:
                with open(tar_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Step 2: Extract .tar archive
            extract_dir = os.path.join(temp_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            with tarfile.open(tar_path, 'r') as tar:
                tar.extractall(path=extract_dir)
            
            # Step 3: Upload all CSV files to GCS
            csv_count = 0
            total_size = 0
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.endswith('.csv'):
                        local_csv_path = os.path.join(root, file)
                        gcs_csv_path = f"{GCS_DECOMPRESSED_PREFIX}{date_str}/{file}"
                        
                        csv_blob = bucket.blob(gcs_csv_path)
                        csv_blob.upload_from_filename(local_csv_path)
                        
                        csv_count += 1
                        total_size += os.path.getsize(local_csv_path)
            
            # Step 4: Delete the compressed file from GCS
            blob.delete()
            
            total_size_mb = total_size / (1024 * 1024)
            return (date_str, "DECOMPRESSED", f"Extracted {csv_count} CSVs ({total_size_mb:.2f} MB), deleted compressed file")
            
    except Exception as e:
        return (date_str, "DECOMPRESS_ERROR", str(e))

# ============================================
# Main Execution
# ============================================
def main():
    """
    Main function to orchestrate the download process.
    """
    print("\n" + "="*60)
    print("Starting Historical Data Download")
    print("="*60 + "\n")
    
    # Ensure GCS bucket exists
    try:
        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(GCS_BUCKET_NAME)
        if not bucket.exists():
            print(f"Creating GCS bucket: {GCS_BUCKET_NAME}")
            bucket.create(location="US")
        else:
            print(f"Using existing GCS bucket: {GCS_BUCKET_NAME}")
    except Exception as e:
        print(f"Error accessing GCS bucket: {e}")
        return
    
    # Generate list of dates to download
    dates = [START_DATE + timedelta(days=x) for x in range((END_DATE - START_DATE).days + 1)]
    
    print(f"\nProcessing {len(dates)} dates with {MAX_WORKERS} parallel workers...\n")
    
    # Track results
    results = {
        "SUCCESS": 0,
        "SKIPPED": 0,
        "NOT_FOUND": 0,
        "ERROR": 0,
        "DECOMPRESSED": 0,
        "DECOMPRESS_ERROR": 0
    }
    
    # Step 1: Download files in parallel
    print("STEP 1: Downloading compressed files...")
    print("-" * 60 + "\n")
    
    compressed_files = []  # Track files that need decompression
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_date = {executor.submit(download_and_upload, date): date for date in dates}
        
        for future in concurrent.futures.as_completed(future_to_date):
            date_str, status, message, compressed_path = future.result()
            results[status] += 1
            
            # Track files that need decompression
            if status == "SUCCESS" and compressed_path:
                compressed_files.append(compressed_path)
            
            # Print status with symbols
            status_symbols = {
                "SUCCESS": "⬇",
                "SKIPPED": "⊘",
                "NOT_FOUND": "✗",
                "ERROR": "✗"
            }
            symbol = status_symbols.get(status, "?")
            print(f"{symbol} {date_str}: {status} - {message}")
    
    # Step 2: Decompress files in parallel
    if compressed_files:
        print("\n" + "="*60)
        print(f"STEP 2: Decompressing {len(compressed_files)} files...")
        print("-" * 60 + "\n")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=DECOMPRESS_WORKERS) as executor:
            future_to_path = {executor.submit(decompress_and_upload, path): path for path in compressed_files}
            
            for future in concurrent.futures.as_completed(future_to_path):
                date_str, status, message = future.result()
                results[status] += 1
                
                status_symbols = {
                    "DECOMPRESSED": "✓",
                    "DECOMPRESS_ERROR": "✗"
                }
                symbol = status_symbols.get(status, "?")
                print(f"{symbol} {date_str}: {status} - {message}")
    
    # Print final summary
    print("\n" + "="*60)
    print("Final Summary")
    print("="*60)
    print(f"⬇ Downloaded (compressed): {results['SUCCESS']}")
    print(f"✓ Decompressed & uploaded: {results['DECOMPRESSED']}")
    print(f"⊘ Skipped (already processed): {results['SKIPPED']}")
    print(f"✗ Not found (404): {results['NOT_FOUND']}")
    print(f"✗ Download errors: {results['ERROR']}")
    print(f"✗ Decompression errors: {results['DECOMPRESS_ERROR']}")
    print(f"\nTotal CSV files ready in GCS: {results['DECOMPRESSED'] + results['SKIPPED']}")
    print("\n" + "="*60)
    print(f"CSV files location: gs://{GCS_BUCKET_NAME}/{GCS_DECOMPRESSED_PREFIX}")
    print("Compressed files: DELETED (cleanup complete)")
    print("="*60 + "\n")
    
    print("Next step - Load to BigQuery:")
    print(f"  bq load --source_format=CSV --skip_leading_rows=1 \\")
    print(f"    {PROJECT_ID}:mta_historical.sensor_data \\")
    print(f"    'gs://{GCS_BUCKET_NAME}/{GCS_DECOMPRESSED_PREFIX}*/*.csv'")

if __name__ == "__main__":
    main()
