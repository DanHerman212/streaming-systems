import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions, SetupOptions
import datetime
import json
import csv
import pytz

PROJECT_ID = "streaming-systems-245"
BIGQUERY_DATASET = "mta_updates"
BIGQUERY_TABLE = "streaming-systems-245.mta_updates.realtime_updates"
PUBSUB_SUBSCRIPTION = "mta-gtfs-ace-sub"
GCS_STOPS_CSV_PATH = "gs://dataflow-enrichment-bucket-245/stops.csv"
FEED_TZ = pytz.timezone('America/New_York')

REQUIRED_FIELDS = [
    'unique_event_id', 'feed_header_timestamp', 'entity_id', 'trip_id', 'start_time', 'start_date',
    'route_id', 'stop_id', 'vehicle_timestamp', 'current_status', 'current_stop_sequence',
    'stop_name', 'stop_lat', 'stop_lon', 'direction'
]

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

def enrich_with_stops(rec: dict, stops_map):
    sid = rec.get('stop_id')
    if not sid:
        rec.update({'stop_name': None, 'stop_lat': None, 'stop_lon': None, 'direction': None})
        return {k: rec.get(k) for k in REQUIRED_FIELDS}
    sid_processed = str(sid).strip()
    info = stops_map.get(sid_processed) or stops_map.get(sid_processed.upper())
    if not info and sid_processed and sid_processed[-1].isalpha():
        info = stops_map.get(sid_processed[:-1]) or stops_map.get(sid_processed[:-1].upper())
    rec['stop_name'] = info.get('stop_name') if info else None
    try:
        rec['stop_lat'] = float(info.get('stop_lat')) if info and info.get('stop_lat') else None
    except ValueError:
        rec['stop_lat'] = None
    try:
        rec['stop_lon'] = float(info.get('stop_lon')) if info and info.get('stop_lon') else None
    except ValueError:
        rec['stop_lon'] = None
    rec['direction'] = 'Southbound' if sid_processed and 'S' in sid_processed else 'Northbound'
    return {k: rec.get(k) for k in REQUIRED_FIELDS}

def flatten_gtfs(obj):
    header = obj.get('header', {})
    entities = obj.get('entity', [])
    feed_header_timestamp = None
    ts = header.get('timestamp')
    if ts:
        try:
            dt = datetime.datetime.fromtimestamp(int(ts), tz=datetime.timezone.utc)
            feed_header_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
    unique_event_id = obj.get('unique_event_id')
    for ent in entities:
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
        if 'trip_update' in ent:
            trip = ent['trip_update'].get('trip', {})
            base.update({
                'trip_id': trip.get('trip_id'),
                'start_time': trip.get('start_time'),
                'start_date': trip.get('start_date'),
                'route_id': trip.get('route_id')
            })
            for su in ent['trip_update'].get('stop_time_update', []) or []:
                r = dict(base)
                r['stop_id'] = su.get('stop_id')
                yield {k: r.get(k) for k in REQUIRED_FIELDS}
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
                'current_status': v.get('current_status'),
                'current_stop_sequence': v.get('current_stop_sequence')
            })
            ts = v.get('timestamp')
            if ts:
                try:
                    dt = datetime.datetime.fromtimestamp(int(ts), tz=datetime.timezone.utc)
                    r['vehicle_timestamp'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    pass
            yield {k: r.get(k) for k in REQUIRED_FIELDS}

class ParseAndFlatten(beam.DoFn):
    def process(self, element):
        data = element.data.decode('utf-8')
        parsed = json.loads(data)
        parsed['dataflow_processing_timestamp'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        yield from flatten_gtfs(parsed)

def run():
    options = PipelineOptions(
        streaming=True,
        project=PROJECT_ID,
        region='us-east1',
        runner='DataflowRunner',
        temp_location='gs://streaming-systems-245-dataflow-temp',
        staging_location='gs://streaming-systems-245-dataflow-temp',
        num_workers=2,
        max_num_workers=5,
        worker_machine_type='n2-highmem-16',
        job_name='dataflow-1029-optimized-w10-3mpm'
    )
    options.view_as(StandardOptions).streaming = True
    options.view_as(SetupOptions).save_main_session = True

    with beam.Pipeline(options=options) as p:
        stops_map_pc = (
            p
            | 'Read stops CSV' >> beam.io.ReadFromText(GCS_STOPS_CSV_PATH)
            | 'Parse stops CSV' >> beam.Map(lambda line: next(csv.reader([line])) if line and line.strip() else None)
            | 'Filter valid stops' >> beam.Filter(lambda row: row and len(row) >= 4 and row[0].lower() != 'stop_id')
            | 'To stops map' >> beam.Map(lambda row: (row[0].strip(), {'stop_name': row[1].strip(), 'stop_lat': row[2].strip(), 'stop_lon': row[3].strip()}))
        )

        (
            p
            | 'ReadFromPubSub' >> beam.io.ReadFromPubSub(
                subscription=f"projects/{PROJECT_ID}/subscriptions/{PUBSUB_SUBSCRIPTION}",
                with_attributes=True
            )
            | 'ParseAndFlatten' >> beam.ParDo(ParseAndFlatten())
            | 'WindowIntoFixedWindows' >> beam.WindowInto(
                                            beam.window.FixedWindows(10),
                                            trigger=beam.trigger.AfterAny(
                                                beam.trigger.AfterProcessingTime(5),
                                                beam.trigger.AfterCount(50)
                                            ),
                                            accumulation_mode=beam.trigger.AccumulationMode.DISCARDING
  )
            | 'FilterCurrentStatus' >> beam.Filter(lambda r: r.get('current_status'))
            | 'EnrichWithStops' >> beam.Map(
                enrich_with_stops,
                stops_map=beam.pvalue.AsDict(stops_map_pc)
            )
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
