import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions, SetupOptions
import datetime
import json
import csv
import pytz

# ============================================
# Configuration
# ============================================
PROJECT_ID = "<your-project-id>"
BIGQUERY_DATASET = "mta_updates"
BIGQUERY_TABLE = "<your-project-id>.mta_updates.realtime_updates"
PUBSUB_SUBSCRIPTION = "mta-gtfs-ace-sub"  # Subscription that receives MTA GTFS-RT updates
GCS_STOPS_CSV_PATH = "gs://<your-project-id>-enrichment/stops.csv"  # Static stop metadata for enrichment
FEED_TZ = pytz.timezone('America/New_York')  # MTA operates in NYC timezone
REGION = "us-east1"  # GCP region for Dataflow workers

# ============================================
# Schema Definitions
# ============================================
# Fields required in the final output to BigQuery
REQUIRED_FIELDS = [
    'unique_event_id', 'feed_header_timestamp', 'entity_id', 'trip_id', 'start_time', 'start_date',
    'route_id', 'stop_id', 'vehicle_timestamp', 'current_status', 'current_stop_sequence',
    'stop_name', 'stop_lat', 'stop_lon', 'direction'
]

# BigQuery table schema definition
BIGQUERY_SCHEMA = {
    'fields': [
        {'name': 'unique_event_id', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'feed_header_timestamp', 'type': 'TIMESTAMP', 'mode': 'NULLABLE'},
        {'name': 'entity_id', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'trip_id', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'start_time', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'start_date', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'route_id', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'stop_id', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'vehicle_timestamp', 'type': 'TIMESTAMP', 'mode': 'NULLABLE'},
        {'name': 'current_status', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'current_stop_sequence', 'type': 'INTEGER', 'mode': 'NULLABLE'},
        {'name': 'stop_name', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'stop_lat', 'type': 'FLOAT', 'mode': 'NULLABLE'},
        {'name': 'stop_lon', 'type': 'FLOAT', 'mode': 'NULLABLE'},
        {'name': 'direction', 'type': 'STRING', 'mode': 'NULLABLE'}
    ]
}

# ============================================
# Enrichment Function
# ============================================
def enrich_with_stops(rec: dict, stops_map):
    """
    Enriches a transit record with stop metadata (name, lat/lon, direction).
    
    Args:
        rec: Dictionary containing transit event data with 'stop_id'
        stops_map: Dictionary mapping stop_id -> {stop_name, stop_lat, stop_lon}
    
    Returns:
        Enriched dictionary with stop metadata and direction
    
    Logic:
        1. Extract stop_id from record
        2. Try exact match, then uppercase match
        3. If no match and stop_id ends with letter (e.g., 'A01N'), try without suffix
        4. Add stop name, coordinates, and derive direction from stop_id suffix
    """
    sid = rec.get('stop_id')
    if not sid:
        # No stop_id provided - return with null values
        rec.update({'stop_name': None, 'stop_lat': None, 'stop_lon': None, 'direction': None})
        return {k: rec.get(k) for k in REQUIRED_FIELDS}
    
    sid_processed = str(sid).strip()
    
    # Try exact match, then uppercase match
    info = stops_map.get(sid_processed) or stops_map.get(sid_processed.upper())
    
    # If no match and stop_id ends with letter (direction indicator like 'N' or 'S'), try without it
    if not info and sid_processed and sid_processed[-1].isalpha():
        info = stops_map.get(sid_processed[:-1]) or stops_map.get(sid_processed[:-1].upper())
    
    # Populate stop metadata
    rec['stop_name'] = info.get('stop_name') if info else None
    try:
        rec['stop_lat'] = float(info.get('stop_lat')) if info and info.get('stop_lat') else None
    except ValueError:
        rec['stop_lat'] = None
    try:
        rec['stop_lon'] = float(info.get('stop_lon')) if info and info.get('stop_lon') else None
    except ValueError:
        rec['stop_lon'] = None
    
    # Derive direction from stop_id (e.g., 'A01S' = Southbound, 'A01N' = Northbound)
    rec['direction'] = 'Southbound' if sid_processed and 'S' in sid_processed else 'Northbound'
    
    return {k: rec.get(k) for k in REQUIRED_FIELDS}

# ============================================
# GTFS-Realtime Flattening Function
# ============================================
def flatten_gtfs(obj):
    """
    Flattens nested GTFS-Realtime protobuf JSON into row-level records.
    
    GTFS-RT structure:
        - header: Feed metadata (timestamp)
        - entity[]: Array of transit updates
            - trip_update: Scheduled stop predictions
            - vehicle: Real-time vehicle positions
    
    This function:
        1. Extracts feed header timestamp
        2. Iterates through entities
        3. For trip_updates: Creates one row per stop_time_update
        4. For vehicle updates: Creates one row per vehicle position
        5. Returns flattened records suitable for BigQuery
    """
    header = obj.get('header', {})
    entities = obj.get('entity', [])
    
    # Parse feed header timestamp (when MTA published this update)
    feed_header_timestamp = None
    ts = header.get('timestamp')
    if ts:
        try:
            dt = datetime.datetime.fromtimestamp(int(ts), tz=datetime.timezone.utc)
            feed_header_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
    
    unique_event_id = obj.get('unique_event_id')
    
    # Process each entity (trip update or vehicle position)
    for ent in entities:
        # Base record with common fields
        base = {
            "unique_event_id": unique_event_id,
            "feed_header_timestamp": feed_header_timestamp,
            "entity_id": ent.get('id'),
            "trip_id": None,
            "start_time": None,
            "start_date": None,
            "route_id": None,
            "stop_id": None,
            "vehicle_timestamp": None,
            "current_status": None,
            "current_stop_sequence": None,
            "stop_name": None,
            "stop_lat": None,
            "stop_lon": None,
            "direction": None
        }
        
        # Process trip_update entities (scheduled predictions for stops)
        if 'trip_update' in ent:
            trip = ent['trip_update'].get('trip', {})
            base.update({
                'trip_id': trip.get('trip_id'),
                'start_time': trip.get('start_time'),
                'start_date': trip.get('start_date'),
                'route_id': trip.get('route_id')
            })
            # Create one record per stop in the trip
            for su in ent['trip_update'].get('stop_time_update', []) or []:
                r = dict(base)
                r['stop_id'] = su.get('stop_id')
                yield {k: r.get(k) for k in REQUIRED_FIELDS}
        
        # Process vehicle entities (real-time positions)
        elif 'vehicle' in ent:
            v = ent['vehicle']
            trip = v.get('trip', {})
            r = dict(base)
            r.update({
                'trip_id': trip.get('trip_id'),
                'start_time': trip.get('start_time'),
                'start_date': trip.get('start_date'),
                'route_id': trip.get('route_id'),
                'stop_id': v.get('stop_id'),
                'current_status': v.get('current_status'),  # STOPPED_AT, IN_TRANSIT_TO, etc.
                'current_stop_sequence': v.get('current_stop_sequence')
            })
            
            # Parse vehicle timestamp (when vehicle sensor recorded this position)
            ts = v.get('timestamp')
            if ts:
                try:
                    dt = datetime.datetime.fromtimestamp(int(ts), tz=datetime.timezone.utc)
                    r['vehicle_timestamp'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    pass
            yield {k: r.get(k) for k in REQUIRED_FIELDS}

# ============================================
# Beam DoFn for Parsing Pub/Sub Messages
# ============================================
class ParseAndFlatten(beam.DoFn):
    """
    DoFn that parses Pub/Sub messages and flattens GTFS-RT data.
    
    Input: Pub/Sub message with JSON payload
    Output: Flattened transit records (generator)
    """
    def process(self, element):
        # Decode Pub/Sub message payload
        data = element.data.decode('utf-8')
        parsed = json.loads(data)
        
        # Add processing timestamp for debugging/monitoring
        parsed['dataflow_processing_timestamp'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # Flatten nested GTFS structure into row-level records
        yield from flatten_gtfs(parsed)

# ============================================
# Main Pipeline Function
# ============================================
def run():
    """
    Dataflow streaming pipeline that:
    1. Reads MTA GTFS-RT updates from Pub/Sub
    2. Flattens nested protobuf structure
    3. Enriches with stop metadata from GCS
    4. Writes to BigQuery in real-time
    """
    # Configure pipeline options
    options = PipelineOptions(
        streaming=True,
        project=PROJECT_ID,
        region=REGION,
        runner='DataflowRunner',
        temp_location="gs://<your-project-id>-dataflow-temp",
        staging_location="gs://<your-project-id>-dataflow-staging",
        num_workers=2,
        max_num_workers=5,
        worker_machine_type='n2-highmem-16',
        job_name='<your-project-id>-dataflow-streaming-pipeline'
    )
    options.view_as(StandardOptions).streaming = True
    options.view_as(SetupOptions).save_main_session = True

    with beam.Pipeline(options=options) as p:
        # ============================================
        # Side Input: Load Stop Metadata from GCS
        # ============================================
        # This creates a dictionary for O(1) lookup during enrichment
        stops_map_pc = (
            p
            # Read CSV file from GCS (one line per stop)
            | 'Read stops CSV' >> beam.io.ReadFromText(GCS_STOPS_CSV_PATH)
            # Parse each CSV line using Python's csv.reader (handles quoted fields)
            | 'Parse stops CSV' >> beam.Map(lambda line: next(csv.reader([line])) if line and line.strip() else None)
            # Filter out invalid rows (None, short rows, header row)
            | 'Filter valid stops' >> beam.Filter(lambda row: row and len(row) >= 4 and row[0].lower() != 'stop_id')
            # Convert to (stop_id, metadata) tuples for dictionary conversion
            # CSV format: stop_id, stop_name, stop_lat, stop_lon
            | 'To stops map' >> beam.Map(lambda row: (row[0].strip(), {'stop_name': row[1].strip(), 'stop_lat': row[2].strip(), 'stop_lon': row[3].strip()}))
        )

        # ============================================
        # Main Pipeline: Process MTA Updates
        # ============================================
        (
            p
            # Read from Pub/Sub subscription (MTA updates arrive here every ~15 seconds)
            | 'ReadFromPubSub' >> beam.io.ReadFromPubSub(
                subscription=f"projects/{PROJECT_ID}/subscriptions/{PUBSUB_SUBSCRIPTION}",
                with_attributes=True
            )
            # Parse JSON and flatten GTFS-RT structure into individual records
            | 'ParseAndFlatten' >> beam.ParDo(ParseAndFlatten())
            # Apply windowing strategy for batch processing
            | 'WindowIntoFixedWindows' >> beam.WindowInto(
                                            beam.window.FixedWindows(30),  # 30-second windows (captures ~2 MTA updates)
                                            trigger=beam.trigger.AfterAny(
                                                beam.trigger.AfterProcessingTime(5),  # Trigger after 5 seconds
                                                beam.trigger.AfterPane(1)  # Or after first element (low latency)
                                            ),
                                            accumulation_mode=beam.trigger.AccumulationMode.DISCARDING,
                                            allowed_lateness=10  # Allow 10 seconds for late-arriving data
  )
            # Filter to only vehicle position updates (ignore trip_updates without current_status)
            | 'FilterCurrentStatus' >> beam.Filter(lambda r: r.get('current_status'))
            # Enrich with stop metadata (name, coordinates, direction)
            | 'EnrichWithStops' >> beam.Map(
                enrich_with_stops,
                stops_map=beam.pvalue.AsDict(stops_map_pc)  # Side input as dictionary
            )
            # Write enriched records to BigQuery
            | 'WriteToBigQuery' >> beam.io.WriteToBigQuery(
                BIGQUERY_TABLE,
                schema=BIGQUERY_SCHEMA,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                method=beam.io.WriteToBigQuery.Method.STREAMING_INSERTS
            )
        )

if __name__ == "__main__":
    run()
