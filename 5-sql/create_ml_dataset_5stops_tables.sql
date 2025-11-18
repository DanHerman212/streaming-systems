-- ============================================
-- Create Training Dataset: E Train Southbound
-- Target: Predict arrival at "Lexington Av/53 St"
-- Context Window: 5 previous stops
-- ============================================

-- ============================================
-- Step 1: Filter and prepare E train data
-- ============================================
CREATE OR REPLACE TABLE `streaming-systems-245.mta_historical.e_train_prepared` AS
SELECT
  trip_uid,
  start_time_dts,
  route_id,
  direction,
  stop_id,
  stop_name,
  stop_lat,
  stop_lon,
  arrival_time,
  departure_time,
  
  -- Convert UTC to NYC timezone for feature extraction
  DATETIME(arrival_time, 'America/New_York') AS arrival_time_nyc,
  
  -- Sequence number within each trip
  ROW_NUMBER() OVER (PARTITION BY trip_uid ORDER BY arrival_time) AS stop_sequence,
  
  -- Calculate time since previous stop (in minutes)
  TIMESTAMP_DIFF(
    arrival_time,
    LAG(arrival_time) OVER (PARTITION BY trip_uid ORDER BY arrival_time),
    SECOND
  ) / 60.0 AS minutes_since_prev_stop,
  
  -- Extract temporal features (using NYC local time)
  EXTRACT(HOUR FROM DATETIME(arrival_time, 'America/New_York')) AS hour_of_day,
  EXTRACT(DAYOFWEEK FROM DATETIME(arrival_time, 'America/New_York')) AS day_of_week,
  EXTRACT(DATE FROM DATETIME(arrival_time, 'America/New_York')) AS trip_date,
  
  -- Rush hour indicator (7-9am, 4-7pm NYC time)
  CASE 
    WHEN EXTRACT(HOUR FROM DATETIME(arrival_time, 'America/New_York')) BETWEEN 7 AND 9 THEN 1
    WHEN EXTRACT(HOUR FROM DATETIME(arrival_time, 'America/New_York')) BETWEEN 16 AND 19 THEN 1
    ELSE 0
  END AS is_rush_hour,
  
  -- Weekend indicator
  CASE 
    WHEN EXTRACT(DAYOFWEEK FROM DATETIME(arrival_time, 'America/New_York')) IN (1, 7) THEN 1
    ELSE 0
  END AS is_weekend

FROM `streaming-systems-245.mta_historical.raw_data_v4`
WHERE 
  route_id = 'E'
  AND direction = 'S'  -- Southbound
  AND arrival_time IS NOT NULL
  AND stop_lat IS NOT NULL
  AND stop_lon IS NOT NULL
ORDER BY trip_uid, arrival_time;
