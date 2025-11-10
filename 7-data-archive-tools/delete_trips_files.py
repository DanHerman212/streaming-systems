"""
Delete *_trips.csv Files from GCS
Removes all files ending in _trips.csv from decompressed folder subfolders
Keeps the other CSV files (stop_times data)
"""

from google.cloud import storage

# ============================================
# Configuration
# ============================================
PROJECT_ID = "streaming-systems-245"
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

# List all blobs in decompressed folder
print("Scanning for *_trips.csv files...\n")

blobs_to_delete = []
for blob in bucket.list_blobs(prefix=GCS_DECOMPRESSED_PREFIX):
    if blob.name.endswith('_trips.csv'):
        blobs_to_delete.append(blob)

print(f"Found {len(blobs_to_delete)} files to delete\n")

# Confirm before deletion
if blobs_to_delete:
    print("Sample files to be deleted:")
    for blob in blobs_to_delete[:5]:
        print(f"  - {blob.name}")
    if len(blobs_to_delete) > 5:
        print(f"  ... and {len(blobs_to_delete) - 5} more")
    
    print("\n" + "-"*60)
    response = input(f"Delete {len(blobs_to_delete)} files? (yes/no): ")
    
    if response.lower() == 'yes':
        print("\nDeleting files...")
        deleted_count = 0
        for blob in blobs_to_delete:
            try:
                blob.delete()
                deleted_count += 1
                print(f"✓ Deleted: {blob.name}")
            except Exception as e:
                print(f"✗ Error deleting {blob.name}: {e}")
        
        print("\n" + "="*60)
        print(f"Deletion complete: {deleted_count}/{len(blobs_to_delete)} files deleted")
        print("="*60)
    else:
        print("\nDeletion cancelled")
else:
    print("No *_trips.csv files found")
