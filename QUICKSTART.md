# 🚀 Quick Start Guide

## For Absolute Beginners

This guide will get your MTA streaming pipeline running in **one command**.

### What You Need
- A Google Cloud Project ([Create one here](https://console.cloud.google.com/))
- Billing enabled on your project
- 15-20 minutes

### Step-by-Step

#### 1. Open Google Cloud Shell
Click this button: [**Open Cloud Shell**](https://shell.cloud.google.com/)

Or go to [Google Cloud Console](https://console.cloud.google.com/) and click the terminal icon in the top right.

#### 2. Clone the Repository
Copy and paste this into Cloud Shell:
```bash
git clone https://github.com/DanHerman212/streaming-systems.git
cd streaming-systems
```

#### 3. Run the Deployment
Replace `YOUR_PROJECT_ID` with your actual GCP project ID:
```bash
chmod +x deploy.sh
./deploy.sh YOUR_PROJECT_ID us-east1
```

**Example:**
```bash
./deploy.sh my-streaming-project us-east1
```

#### 4. Wait
The script will:
- ✅ Enable APIs (~2 min)
- ✅ Build containers (~5 min)
- ✅ Deploy infrastructure (~3 min)
- ✅ Launch Dataflow (~5 min)
- ✅ Activate pipeline

**Total time: 15-20 minutes** ☕

### What Happens Next?

After deployment:
1. **Wait 5 minutes** for Dataflow to initialize
2. **Check BigQuery** for incoming data:
   - Go to [BigQuery Console](https://console.cloud.google.com/bigquery)
   - Look for `mta_streaming` dataset
   - Query the table to see real-time subway data!

### Monitoring Your Pipeline

**Dataflow Dashboard:**
```bash
# Check Dataflow job status
gcloud dataflow jobs list --region=us-east1 --status=active
```

**Cloud Run Logs:**
```bash
# View application logs
gcloud logging read 'resource.type=cloud_run_revision' --limit=20
```

**BigQuery Data:**
```sql
-- Run this in BigQuery Console
SELECT * FROM `your-project-id.mta_streaming.mta_data`
ORDER BY event_timestamp_unix DESC
LIMIT 100
```

### Troubleshooting

**Script fails with "Permission Denied":**
```bash
# Make sure you have Owner/Editor role
gcloud projects get-iam-policy YOUR_PROJECT_ID --flatten="bindings[].members" --filter="bindings.members:user:YOUR_EMAIL"
```

**Need to re-run deployment:**
```bash
# Clean up first
cd 4-terraform
terraform destroy -auto-approve
cd ..

# Then re-run
./deploy.sh YOUR_PROJECT_ID us-east1
```

**Check deployment logs:**
The script outputs detailed logs. If something fails, scroll up to see the error message.

### Cost Estimate

Running 24/7:
- Cloud Run: ~$10-20/month
- Dataflow: ~$50-100/month
- BigQuery: ~$5-10/month
- Other services: ~$5-10/month

**Total: ~$70-140/month**

💡 **Tip:** Delete resources when not in use to save costs!

### Cleanup

To delete everything:
```bash
cd 4-terraform
terraform destroy -auto-approve
```

### Need Help?

- 📖 [Full Documentation](readme.md)
- 🐛 [Report Issues](https://github.com/DanHerman212/streaming-systems/issues)
- 📧 Email: [your-email]

---

**Next Steps:**
- [Query your data in BigQuery](5-sql/)
- [View the architecture diagram](0.5%20Architecture.png)
- [Understand the data schema](data.md)
