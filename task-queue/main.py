# main.py for event-task-enqueuer
import os
import json
from datetime import datetime, timedelta

from flask import Flask, request
from google.cloud import tasks_v2

app = Flask(__name__)
client = tasks_v2.CloudTasksClient()

PROJECT_ID = os.environ.get('PROJECT_ID')
REGION = os.environ.get('REGION')
TASK_QUEUE_NAME = os.environ.get('TASK_QUEUE_NAME')
EVENT_FEED_PROCESSOR_SERVICE_URL = os.environ.get('EVENT_FEED_PROCESSOR_SERVICE_URL') 
TASKS_SA_EMAIL = os.environ.get('TASKS_SA_EMAIL') # Service account for Cloud Tasks to invoke processor

@app.route('/', methods=['POST'])
def enqueue_tasks():
    try:
        processor_service_url = EVENT_FEED_PROCESSOR_SERVICE_URL 
        queue_path = client.queue_path(PROJECT_ID, REGION, TASK_QUEUE_NAME)
        
        # Define a base task structure to avoid repetition
        base_task_http_request = {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": processor_service_url,
            "oidc_token": {
                "service_account_email": TASKS_SA_EMAIL,
                "audience": processor_service_url,
            },
            "headers": {"Content-Type": "application/json"},
        }

        # Task 1: Trigger immediately (0 seconds delay)
        schedule_time_1 = datetime.utcnow()
        task1 = {
            "http_request": {
                **base_task_http_request,
                "body": json.dumps({"trigger_time": schedule_time_1.isoformat()}).encode(),
            }
        }
        client.create_task(parent=queue_path, task=task1)
        print(f"Enqueued immediate task for {processor_service_url} at {schedule_time_1}")

        # Task 2: Trigger after 20 seconds
        schedule_time_2 = datetime.utcnow() + timedelta(seconds=20)
        task2 = {
            "http_request": {
                **base_task_http_request,
                "body": json.dumps({"trigger_time": schedule_time_2.isoformat()}).encode(),
            },
            "schedule_time": schedule_time_2,
        }
        client.create_task(parent=queue_path, task=task2)
        print(f"Enqueued delayed task for {processor_service_url} at {schedule_time_2}")

        # Task 3: Trigger after 40 seconds
        schedule_time_3 = datetime.utcnow() + timedelta(seconds=40)
        task3 = {
            "http_request": {
                **base_task_http_request,
                "body": json.dumps({"trigger_time": schedule_time_3.isoformat()}).encode(),
            },
            "schedule_time": schedule_time_3,
        }
        client.create_task(parent=queue_path, task=task3)
        print(f"Enqueued delayed task for {processor_service_url} at {schedule_time_3}")

        return "Tasks enqueued successfully", 200
    except Exception as e:
        print(f"Error enqueuing tasks: {e}")
        return f"Error: {e}", 500

@app.route('/', methods=['GET'])
def health_check():
    return "Task Enqueuer is running!", 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
