# Stream Processing Systems
<br>
Production grade data pipelines capable of processing event streams in real time or near real time.
<br><br>

This implementation is connected to the [MTA real-time data feed](https://api.mta.info/#/subwayRealTimeFeeds) for the New York City subway system.  There are 8 separate feeds available, where this project is connected to the ACE subway line, which can be observed on the [subway diagram](https://www.mta.info/map/5256).<br>  <br>The subway system is the largest in the world, offering 475 stations, operating 24/7.  The ACE line includes roughly 30 stations and produces 1,200 unique daily trips on a weekday or 750 unique daily trips on weekends.<br>

The MTA claims the feed is updated with each subway vehicle timestamp every 30 seconds.  However, we found the updates are produced from 5 - 25 seconds.
We are polling the subway feed every 20 seconds, processing 3 messages per minute.  The feed produces nearly 1.25gb of data every 24 hrs with roughly, 250,000 updates per 24 hrs on a weekday and about 150,000 updates on a weekend.
<br>

# Video Tutorial
This Tutorial will provide a comprehensive walk through on the project implementation and architecture.<br>

![Video Title](https://www.youtube.com/watch?v=VIDEO_ID)<br>


![Architecture Diagram](/z_images/architecture2.png) <br>
<br><font size="4">
The architecture uses the following GCP services:<br>
- Artifact Registry: Universal Package Manager<br>
There are two applications built with Flask that will be containerized to poll the MTA endpoint through Cloud Run.  The first application is the event processor, which fetches messages and publishes to pubsub.  The next application is a task queue, which will setup 3 tasks to poll the MTA endpoint.  The first task will get fired off immediately, the second task will be scheduled on a 20 second delay and the third on a 40 second delay  

- Cloud Run: Serverless Application Execution
The event processor and task queue will be deployed for execution on Cloud Run<br>

- Cloud Tasks: Queue Management
This is a workaround, since Cloud Run does not allow you to run a continuous loop in a container.  The container will time out after 12 minutes.  Cloud tasks allows us to distribute triggers to granular controls for long running tasks.  The task queue polls the data feed every 20 seconds<br>

- Cloud Scheduler: Cron Jobs (Event Triggers)
Creates event triggers on a schedule.  There is a constraint where the lowest time interval available is 1 minute.  This is a workaround for Cloud Run's 12 minute timeout limit.  The scheduler will trigger the task queue every minute to poll the MTA endpoint.

- Pub/Sub: Message Broker
Messages are fetched from the MTA and published to a pubsub topic.  There is a pubsub pull subscription setup with the consumer, which is Dataflow, the data processing engine.<br>

- Dataflow: Stream Processing Engine
Dataflow consumes messages, applies transformations and writes to a 'data sink'.  For this implementation there are 3 primary transforms, where we will first 1) Flatten 2) Filter and 3) Enrich.  The messages come in json and need to be flattened.  Then we will filter erroneous messages that are not relevant, finally we will enrich with the stops data including stop name and GIS data (lat lon) for interpretability and data visualization.

- BigQuery: Data Warehouse
Once the data is processed it will be written to BigQuery, available for analysis between 7 - 35 seconds after the data is generated.  For faster read/write, where lower latency is a requirement, BigTable can be plugged in as an alternative data sink.
</font>

## Implementation Steps
## Most implementation is automated through <img src="z_images/tf.png" alt="drawing" width="50"/><br>
<br><font size="4">
The implementation is quite simple, it's a 4 step process:<br><br>
To get started, please launch a new <img src="z_images/shell.png" alt="drawing" width="100"/> 

## Step 1: Containerize Applications <br>
```shell
./build_containers.sh
```
Once the script completes update the .tfvars file with the image URIs and go to step 2<br>
```shell
# Replace your-project with your GCP project ID
mta_processor_endpoint_image = "gcr.io/your-project/mta-processor"
event_task_enqueuer_image    = "gcr.io/your-project/event-task-enqueuer"
```

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
![Cloud Scheduler](/z_images/scheduler.png)


<br>

## Dataflow Dashboard
It will take 3 minutes for Dataflow to get up and running.  You can check the data watermark lag on the first step of the pipeline.  That's the primary performance metric you should be concerned about.
<br>

![Dataflow Dashboard](/z_images/dataflow.png)

</font>

## SQL Anlaysis and Data Visualization
<br>

## Folder Structure
```
├── dataflow # script for dataflow pipeline
│   ├── dataflow.py
│   ├── service_account.sh
│   └── write_to_bq.sh
├── event-processor # collects messages and sends them to pubsub from data feed
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── task-queue # distributes triggers to the event processor asynchronously every 20 seconds
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── terraform # infrastructure as code using terraform
│   ├── main.tf
│   ├── modules
│   │   ├── apis
│   │   ├── cloud_run
│   │   ├── cloud_tasks
│   │   ├── pubsub
│   │   ├── scheduler
│   │   ├── service_accounts
│   │   └── storage
│   ├── outputs.tf
│   ├── terraform.tfvars
│   └── variables.tf
├── utils # utilities to build container images
│   ├── build_containers.sh
└── z_images # images for presentation
    ├── 0.5 Architecture.png
    ├── architecture2.png
    ├── dataflow.png
    ├── image.png
    ├── scheduler.png
    ├── shell.png
    └── tf.png
├── readme.md
├── schema.json # BigQuery table schema for pipeline
├── stops.csv # station names for MTA used to enrich dataset in pipeline
```
<br>