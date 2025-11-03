# DATA DICTIONARY

| Column Name | Data Type | Description | Primary Key/Foreign Key | Nullable | Example Values |
|---|---|---|---|---|---|
| `feed_header_timestamp` | `TIMESTAMP` | Message timestamp coming directly from MTA GTFS | - | NO | "2025-10-24 13:59:58 UTC" |
| `trip_id` | `STRING` | Combines origin time, route id, path identifier and direction. | - | NO | "R12345.6789" |
| `start_time` | `STRING` | Scheduled start time of the trip. | - | NO | "14:00:00" |
| `start_date` | `STRING` | Scheduled start date of the trip. | - | NO | "20251024" |
| `route_id` | `STRING` | Public identifier for each train route. | - | NO | "A" |
| `stop_id` | `STRING` | Unique identifier for a subway stop. | - | NO | "A02" |
| `vehicle_timestamp` | `TIMESTAMP` | Timestamp from vehicle sensor in closest subway station. | - | NO | "2025-10-24 14:05:30 UTC" |
| `current_status` | `STRING` | Current operational status of the vehicle. | - | NO | "STOPPED_AT" |
| `current_stop_sequence` | `INTEGER` | The sequence number of the stop within the trip. | - | NO | 5 |
| `stop_name` | `STRING` | Human-readable name of the subway stop. | - | NO | "Fulton St" |
| `stop_lat` | `FLOAT` | Latitude coordinate of the subway stop. | - | NO | 40.7103 |
| `stop_lon` | `FLOAT` | Longitude coordinate of the subway stop. | - | NO | -74.0095 |
| `direction` | `STRING` | Direction of travel for the trip (e.g., "Northbound", "Southbound"). | - | NO | "Southbound" |