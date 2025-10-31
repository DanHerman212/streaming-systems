# Stream Processing Systems
<font size="5">Production grade data pipelines capable of processing event streams in real time or near real time. <br>
<br>
For this particular implementation, the architecture is setup on GCP and is completely serverless.  The design is modular with a primary goal to provide a real time data warehouse, delivering data between 7 - 35 seconds after it's created (dependant on event stream).  The warehouse can be swapped for a nosql database such as BigTable, to support lower latency i/o for real time applications.<br>
<br>
![Architecture Diagram](architecture2.png) <br>
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
