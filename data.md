# Data Dictionary
| Column Name | Data Type | Description |
|---|---|---|
| `feed_header_timestamp` | `TIMESTAMP` | Message timestamp coming directly from MTA GTFS |
| `trip_id` | `STRING` | Combines origin time, route id, path identifier and direction. |
| `start_time` | `STRING` | Scheduled start time of the trip. |
| `start_date` | `STRING` | Scheduled start date of the trip. |
| `route_id` | `STRING` | Public identifier for each train route. |
| `stop_id` | `STRING` | Unique identifier for a subway stop. |
| `vehicle_timestamp` | `TIMESTAMP` | Timestamp from vehicle sensor in closest subway station. |
| `current_status` | `STRING` | Current operational status of the vehicle. |
| `current_stop_sequence` | `INTEGER` | The sequence number of the stop within the trip. |
| `stop_name` | `STRING` | Human-readable name of the subway stop. |
| `stop_lat` | `FLOAT` | Latitude coordinate of the subway stop. |
| `stop_lon` | `FLOAT` | Longitude coordinate of the subway stop. |
| `direction` | `STRING` | Direction of travel for the trip (e.g., "Northbound", "Southbound"). |