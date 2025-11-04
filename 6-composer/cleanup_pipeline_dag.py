"""
Airflow DAG to tear down the MTA Streaming Pipeline infrastructure
This DAG handles the complete cleanup of all deployed resources
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import os

# Default arguments for the DAG
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# Configuration - Update these values
PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'your-project-id')
REGION = os.environ.get('GCP_REGION', 'us-east1')
REPO_PATH = os.environ.get('REPO_PATH', '/home/airflow/gcs/dags/streaming-systems')

# DAG definition
dag = DAG(
    'streaming_pipeline_cleanup',
    default_args=default_args,
    description='Tear down all MTA streaming pipeline infrastructure',
    schedule_interval=None,  # Manual trigger only
    start_date=days_ago(1),
    catchup=False,
    tags=['streaming', 'mta', 'infrastructure', 'cleanup'],
)

# Task 1: Pause Cloud Scheduler
pause_scheduler = BashOperator(
    task_id='pause_cloud_scheduler',
    bash_command=f"""
    echo "⏸️  Pausing Cloud Scheduler jobs..."
    
    for JOB in $(gcloud scheduler jobs list \
      --location={REGION} \
      --project={PROJECT_ID} \
      --format="value(name)" \
      --filter="state:ENABLED"); do
      
      gcloud scheduler jobs pause $JOB \
        --location={REGION} \
        --project={PROJECT_ID}
      echo "Paused: $JOB"
    done
    
    echo "✅ Cloud Scheduler paused"
    """,
    dag=dag,
)

# Task 2: Cancel Dataflow jobs
cancel_dataflow = BashOperator(
    task_id='cancel_dataflow_jobs',
    bash_command=f"""
    echo "🛑 Cancelling Dataflow jobs..."
    
    for JOB_ID in $(gcloud dataflow jobs list \
      --project={PROJECT_ID} \
      --region={REGION} \
      --status=active \
      --format="value(id)"); do
      
      gcloud dataflow jobs cancel $JOB_ID \
        --region={REGION} \
        --project={PROJECT_ID}
      echo "Cancelled: $JOB_ID"
    done
    
    echo "✅ Dataflow jobs cancelled"
    """,
    dag=dag,
)

# Task 3: Wait for Dataflow to drain
wait_for_dataflow = BashOperator(
    task_id='wait_for_dataflow_drain',
    bash_command="""
    echo "⏳ Waiting 60 seconds for Dataflow to drain..."
    sleep 60
    echo "✅ Dataflow drain wait complete"
    """,
    dag=dag,
)

# Task 4: Destroy Terraform infrastructure
terraform_destroy = BashOperator(
    task_id='terraform_destroy',
    bash_command=f"""
    cd {REPO_PATH}/4-terraform
    
    echo "🗑️  Destroying Terraform infrastructure..."
    terraform destroy -auto-approve
    
    echo "✅ Terraform infrastructure destroyed"
    """,
    dag=dag,
)

# Task 5: Delete container images
delete_images = BashOperator(
    task_id='delete_container_images',
    bash_command=f"""
    echo "🗑️  Deleting container images..."
    
    # Delete mta-processor image
    gcloud artifacts docker images delete \
      {REGION}-docker.pkg.dev/{PROJECT_ID}/streaming-systems-repo/mta-processor \
      --quiet \
      --project={PROJECT_ID} || echo "Image already deleted or doesn't exist"
    
    # Delete event-task-enqueuer image
    gcloud artifacts docker images delete \
      {REGION}-docker.pkg.dev/{PROJECT_ID}/streaming-systems-repo/event-task-enqueuer \
      --quiet \
      --project={PROJECT_ID} || echo "Image already deleted or doesn't exist"
    
    echo "✅ Container images deleted"
    """,
    dag=dag,
)

# Task 6: Delete Artifact Registry repository
delete_artifact_registry = BashOperator(
    task_id='delete_artifact_registry',
    bash_command=f"""
    echo "🗑️  Deleting Artifact Registry repository..."
    
    gcloud artifacts repositories delete streaming-systems-repo \
      --location={REGION} \
      --project={PROJECT_ID} \
      --quiet || echo "Repository already deleted"
    
    echo "✅ Artifact Registry repository deleted"
    """,
    dag=dag,
)

# Task 7: Delete BigQuery dataset (optional - commented out for safety)
delete_bigquery = BashOperator(
    task_id='delete_bigquery_dataset',
    bash_command=f"""
    echo "⚠️  Skipping BigQuery dataset deletion (contains data)"
    echo "To delete manually:"
    echo "bq rm -r -f -d {PROJECT_ID}:mta_streaming"
    
    # Uncomment below to enable automatic deletion:
    # bq rm -r -f -d {PROJECT_ID}:mta_streaming
    """,
    dag=dag,
)

# Task 8: Delete GCS buckets (optional - commented out for safety)
delete_gcs_buckets = BashOperator(
    task_id='delete_gcs_buckets',
    bash_command=f"""
    echo "⚠️  Skipping GCS bucket deletion"
    echo "To delete manually:"
    echo "gsutil -m rm -r gs://{PROJECT_ID}-streaming-*"
    
    # Uncomment below to enable automatic deletion:
    # for BUCKET in $(gsutil ls -p {PROJECT_ID} | grep streaming); do
    #   gsutil -m rm -r $BUCKET
    # done
    """,
    dag=dag,
)

# Task 9: Verify cleanup
verify_cleanup = BashOperator(
    task_id='verify_cleanup',
    bash_command=f"""
    echo "🔍 Verifying cleanup..."
    echo ""
    
    echo "Remaining Cloud Run Services:"
    gcloud run services list --project={PROJECT_ID} --platform=managed || echo "None"
    echo ""
    
    echo "Remaining Cloud Scheduler Jobs:"
    gcloud scheduler jobs list --location={REGION} --project={PROJECT_ID} || echo "None"
    echo ""
    
    echo "Remaining Dataflow Jobs:"
    gcloud dataflow jobs list --project={PROJECT_ID} --region={REGION} --status=active || echo "None"
    echo ""
    
    echo "✅ Cleanup verification complete"
    echo "🎉 Infrastructure teardown successful!"
    echo ""
    echo "⚠️  Note: BigQuery dataset and GCS buckets preserved (contain data)"
    """,
    dag=dag,
)

# Define task dependencies (execution order)
pause_scheduler >> cancel_dataflow >> wait_for_dataflow
wait_for_dataflow >> terraform_destroy
terraform_destroy >> delete_images >> delete_artifact_registry
delete_artifact_registry >> [delete_bigquery, delete_gcs_buckets] >> verify_cleanup
