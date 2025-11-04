-- ============================================
-- Average Idle Time By Station Analysis
-- ============================================
-- Purpose: Calculate the average time trains spend idle (stopped) at each station
-- Use Case: Identify stations with longer dwell times, potential bottlenecks
-- Direction: Southbound trains only
-- ============================================

WITH
  time_diffs AS (
    -- Step 1: Calculate time differences between consecutive updates for the same train at the same station
    SELECT
      stop_name,
      stop_lat,
      stop_lon,
      trip_id,
      -- Convert timestamps to NYC timezone for accurate daily analysis
      DATE(vehicle_timestamp, 'America/New_York') AS trip_date,
      TIME(vehicle_timestamp, 'America/New_York') AS trip_time,
      -- Get the previous timestamp for this train at this station
      LAG(TIME(vehicle_timestamp, 'America/New_York')) OVER (
        PARTITION BY stop_name, trip_id, DATE(vehicle_timestamp, 'America/New_York')
        ORDER BY vehicle_timestamp
      ) AS prev_trip_time,
      -- Calculate seconds since last update for this train at this station
      CASE
        -- If timestamps are identical (duplicate updates), default to 60 seconds
        WHEN TIME(vehicle_timestamp, 'America/New_York') = LAG(TIME(vehicle_timestamp, 'America/New_York')) OVER (
          PARTITION BY stop_name, trip_id, DATE(vehicle_timestamp, 'America/New_York')
          ORDER BY vehicle_timestamp
        ) THEN 60
        -- Otherwise, calculate actual time difference in seconds
        ELSE TIMESTAMP_DIFF(
          vehicle_timestamp, 
          LAG(vehicle_timestamp) OVER (
            PARTITION BY stop_name, trip_id, DATE(vehicle_timestamp, 'America/New_York')
            ORDER BY vehicle_timestamp
          ), 
          SECOND
        )
      END AS seconds_since_last
    FROM
      `<Your-project-ID>`.mta_updates.realtime_updates
    WHERE
      direction = "Southbound" 
      AND stop_name IS NOT NULL  -- Exclude records with missing station names
  )
-- Step 2: Aggregate idle times by station and format as MM:SS
SELECT
  stop_name,
  stop_lat,
  stop_lon,
  -- Format average idle time as "minutes:seconds" (e.g., "2:30" for 2 minutes 30 seconds)
  CONCAT(
    CAST(FLOOR(AVG(seconds_since_last) / 60) AS STRING),  -- Minutes
    ':', 
    LPAD(
      CAST(MOD(CAST(ROUND(AVG(seconds_since_last)) AS INT64), 60) AS STRING),  -- Seconds
      2, 
      '0'
    )
  ) AS avg_idle_time_m_s
FROM
  time_diffs
WHERE
  seconds_since_last IS NOT NULL 
    AND seconds_since_last <= 300  -- Filter out unrealistic gaps (> 5 minutes = not idle, likely movement)
    AND stop_name != "Broad Channel"  -- Exclude Broad Channel (outlier station)
GROUP BY stop_name, stop_lat, stop_lon
ORDER BY avg_idle_time_m_s DESC  -- Stations with longest idle times first
