# Cloud Composer Deployment Guide

This folder contains an Airflow DAG that automates the entire deployment process for the MTA streaming pipeline.

## What This DAG Does

The DAG automates all 6 manual steps into a single workflow:

1. ✅ **Enable GCP APIs** - Enables all required APIs
2. ✅ **Create Artifact Registry** - Creates Docker repository
3. ✅ **Build & Push Images** - Containerizes applications
4. ✅ **Prepare Terraform** - Configures variables
5. ✅ **Deploy Infrastructure** - Runs terraform apply
6. ✅ **Wait for IAM** - 5-minute wait for propagation
7. ✅ **Update Dataflow** - Prepares Dataflow script
8. ✅ **Deploy Dataflow** - Launches stream processing
9. ✅ **Wait for Dataflow** - 3-minute initialization
10. ✅ **Enable Scheduler** - Activates the pipeline
11. ✅ **Verify Deployment** - Confirms everything works

## Prerequisites

- Google Cloud Project with billing enabled
- Owner or Editor permissions on the project
- `gcloud` CLI configured

## Option 1: Quick Setup (Recommended)

### Step 1: Set Environment Variables
```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-east1"  # or your preferred region
```

### Step 2: Create Cloud Composer Environment
```bash
gcloud composer environments create mta-streaming-composer \
  --location=$GCP_REGION \
  --python-version=3.11 \
  --machine-type=n1-standard-2 \
  --disk-size=30GB \
  --project=$GCP_PROJECT_ID

# This takes 20-30 minutes to provision
```

### Step 3: Upload Repository to Composer's GCS Bucket
```bash
# Get the DAGs bucket name
export DAGS_BUCKET=$(gcloud composer environments describe mta-streaming-composer \
  --location=$GCP_REGION \
  --project=$GCP_PROJECT_ID \
  --format="get(config.dagGcsPrefix)")

# Upload the entire repo to the dags/ folder
cd streaming-systems
gsutil -m rsync -r -x ".*\.git.*|.*\.terraform.*|.*__pycache__.*" \
  . ${DAGS_BUCKET}/streaming-systems/

# Upload the DAG file
gsutil cp 6-composer/streaming_pipeline_dag.py ${DAGS_BUCKET}/
```

### Step 4: Set Airflow Variables
```bash
gcloud composer environments run mta-streaming-composer \
  --location=$GCP_REGION \
  --project=$GCP_PROJECT_ID \
  variables set -- \
  GCP_PROJECT_ID $GCP_PROJECT_ID

gcloud composer environments run mta-streaming-composer \
  --location=$GCP_REGION \
  --project=$GCP_PROJECT_ID \
  variables set -- \
  GCP_REGION $GCP_REGION

gcloud composer environments run mta-streaming-composer \
  --location=$GCP_REGION \
  --project=$GCP_PROJECT_ID \
  variables set -- \
  REPO_PATH /home/airflow/gcs/dags/streaming-systems
```

### Step 5: Trigger the DAG
1. Go to Airflow UI:
   ```bash
   gcloud composer environments describe mta-streaming-composer \
     --location=$GCP_REGION \
     --project=$GCP_PROJECT_ID \
     --format="get(config.airflowUri)"
   ```
2. Open the URL in your browser
3. Find `streaming_pipeline_deployment` DAG
4. Toggle it ON
5. Click the "Play" button to trigger manually

## Option 2: Manual Composer Setup via Console

1. **Create Composer Environment:**
   - Go to Cloud Composer in GCP Console
   - Click "Create Environment"
   - Choose Composer 2
   - Name: `mta-streaming-composer`
   - Location: Your preferred region
   - Machine type: `n1-standard-2`
   - Wait 20-30 minutes for provisioning

2. **Upload Files:**
   - In Composer environment, click "Open DAGs folder"
   - Create folder `streaming-systems` in the bucket
   - Upload entire repo contents to that folder
   - Upload `streaming_pipeline_dag.py` to root of DAGs folder

3. **Set Variables:**
   - In Airflow UI, go to Admin > Variables
   - Add: `GCP_PROJECT_ID` = your project ID
   - Add: `GCP_REGION` = your region
   - Add: `REPO_PATH` = `/home/airflow/gcs/dags/streaming-systems`

4. **Run DAG:**
   - Enable the DAG toggle
   - Click trigger button

## Monitoring

- **Airflow UI**: Monitor each task's status
- **Task Logs**: Click on individual tasks to see detailed logs
- **GCP Console**: 
  - Cloud Run: See service deployments
  - Dataflow: Monitor pipeline execution
  - Cloud Scheduler: Verify job is running

## Cleanup DAG (Optional)

You can create a separate DAG to tear down all resources:

```bash
# Coming soon: cleanup_pipeline_dag.py
```

## Troubleshooting

### DAG Not Appearing
- Wait 3-5 minutes after uploading (Composer syncs periodically)
- Check DAG file for syntax errors in Airflow UI

### Task Failures
- Click on failed task to see logs
- Common issues:
  - **API not enabled**: Re-run from start
  - **IAM permissions**: Ensure Composer service account has Owner/Editor role
  - **Terraform state**: Delete state files and re-run

### Terraform State Lock
If Terraform gets locked:
```bash
# SSH into Composer worker or use Cloud Shell
cd /home/airflow/gcs/dags/streaming-systems/4-terraform
terraform force-unlock <LOCK_ID>
```

## Cost Considerations

**Cloud Composer Environment**: ~$300-400/month (always running)

**Alternatives if cost is a concern:**
1. **Cloud Build**: Use Cloud Build triggers instead (pay per build)
2. **Cloud Run Jobs**: Run deployment as a one-time job
3. **Local Execution**: Keep the manual 6-step process

Cloud Composer is best if you need:
- Regular deployments (dev/staging/prod)
- Scheduled infrastructure updates
- Complex orchestration
- Audit trails and monitoring

## Next Steps

After successful deployment:
1. ✅ Check BigQuery for incoming data
2. ✅ Monitor Dataflow dashboard
3. ✅ Verify Cloud Scheduler is running
4. ✅ Review costs in Billing console

## Additional Resources

- [Cloud Composer Docs](https://cloud.google.com/composer/docs)
- [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [Original Manual Deployment](../readme.md)
