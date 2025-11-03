# Stream Processing Systems
<br>
Production grade data pipelines capable of processing event streams in real time or near real time.
<br><br>

This implementation is connected to the [MTA real-time data feed](https://api.mta.info/#/subwayRealTimeFeeds) for the New York City subway system.  There are 8 separate feeds available, where this project is connected to the ACE subway line, which can be observed on the [subway diagram](https://www.mta.info/map/5256).<br>  <br>The subway system is the largest in the world, with approximately 3.5 million daily riders, accessing subways through 470 stations, operating 24/7.  The ACE line includes roughly 30 stations and produces 1,200 unique daily trips on a weekday or 750 unique daily trips on weekends.<br>

The MTA claims the feed is updated with each subway vehicle timestamp every 30 seconds.  However, we found the updates are produced from 5 - 25 seconds.
We are polling the subway feed every 20 seconds, processing 3 messages per minute.  The feed produces nearly 1.25gb of data every 24 hrs with roughly, 250,000 updates per 24 hrs on a weekday and about 130,000 updates on a weekend.
<br>

# Video Tutorial
This Tutorial will provide a comprehensive walk through on the project implementation and architecture.<br>

![Video Title](https://www.youtube.com/watch?v=VIDEO_ID)<br>


![Architecture Diagram](/7-images/architecture2.png) <br>
<br><font size="4">
The architecture uses the following GCP services:<br>
- Artifact Registry: Universal Package Manager<br>
There are two applications built with Flask that will be containerized to poll the MTA endpoint, executed through Cloud Run.  The first application is the event processor, which fetches messages and publishes to pubsub.  The next application is a task queue, which will setup 3 tasks to poll the event processor.  The first task will get fired off immediately, the second task will be scheduled on a 20 second delay and the third on a 40 second delay.  The task queue will be triggered every minute by Cloud Scheduler.  

- Cloud Run: Serverless Application Execution<bR>
The event processor and task queue will be deployed for execution on Cloud Run<br>

- Cloud Tasks: Queue Management<br>
This is a workaround, since Cloud Run does not allow you to run a continuous loop in a container.  The container will time out after 12 minutes.  Cloud tasks allows us to distribute triggers asyncronously for granular controls of long running tasks.  The task queue sends a `POST` message to the event processor every 20 seconds to fetch messages.<br>

- Cloud Scheduler: Cron Jobs (Event Triggers)<br>
Creates event triggers on a schedule.  There is a constraint where the lowest time interval available is 1 minute.  You cannot schedule sub 1 minute triggers.  Therefore, we setup the workaround with Cloud Tasks to distribute 3 triggers every minute on a 20 second interval.<br>

- Pub/Sub: Message Broker<br>
Messages are fetched from the MTA and published to a pubsub topic.  There is a pubsub pull subscription setup with the consumer, which is Dataflow, the data processing engine.<br>

- Dataflow: Stream Processing Engine<br>
Dataflow consumes messages, applies transformations and writes to a 'data sink'.  For this implementation there are 3 primary transforms, where we will first 1) Flatten 2) Filter and 3) Enrich.  The messages come in json and need to be flattened.  Then we will filter erroneous messages that are not relevant, finally we will enrich with the stops data including stop name and GIS data (lat lon) for interpretability and data visualization.

- BigQuery: Data Warehouse<br>
Once the data is processed it will be written to BigQuery, available for analysis between 7 - 35 seconds after the data is generated.  For faster read/write, where lower latency is a requirement, BigTable can be plugged in as an alternative data sink.
</font>

## Implementation Steps
## Most implementation is automated through <img src="7-images/tf.png" alt="drawing" width="50"/><br>
<br><font size="4">
The implementation is quite simple, it's a 6 step process:<br><br>
To get started, please launch a new <img src="7-images/shell.png" alt="drawing" width="100"/> 

## Step 1: Clone the Repository<br>
```shell
git clone https://github.com/your-username/streaming-systems.git
```
## Step 2: Enable APIs:
Update the project flag at the end of this command
```shell
gcloud services enable cloudresourcemanager.googleapis.com \
  cloudtasks.googleapis.com \
  pubsub.googleapis.com \
  iam.googleapis.com \
  --project=<your-project-id>
```

## Step 2: Containerize Applications <br>
Open the file editor<br>
Look in the root directory and open `build_images.sh` <br>

You will first need to update your project id in the bash script.
```shell
# update your project id in the build_images.sh script
REPO="gcr.io/YOUR_PROJECT_ID"
```
Return to the terminal to run the bash script<br>
It will containerize the code and push the container to the container registry<br>
```shell
# run the script from the root directory
./build_images.sh
```
Once the script completes go back into the file editor<br>
Go to `4-terraform` folder and update the .tfvars file with the image URIs<br>
Now update the project-id<br>
pro tip: there is a `sample.tfvars` file in the `4-terraform` folder<br>

```shell
# Replace your-project with your GCP project ID
project_id = "your-project-id"
mta_processor_endpoint_image = "gcr.io/your-project-id/mta-processor"
event_task_enqueuer_image    = "gcr.io/your-project-id/event-task-enqueuer"
```
After project variables are updated, go back to the terminal<br>
and proceed to step 4<br>

## Step 4: Deploy Infrastructure <br>
```shell
cd 4-terraform
terraform init
terraform apply
```
Once infrastructure is deployed prepare the Dataflow script<br>

## Step 5: Prepare and Launch Dataflow Pipeline<br>
There are a few places where project ID needs to be updated.<bR>
I created a bash script that will update all fields for you.<br>
please execute the command below, replacing `<YOUR_PROJECT_ID>` with your actual GCP project ID and it will update your dataflow script.<bR>

```shell
cd streaming-systems/1-dataflow
./replace_project_id.sh <YOUR_PROJECT_ID>
```

Once the infrastructure is deployed go to step 5<br>
## Step 5: Deploy Dataflow Job - It takes 3 minutes for Dataflow to get started <br>
```shell
cd 1-dataflow
python dataflow.py
``` 
Once Dataflow is deployed go to step 4<br>
## Step 6:  Turn on `Cloud Scheduler` to activate the trigger and start the event feed as it will be deployed in a paused state.<br>
![Cloud Scheduler](/7-images/scheduler.png)


<br>

## Dataflow Dashboard
It will take 3 minutes for Dataflow to get up and running.  You can check the data watermark lag on the first step of the pipeline.  That's the primary performance metric you should be concerned about.
<br>

![Dataflow Dashboard](/7-images/dataflow.png)

# Data Dictionary
Data definition can be found at [data dictionary page](data.md)<br>

# SQL Anlaysis and Data Visualization
Queries can be found in the [sql folder](/5-sql) folder.<br>

## Avg Time Between Trains and Frequency
The average time waiting for a train and the frequency of trains on the ACE line during a 24 hour weekday period.
![Avg Time Between Train Arrivals](/7-images/avg_time_bet_trains1.png)
<br>

# Top 10 Busiest Stations
These are the busiest stations for the ACE line, based on total number of train arrivals in a 24 hour weekday period.
![Top 10 Busiest Stations](/7-images/barplot.png)
Fun Fact: [42-St Port Authority Terminal](https://www.mta.info/agency/new-york-city-transit/subway-bus-ridership-2024) (Times Square) has the most riders with 58 million paid passengers in 2024.

# Idle Time Per Station
The map represents all stations and average idle time per station.  Most stations show less than 30 second idle time, for the ACE line.
![Idle Time Per Station](/7-images/idle.png)
---
# Folder Structure
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
</font>