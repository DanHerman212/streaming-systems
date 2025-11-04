-- ============================================
-- Average Time Between Trains Analysis
-- ============================================
-- Purpose: Calculate average wait time between consecutive train arrivals at each station
-- Use Case: Service frequency analysis, identify stations with poor service intervals
-- Metric: Average minutes between trains (headway)
-- Date: 2025-10-31 (single day analysis)
-- ============================================

WITH
  TripArrivals AS (
    -- Step 1: Get the first arrival time for each unique trip at each station
    -- This represents when a train first arrives at a station (ignores subsequent updates while stopped)
    SELECT
      stop_name,
      DATE(vehicle_timestamp, 'America/New_York') AS event_date,
      trip_id,
      MIN(vehicle_timestamp) AS trip_arrival_time  -- First update = arrival time
    FROM
      `<Your-project-id>`.mta_updates.realtime_updates
    WHERE
      vehicle_timestamp IS NOT NULL
      AND stop_name IS NOT NULL
      AND DATE(vehicle_timestamp, 'America/New_York') = '2025-10-31'  -- Filter to specific date
    GROUP BY stop_name, DATE(vehicle_timestamp, 'America/New_York'), trip_id
  ),
  CalculatedArrivalLags AS (
    -- Step 2: Calculate time difference between consecutive train arrivals at each station
    SELECT
      stop_name,
      event_date,
      trip_arrival_time AS current_trip_arrival_time,
      -- Get the previous train's arrival time at this station
      LAG(trip_arrival_time) OVER (
        PARTITION BY stop_name, event_date
        ORDER BY trip_arrival_time
      ) AS prev_trip_arrival_time,
      -- Calculate minutes between this train and the previous train
      TIMESTAMP_DIFF(
        trip_arrival_time, 
        LAG(trip_arrival_time) OVER (
          PARTITION BY stop_name, event_date
          ORDER BY trip_arrival_time
        ), 
        MINUTE
      ) AS minute_difference_between_trains
    FROM
      TripArrivals
  )
-- Step 3: Aggregate wait times by station and count total trips
SELECT
  cal.stop_name,
  -- Average wait time (headway) between trains in minutes
  ROUND(AVG(cal.minute_difference_between_trains), 2) AS average_min_difference_between_trains,
  -- Total number of unique trains that stopped at this station
  COUNT(DISTINCT ta.trip_id) AS total_unique_trip_ids
FROM
  CalculatedArrivalLags AS cal
  JOIN
  TripArrivals AS ta
  ON cal.stop_name = ta.stop_name AND cal.current_trip_arrival_time = ta.trip_arrival_time
WHERE
  cal.prev_trip_arrival_time IS NOT NULL  -- Exclude first train of the day (no previous train)
  AND cal.minute_difference_between_trains <= 20  -- Filter out unrealistic gaps (> 20 min likely service disruption)
GROUP BY cal.stop_name
ORDER BY average_min_difference_between_trains DESC;  -- Stations with longest wait times first