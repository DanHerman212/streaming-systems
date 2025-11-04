# Stream Processing Systems
<br><font size="5">
Production grade data pipelines capable of processing event streams in real time or near real time.
<br><br>

This implementation is connected to the [MTA real-time data feed](https://api.mta.info/#/subwayRealTimeFeeds) for the New York City subway system.  There are 8 separate feeds available, where this project is connected to a single feed, which is the ACE subway line, which can be observed on the [subway diagram](https://www.mta.info/map/5256).<br>  <br>The subway system is the largest in the world, with approximately 3.5 million daily riders, accessing subways through 470 stations, operating 24/7.  The ACE line will travel through approximately 100 of these stations and produce 1,200 unique daily trips on a weekday or 750 unique daily trips on weekends.<br>

The MTA claims the feed is updated with each subway vehicle timestamp every 30 seconds.  However, we found the updates are produced from 5 - 25 seconds.
We are polling the subway feed every 20 seconds, processing 3 messages per minute.  We are getting roughly 50 - 60 updates per message, so about 150 - 180 updates per minute. The feed produces nearly 1.25gb of data every 24 hrs with roughly 250,000 updates per 24 hrs on a weekday and about 130,000 updates on a weekend.
<br>

# Video Tutorial
I will launch a video tutorial sometime soon to walk through the project.

![Architecture Diagram](/6-images/architecture2.png) <br>
<br>
The architecture uses the following GCP services:<br>
- Artifact Registry: Universal Package Manager<br>
There are two applications built with Flask that will be containerized to poll the MTA endpoint, executed through Cloud Run.  The first application is the event processor, which fetches messages and publishes to pubsub.  The next application is a task queue, which will setup 3 tasks to poll the event processor.  The first task will get fired off immediately, the second task will be scheduled on a 20 second delay and the third on a 40 second delay.  The task queue will be triggered every minute by Cloud Scheduler.  

- Cloud Run: Serverless Application Execution<br>
The event processor and task queue will be deployed for serverless execution on Cloud Run<br>

- Cloud Tasks: Queue Management<br>
This is a workaround, since I was having trouble finding ways to poll the MTA endpoint continuously.  Cloud Run does not allow you to run a continuous loop in a container.  The container will time out after 12 minutes.  Cloud tasks allows us to distribute triggers asyncronously for granular controls of long running tasks.  The task queue sends a `POST` message to the event processor every 20 seconds to fetch messages.<br>

- Cloud Scheduler: Cron Jobs (Event Triggers)<br>
Creates event triggers on a schedule.  There is a constraint where the lowest time interval available is 1 minute.  You cannot schedule sub 1 minute triggers.  Therefore, we setup the workaround with Cloud Tasks, where we receive a trigger every minute and distribute 3 tasks in 20 second intervals, providing more granular control.<br>

- Pub/Sub: Message Broker<br>
Messages are fetched from the MTA and published to a pubsub topic.  There is a pubsub pull subscription setup with the consumer, which is Dataflow, the data processing engine.<br>

- Dataflow: Data Processing Engine<br>
Dataflow consumes messages, applies transformations and writes to a relational database.  For this implementation there are 4 primary transforms, where we will first 1) Flatten 2) Filter 3) Enrich and 4) Apply windowing to our datset before we write to BigQuery.  The messages come in json and need to be flattened.  Most information in the feed is not required, so we will filter out 97% of the information.  After filtering, we will enrich with station information that is provided through a static csv file.  After enrichment, we will apply windowing to handle late arriving data and ensure data consistency.<br>

- BigQuery: Data Warehouse<br>
Once the data is processed it will be written to BigQuery, available for analysis between 7 - 35 seconds after the data is generated.  For faster read/write, where lower latency is a requirement, BigTable can be plugged in as an alternative data sink.
</font>
<br>

<font size="5">

# Implementation Steps
Most implementation is automated through Terraform<img src="6-images/tf.png" alt="drawing" width="50"/>

# Quick Start 
Deploy the entire pipeline with a single command! 

## Prerequisites
- Google Cloud Project with billing enabled
- Owner or Editor permissions
- Cloud Shell or `gcloud` CLI installed

## One-Command Deployment

**Step 1:** Open [Google Cloud Shell](https://shell.cloud.google.com/) 

**Step 2:** Clone the repository
```shell
git clone https://github.com/DanHerman212/streaming-systems.git
cd streaming-systems
```

**Step 3:** Run the deployment script
```shell
chmod +x deploy.sh
./deploy.sh YOUR_PROJECT_ID us-east1
```
</font>

## **That's it!**<br>
### Here is what happens next:
<font size="5">
1.  It will take between 1 - 2 minutes to deploy the containers and about 1 minute to deploy all the infrastructure.<br>
<bR>
2. There are quite a few service accounts and permissions being propogated, with that said, you may see some errors from cloud scheduler and in the logs for cloud run. It can take between 20 - 30 minutes to propagate permissions.
Ignore these errors, as the permissions propagate in the background, it will self-correct.<br>
<br>
3. The dataflow script takes 3 minutes to warm up.<br>
<br> 
4. It will take dataflow about 35 - 40 minutes to catch up to the data feed, where you should see an improvement in performance metrics on the dataflow dashboard.<br>


# Dataflow Dashboard
It will take 3 minutes for Dataflow to get up and running.  You can check the data watermark lag on the first step of the pipeline.  That's the primary performance metric you should be concerned about.
<br>

![Dataflow Dashboard](/6-images/dataflow.png)
<bR><br>
You can click the three small dots and expand the dashboard for better visibility.

![Dataflow Dashboard Expanded](/6-images/1206.png)

# Data Dictionary
Data definition can be found at [data dictionary page](data.md)<br>

# SQL Anlaysis and Data Visualization
As a frequent passenger of the ACE subway line, I answered a few common questions I was curious about:<br>
- What is the average time between train arrivals on the ACE line during a weekday?<br>
- What are the top 10 busiest stations on the ACE line?<br>
- What is the average idle time per station on the ACE line?<br><br>
Queries can be found in the [sql folder](/5-sql) folder.<br>

## Avg Time Between Trains and Frequency
The range of time waiting for a train can be less than 2 minutes to over 16 minutes.  There is a clear correlation between busy stations and wait times.  Busier stations are served with <2 minute wait times.  <br>  The top 5 stations can be observed in the lower right quadrant.  The next insight will identify those stations.

![Avg Time Between Train Arrivals](/6-images/avg_time_bet_trains1.png)
<br>

# Top 10 Busiest Stations
These are the busiest stations for the ACE line, based on total number of train arrivals in a 24 hour weekday period.
![Top 10 Busiest Stations](/6-images/barplot.png)
Fun Fact: [42-St Port Authority Terminal](https://www.mta.info/agency/new-york-city-transit/subway-bus-ridership-2024) (Times Square) has the most riders with 58 million paid passengers in 2024.

# Idle Time Per Station

The map represents all stations and average idle time per station.  Most stations show less than 30 second idle time, for the ACE line.

![Idle Time Per Station](/6-images/idle.png)
---
# Folder Structure
```
├── 1-dataflow # dataflow pipeline script and utilities
│   ├── dataflow.py
│   └── replace_project_id.sh
├── 2-event-processor # event processor application that fetches messages
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── 3-task-queue # task queue polls the event processor every 20 seconds
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── 4-terraform # terraform infrastructure as code - automates deployment in 1 minute
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
│   ├── sample.tfvars
│   ├── schema.json
│   └── variables.tf
├── 5-sql # a few sample SQL queries to experiment with
│   ├── avg idle time by station.sql
│   └── avg wait time and total trips per station.sql
├── 6-images # just images for presentation
│   ├── 0.5 Architecture.png
│   ├── architecture2.png
│   ├── avg_time_bet_trains1.png
│   ├── barplot.png
│   ├── dataflow.png
│   ├── idle.png
│   ├── image.png
│   ├── scheduler.png
│   ├── shell.png
│   └── tf.png
├── build_images.sh # script to automate container builds
├── data.md # data dictionary
├── deploy.sh # one-command deployment script
└── readme.md # this file
``` 
</font>