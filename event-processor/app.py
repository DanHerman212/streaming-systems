import os
import requests
import json
from flask import Flask, Response, request
from google.cloud import pubsub_v1
from google.protobuf.json_format import MessageToJson
from google.transit import gtfs_realtime_pb2
import datetime
import base64
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

#----Configuration
PROJECT_ID = os.environ.get('PROJECT_ID')
NYC_SUBWAY_FEED_URL = os.environ.get('NYC_SUBWAY_FEED_URL')
PUBSUB_TOPIC_ID = os.environ.get('PUBSUB_TOPIC_ID')
#----------

publisher = pubsub_v1.PublisherClient()

@app.route('/', methods=['POST'])
def fetch_and_publish_subway_data():
    # --- IMMEDIATE LOGGING FOR INCOMING REQUEST ---
    logging.info(f"Received POST request from Cloud Tasks. Request Headers: {request.headers}")
    if request.data:
        logging.info(f"Request Body: {request.data.decode('utf-8')}") # Log body if present

    missing = [name for name, val in (
        ("GCP_PROJECT_ID", PROJECT_ID),
        ("PUBSUB_TOPIC_ID", PUBSUB_TOPIC_ID),
        ("NYC_SUBWAY_FEED_URL", NYC_SUBWAY_FEED_URL),
    ) if not val]
    if missing:
        logging.error("Missing required environment variables: %s", missing)
        # --- RETURN 400 FOR CONFIGURATION ERRORS ---
        return (f"Missing required environment variables: {', '.join(missing)}", 400)

    try:
        #1 fetch data from NYC subway api
        response = requests.get(NYC_SUBWAY_FEED_URL, timeout=10)
        response.raise_for_status() # raise an exception for http errors

        #2 parse grfs realitme protocol buffer
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)

        #3 convert to human-readable json
        human_readable_data_json = MessageToJson(
            feed, preserving_proto_field_name=True, indent=2)
        data_bytes = human_readable_data_json.encode('utf-8')

        # 4 determine ordering key and unique event id
        feed_timestamp = (feed.header.timestamp
        if feed.header.HasField('timestamp')
        else int(datetime.datetime.now(datetime.timezone.utc).timestamp()))

        parsed_json_dict = json.loads(human_readable_data_json)
        parsed_json_dict['unique_event_id'] = f"{feed_timestamp}-{hash(human_readable_data_json)}"
        parsed_json_dict["event_timestamp_unix"] = feed_timestamp

        # re-encode the json with the added unique event id
        data_bytes_with_id = json.dumps(parsed_json_dict).encode('utf-8')

        #5 publish to pub/sub with ordering_key
        topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC_ID)
        future = publisher.publish(
            topic_path,
            data=data_bytes_with_id
            #ordering_key=ordering_key # set ordering key here
        )
        message_id = future.result()

        logging.info(f"Successfully fetched, parsed, and published data to {topic_path}. Message ID: {message_id}")
        # --- EXPLICIT SUCCESS RESPONSE ---
        return f"Succesfully fetched, parsed and publised data to {topic_path}. Message ID: {message_id}", 200

    except requests.exceptions.RequestException as e:
        logging.exception("HTTP request to NYC subway API failed")
        # --- RETURN 500 FOR EXTERNAL API FAILURES TO TRIGGER RETRY ---
        return f"Failed to fetch subway data: {e}", 500
    except Exception as e:
        logging.exception("An unexpected error occurred during data processing or publishing")
        # --- RETURN 500 FOR UNEXPECTED INTERNAL ERRORS ---
        return f"An unexpected error occurred: {e}", 500

@app.route('/', methods=['GET'])
def health_check():
    # --- LOG HEALTH CHECK ---
    logging.info("Health check received.")
    return "MTA Request Endpoint is running!", 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

