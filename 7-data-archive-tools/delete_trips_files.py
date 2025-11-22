"""
Delete *_trips.csv Files from GCS
Removes all files ending in _trips.csv from monthly decompressed folders (YYYY-MM/)
Keeps the stop_times CSV files in decompressed folders
"""

from google.cloud import storage

# ============================================
# Configuration
# ============================================
PROJECT_ID = "time-series-478616"
GCS_BUCKET_NAME = f"{PROJECT_ID}-historical-data"
GCS_DECOMPRESSED_PREFIX = "decompressed/"

print("="*60)
print("Deleting *_trips.csv files from GCS")
print("="*60)
print(f"Bucket: {GCS_BUCKET_NAME}")
print(f"Prefix: {GCS_DECOMPRESSED_PREFIX}")
print("="*60 + "\n")

# Initialize GCS client
client = storage.Client(project=PROJECT_ID)
bucket = client.bucket(GCS_BUCKET_NAME)

# ============================================
# Find files to delete
# ============================================
print("Scanning for *_trips.csv files in monthly folders...\n")

trips_files = []

# Find *_trips.csv files in decompressed monthly folders
for blob in bucket.list_blobs(prefix=GCS_DECOMPRESSED_PREFIX):
    if blob.name.endswith('_trips.csv'):
        trips_files.append(blob)

print(f"Found {len(trips_files)} *_trips.csv files\n")

# ============================================
# Confirm before deletion
# ============================================
if len(trips_files) == 0:
    print("No *_trips.csv files found to delete")
else:
    print("Sample files to be deleted:")
    for blob in trips_files[:5]:
        print(f"  - {blob.name}")
    if len(trips_files) > 5:
        print(f"  ... and {len(trips_files) - 5} more")
    
    print("\n" + "-"*60)
    response = input(f"Delete {len(trips_files)} files? (yes/no): ")
    
    if response.lower() == 'yes':
        print("\n" + "="*60)
        print("Deleting files...")
        print("="*60 + "\n")
        
        deleted_count = 0
        error_count = 0
        
        print(f"Deleting {len(trips_files)} *_trips.csv files...")
        for blob in trips_files:
            try:
                blob.delete()
                deleted_count += 1
                if deleted_count % 100 == 0:
                    print(f"  Deleted {deleted_count} files...")
            except Exception as e:
                error_count += 1
                print(f"  ✗ Error deleting {blob.name}: {e}")
        
        print("\n" + "="*60)
        print(f"Deletion complete: {deleted_count}/{len(trips_files)} files deleted")
        if error_count > 0:
            print(f"Errors: {error_count} files failed to delete")
        print("="*60)
    else:
        print("\nDeletion cancelled")
