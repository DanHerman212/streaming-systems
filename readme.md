# Stream Processing Systems
<font size="4">Production grade data pipelines capable of processing event streams in real time or near real time. <br>
<br>
For this particular implementation, the architecture is setup on GCP and is completely serverless.  The design is modular and is based on a real time data warehouse, that delivers between 7 second to 35 second data processing times (dependant on event stream).  The warehouse can be swapped for a nosql database to support immediate i/o for real time applications.<br>
<br>
![Architecture Diagram](0.5%20Architecture.png) <br>
<br>
The architecture uses the following GCP services:<br>
- Artifact Registry: Universal Package Manager<br>
- Cloud Run: Serverless Application Execution<br>
- Cloud Tasks: Queue Management<br>
- Cloud Scheduler: Cron Jobs (Event Triggers) <br>
- Pub/Sub: Message Broker<br>
- Dataflow: Stream Processing Engine<br>
- BigQuery: Data Warehouse

</font>
