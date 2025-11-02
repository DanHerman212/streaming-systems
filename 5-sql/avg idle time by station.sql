WITH
  time_diffs AS (
    SELECT
      stop_name,
      stop_lat,
      stop_lon,
      trip_id,
      DATE(vehicle_timestamp, 'America/New_York') AS trip_date,
      TIME(vehicle_timestamp, 'America/New_York') AS trip_time,
      LAG(TIME(vehicle_timestamp, 'America/New_York')) OVER (PARTITION BY stop_name, trip_id, DATE(vehicle_timestamp,
          'America/New_York')
        ORDER BY vehicle_timestamp) AS prev_trip_time,
      CASE
        WHEN TIME(vehicle_timestamp, 'America/New_York') = LAG(TIME(vehicle_timestamp, 'America/New_York')) OVER (PARTITION BY
          stop_name, trip_id, DATE(vehicle_timestamp, 'America/New_York')
          ORDER BY vehicle_timestamp) THEN 60
        ELSE TIMESTAMP_DIFF(vehicle_timestamp, LAG(vehicle_timestamp) OVER (PARTITION BY stop_name, trip_id,
            DATE(vehicle_timestamp, 'America/New_York')
            ORDER BY vehicle_timestamp), SECOND)
      END AS seconds_since_last
    FROM
      `streaming-systems-245`.mta_updates.realtime_updates
    WHERE
      direction = "Southbound" AND stop_name IS NOT NULL
  )
SELECT
  stop_name,
  stop_lat,
  stop_lon,
  CONCAT(CAST(FLOOR(AVG(seconds_since_last) / 60) AS STRING), ':', LPAD(CAST(MOD(CAST(ROUND(AVG(seconds_since_last)) AS INT64),
        60) AS STRING), 2, '0')) AS avg_idle_time_m_s
FROM
  time_diffs
WHERE
  seconds_since_last IS NOT NULL 
    AND seconds_since_last <= 300
    AND stop_name != "Broad Channel"
GROUP BY stop_name, stop_lat, stop_lon
ORDER BY avg_idle_time_m_s DESC
