# Stream Processing Systems
<br>
Production grade data pipelines capable of processing event streams in real time or near real time. <br>
<br>

# Video Tutorial

![Video Title](https://www.youtube.com/watch?v=VIDEO_ID)<br>
<br>
For this particular implementation, the architecture is setup on GCP and is completely serverless.  The design is modular and is based on a real time data warehouse, that delivers between 7 second to 35 second data processing times (dependant on event stream).  The warehouse can be swapped for a nosql database to support immediate i/o for real time applications.<br>
<br>

![Architecture Diagram](architecture2.png) <br>
<br><font size="4">
The architecture uses the following GCP services:<br>
- Artifact Registry: Universal Package Manager<br>
- Cloud Run: Serverless Application Execution<br>
- Cloud Tasks: Queue Management<br>
- Cloud Scheduler: Cron Jobs (Event Triggers) <br>
- Pub/Sub: Message Broker<br>
- Dataflow: Stream Processing Engine<br>
- BigQuery: Data Warehouse
</font>

## Implementation Steps
Step 2 will be executed through a bash script(outlined below), the remaining steps are done through executing a Terraform script to provision all services and granting permissions to service accounts.<br>
<br>
<font size="4">
1. Enable APIs
2. Containerize Applications 
3. Create Service Accounts and Grant Permissions
4. Create Cloud Run Services:
    - Event Processor
    - Task Queue
5. Create Pub/Sub Topics and Subscriptions
6. Create Scheduler Job
7. Create Dataflow Job
</font><br>