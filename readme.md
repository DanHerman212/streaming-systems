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
The implementation is quite simple, it's a 4 step process:<br><br>
To get started, please launch a new <img src="images/shell.png" alt="drawing" width="100"/> 

## Step 1: Containerize Applications <br>
```shell
./build_containers.sh
```
Once the script completes go to step 2

## Step 2: Deploy Infrastructure <br>
```shell
cd terraform
terraform init
terraform apply
```
Once the infrastructure is deployed go to step 3<br>
## Step 3: Deploy Dataflow Job - It takes 3 minutes for Dataflow to get started <br>
```shell
python dataflow/deploy_dataflow.py
``` 
Once Dataflow is deployed go to step 4<br>
## Step 4:  Turn on `Cloud Scheduler` to activate the trigger and start the event feed as it will be deployed in a paused state.<br>
![Cloud Scheduler](/images/scheduler.png)


<br>

## Dataflow Dashboard
It will take 3 minutes for Dataflow to get up and running.  You can check the data watermark lag on the first step of the pipeline.  That's the primary performance metric you should be concerned about.
<br>
![Dataflow Dashboard](/images/dataflow.png)
</font>