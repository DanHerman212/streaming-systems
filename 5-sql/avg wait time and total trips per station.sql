WITH
  TripArrivals AS (
    SELECT
      stop_name,
      DATE(vehicle_timestamp, 'America/New_York') AS event_date,
      trip_id,
      MIN(vehicle_timestamp) AS trip_arrival_time
    FROM
      `streaming-systems-245`.mta_updates.realtime_updates
    WHERE
      vehicle_timestamp IS NOT NULL AND stop_name IS NOT NULL
    GROUP BY stop_name, DATE(vehicle_timestamp, 'America/New_York'), trip_id
  ),
  CalculatedArrivalLags AS (
    SELECT
      stop_name,
      event_date,
      trip_arrival_time AS current_trip_arrival_time,
      LAG(trip_arrival_time) OVER (PARTITION BY stop_name, event_date
        ORDER BY trip_arrival_time) AS prev_trip_arrival_time,
      TIMESTAMP_DIFF(trip_arrival_time, LAG(trip_arrival_time) OVER (PARTITION BY stop_name, event_date
          ORDER BY trip_arrival_time), MINUTE) AS minute_difference_between_trains
    FROM
      TripArrivals
  )
SELECT
  cal.stop_name,
  ROUND(AVG(cal.minute_difference_between_trains), 2) AS average_min_difference_between_trains,
  COUNT(DISTINCT ta.trip_id) AS total_unique_trip_ids
FROM
  CalculatedArrivalLags AS cal
  JOIN
  TripArrivals AS ta
  ON cal.stop_name = ta.stop_name AND cal.current_trip_arrival_time = ta.trip_arrival_time
WHERE
  cal.prev_trip_arrival_time IS NOT NULL AND cal.minute_difference_between_trains <= 20
GROUP BY cal.stop_name
ORDER BY average_min_difference_between_trains;
