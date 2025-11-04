"""
Airflow DAG to automate the deployment of the MTA Streaming Pipeline
This DAG handles the complete infrastructure setup from API enablement to Dataflow deployment
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import os

# Default arguments for the DAG
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Configuration - Update these values
PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'your-project-id')
REGION = os.environ.get('GCP_REGION', 'us-east1')
REPO_PATH = os.environ.get('REPO_PATH', '/home/airflow/gcs/dags/streaming-systems')

# DAG definition
dag = DAG(
    'streaming_pipeline_deployment',
    default_args=default_args,
    description='Automate MTA streaming pipeline deployment on GCP',
    schedule_interval=None,  # Manual trigger only
    start_date=days_ago(1),
    catchup=False,
    tags=['streaming', 'mta', 'infrastructure', 'deployment'],
)

# Task 1: Enable required GCP APIs
enable_apis = BashOperator(
    task_id='enable_gcp_apis',
    bash_command=f"""
    gcloud services enable cloudresourcemanager.googleapis.com \
      cloudtasks.googleapis.com \
      pubsub.googleapis.com \
      iam.googleapis.com \
      artifactregistry.googleapis.com \
      run.googleapis.com \
      cloudscheduler.googleapis.com \
      dataflow.googleapis.com \
      bigquery.googleapis.com \
      storage-component.googleapis.com \
      --project={PROJECT_ID}
    
    echo "✅ APIs enabled successfully"
    """,
    dag=dag,
)

# Task 2: Create Artifact Registry repository
create_artifact_registry = BashOperator(
    task_id='create_artifact_registry',
    bash_command=f"""
    # Check if repository already exists
    if gcloud artifacts repositories describe streaming-systems-repo \
      --location={REGION} \
      --project={PROJECT_ID} 2>/dev/null; then
      echo "Repository already exists, skipping creation"
    else
      gcloud artifacts repositories create streaming-systems-repo \
        --repository-format=docker \
        --location={REGION} \
        --project={PROJECT_ID}
      echo "✅ Artifact Registry repository created"
    fi
    """,
    dag=dag,
)

# Task 3: Build and push container images
build_and_push_images = BashOperator(
    task_id='build_and_push_images',
    bash_command=f"""
    cd {REPO_PATH}
    
    # Update build_images.sh with project variables
    sed -i 's/YOUR_REGION/{REGION}/g' build_images.sh
    sed -i 's/YOUR_PROJECT_ID/{PROJECT_ID}/g' build_images.sh
    
    # Make script executable and run it
    chmod +x build_images.sh
    ./build_images.sh
    
    echo "✅ Container images built and pushed"
    """,
    dag=dag,
)

# Task 4: Prepare Terraform variables
prepare_terraform_vars = BashOperator(
    task_id='prepare_terraform_vars',
    bash_command=f"""
    cd {REPO_PATH}/4-terraform
    
    # Create terraform.tfvars from sample or create new one
    cat > terraform.tfvars <<EOF
project_id = "{PROJECT_ID}"
region = "{REGION}"
mta_processor_endpoint_image = "{REGION}-docker.pkg.dev/{PROJECT_ID}/streaming-systems-repo/mta-processor"
event_task_enqueuer_image = "{REGION}-docker.pkg.dev/{PROJECT_ID}/streaming-systems-repo/event-task-enqueuer"
EOF
    
    echo "✅ Terraform variables prepared"
    cat terraform.tfvars
    """,
    dag=dag,
)

# Task 5: Initialize Terraform
terraform_init = BashOperator(
    task_id='terraform_init',
    bash_command=f"""
    cd {REPO_PATH}/4-terraform
    terraform init
    echo "✅ Terraform initialized"
    """,
    dag=dag,
)

# Task 6: Apply Terraform (deploy infrastructure)
terraform_apply = BashOperator(
    task_id='terraform_apply',
    bash_command=f"""
    cd {REPO_PATH}/4-terraform
    terraform apply -auto-approve
    echo "✅ Infrastructure deployed"
    """,
    dag=dag,
)

# Task 7: Wait for IAM propagation (5 minutes)
wait_for_iam = BashOperator(
    task_id='wait_for_iam_propagation',
    bash_command="""
    echo "⏳ Waiting 5 minutes for IAM bindings to propagate..."
    sleep 300
    echo "✅ IAM propagation wait complete"
    """,
    dag=dag,
)

# Task 8: Update Dataflow script with project ID
update_dataflow_script = BashOperator(
    task_id='update_dataflow_script',
    bash_command=f"""
    cd {REPO_PATH}/1-dataflow
    
    # Make script executable and run it
    chmod +x replace_project_id.sh
    ./replace_project_id.sh {PROJECT_ID}
    
    echo "✅ Dataflow script updated with project ID"
    """,
    dag=dag,
)

# Task 9: Deploy Dataflow job
deploy_dataflow = BashOperator(
    task_id='deploy_dataflow_job',
    bash_command=f"""
    cd {REPO_PATH}/1-dataflow
    python dataflow.py
    echo "✅ Dataflow job deployed"
    """,
    dag=dag,
)

# Task 10: Wait for Dataflow to initialize (3 minutes)
wait_for_dataflow = BashOperator(
    task_id='wait_for_dataflow_init',
    bash_command="""
    echo "⏳ Waiting 3 minutes for Dataflow to initialize..."
    sleep 180
    echo "✅ Dataflow initialization wait complete"
    """,
    dag=dag,
)

# Task 11: Enable Cloud Scheduler to start the pipeline
enable_scheduler = BashOperator(
    task_id='enable_cloud_scheduler',
    bash_command=f"""
    # Get the scheduler job name from Terraform output or use default naming
    SCHEDULER_JOB=$(gcloud scheduler jobs list \
      --location={REGION} \
      --project={PROJECT_ID} \
      --format="value(name)" \
      --filter="state:PAUSED" | head -n 1)
    
    if [ -n "$SCHEDULER_JOB" ]; then
      gcloud scheduler jobs resume $SCHEDULER_JOB \
        --location={REGION} \
        --project={PROJECT_ID}
      echo "✅ Cloud Scheduler enabled and pipeline activated"
    else
      echo "⚠️ No paused scheduler jobs found. Pipeline may already be active."
    fi
    """,
    dag=dag,
)

# Task 12: Verify deployment
verify_deployment = BashOperator(
    task_id='verify_deployment',
    bash_command=f"""
    echo "🔍 Verifying deployment..."
    echo ""
    echo "Cloud Run Services:"
    gcloud run services list --project={PROJECT_ID} --platform=managed
    echo ""
    echo "Cloud Scheduler Jobs:"
    gcloud scheduler jobs list --location={REGION} --project={PROJECT_ID}
    echo ""
    echo "Dataflow Jobs:"
    gcloud dataflow jobs list --project={PROJECT_ID} --region={REGION} --status=active
    echo ""
    echo "Pub/Sub Topics:"
    gcloud pubsub topics list --project={PROJECT_ID}
    echo ""
    echo "✅ Deployment verification complete"
    echo "🎉 Streaming pipeline is now active!"
    """,
    dag=dag,
)

# Define task dependencies (execution order)
enable_apis >> create_artifact_registry >> build_and_push_images
build_and_push_images >> prepare_terraform_vars >> terraform_init >> terraform_apply
terraform_apply >> wait_for_iam >> update_dataflow_script >> deploy_dataflow
deploy_dataflow >> wait_for_dataflow >> enable_scheduler >> verify_deployment
