# Stream Processing Systems
<br>
Production grade data pipelines capable of processing event streams in real time or near real time. <br>
<br>

# Video Tutorial

![Video Title](https://www.youtube.com/watch?v=VIDEO_ID)<br>
<br>
For this particular implementation, the architecture is setup on GCP and is completely serverless.  The design is modular with a primary goal to provide a real time data warehouse, delivering data between 7 - 35 seconds after it's created (dependant on event stream).  The warehouse can be swapped for a nosql database such as BigTable, to support lower latency i/o for real time applications.<br>
<br>

![Architecture Diagram](/images/architecture2.png) <br>
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
## Most implementation is automated through <img src="images/tf.png" alt="drawing" width="50"/><br>
<br><font size="4">
The implementation is quite simple, it's a 3 step process:<br><br>
To get started, please launch a new <img src="images/shell.png" alt="drawing" width="100"/> 

Step 1: Containerize Applications <br>
```shell
./build_containers.sh
```
Step 2: Deploy Infrastructure <br>
```shell
cd terraform
terraform init
terraform apply
```
Step 3: Deploy Dataflow Job <br>
```shell
python dataflow/deploy_dataflow.py
``` 
</font>

<br>

<font size="5">

The Terraform script will go through this order of operations:<br><br>
1. Enable APIs
2. Create Service Accounts and Grant Permissions
3. Create Cloud Run Services:
    - Event Processor
    - Task Queue
4. Create Pub/Sub Topics and Subscriptions
5. Create Scheduler Job

</font><br>