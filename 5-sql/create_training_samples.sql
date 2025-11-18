-- ============================================
-- Create training samples with 5-stop context window
-- ============================================

CREATE OR REPLACE TABLE `streaming-systems-245.mta_historical.e_train_training_samples` AS
WITH TargetStops AS (
  -- Get all Lexington Av/53 St arrivals
  SELECT
    trip_uid,
    start_time_dts,
    stop_sequence AS target_sequence,
    stop_name AS target_stop_name,
    arrival_time AS target_arrival_time,
    minutes_since_prev_stop AS target_minutes_from_prev,
    hour_of_day,
    day_of_week,
    trip_date,
    is_rush_hour,
    is_weekend
  FROM `streaming-systems-245.mta_historical.e_train_prepared`
  WHERE stop_name = 'Lexington Av/53 St'
),
ContextWindows AS (
  -- Collect the 5 previous stops for each target
  SELECT
    target.trip_uid,
    target.start_time_dts,
    target.target_stop_name,
    target.target_arrival_time,
    target.target_sequence,
    target.target_minutes_from_prev,
    target.hour_of_day,
    target.day_of_week,
    target.trip_date,
    target.is_rush_hour,
    target.is_weekend,
    
    -- Collect previous 5 stops as array
    ARRAY_AGG(
      STRUCT(
        prep.stop_sequence,
        prep.stop_name,
        prep.stop_lat,
        prep.stop_lon,
        prep.arrival_time,
        prep.minutes_since_prev_stop,
        prep.hour_of_day,
        prep.day_of_week,
        prep.is_rush_hour,
        prep.is_weekend
      ) ORDER BY prep.stop_sequence
    ) AS context_stops
    
  FROM TargetStops target
  INNER JOIN `streaming-systems-245.mta_historical.e_train_prepared` prep
    ON target.trip_uid = prep.trip_uid
    AND prep.stop_sequence < target.target_sequence  -- Previous stops only
    AND prep.stop_sequence >= target.target_sequence - 5  -- Last 5 stops
  GROUP BY
    target.trip_uid,
    target.start_time_dts,
    target.target_stop_name,
    target.target_arrival_time,
    target.target_sequence,
    target.target_minutes_from_prev,
    target.hour_of_day,
    target.day_of_week,
    target.trip_date,
    target.is_rush_hour,
    target.is_weekend
)
SELECT *
FROM ContextWindows
WHERE ARRAY_LENGTH(context_stops) = 5  -- Ensure full 5-stop context
ORDER BY trip_date, trip_uid;
