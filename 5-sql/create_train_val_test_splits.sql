-- ============================================
-- Create Train/Validation/Test Splits
-- Strategy: Temporal split (70% train, 15% val, 15% test)
-- ============================================

-- Get date boundaries for splits
CREATE OR REPLACE TABLE `streaming-systems-245.mta_historical.split_dates` AS
WITH DateStats AS (
  SELECT
    MIN(trip_date) AS min_date,
    MAX(trip_date) AS max_date,
    DATE_DIFF(MAX(trip_date), MIN(trip_date), DAY) AS total_days
  FROM `streaming-systems-245.mta_historical.e_train_training_samples`
)
SELECT
  min_date,
  max_date,
  total_days,
  DATE_ADD(min_date, INTERVAL CAST(total_days * 0.70 AS INT64) DAY) AS train_end_date,
  DATE_ADD(min_date, INTERVAL CAST(total_days * 0.85 AS INT64) DAY) AS val_end_date
FROM DateStats;

-- Display split information
SELECT
  '═══════════════════════════════════════════════════' AS info
UNION ALL
SELECT 'DATA SPLIT SUMMARY'
UNION ALL
SELECT '═══════════════════════════════════════════════════'
UNION ALL
SELECT ''
UNION ALL
SELECT CONCAT('Full date range: ', CAST(min_date AS STRING), ' to ', CAST(max_date AS STRING))
FROM `streaming-systems-245.mta_historical.split_dates`
UNION ALL
SELECT CONCAT('Total days: ', CAST(total_days AS STRING))
FROM `streaming-systems-245.mta_historical.split_dates`
UNION ALL
SELECT ''
UNION ALL
SELECT CONCAT('TRAIN:      ', CAST(min_date AS STRING), ' to ', CAST(train_end_date AS STRING))
FROM `streaming-systems-245.mta_historical.split_dates`
UNION ALL
SELECT CONCAT('VALIDATION: ', CAST(DATE_ADD(train_end_date, INTERVAL 1 DAY) AS STRING), ' to ', CAST(val_end_date AS STRING))
FROM `streaming-systems-245.mta_historical.split_dates`
UNION ALL
SELECT CONCAT('TEST:       ', CAST(DATE_ADD(val_end_date, INTERVAL 1 DAY) AS STRING), ' to ', CAST(max_date AS STRING))
FROM `streaming-systems-245.mta_historical.split_dates`
UNION ALL
SELECT ''
UNION ALL
SELECT '--- Sample Counts ---'
UNION ALL
SELECT CONCAT('Train samples: ', CAST(
  (SELECT COUNT(*) FROM `streaming-systems-245.mta_historical.e_train_training_samples` samples, `streaming-systems-245.mta_historical.split_dates` dates
   WHERE samples.trip_date >= dates.min_date AND samples.trip_date <= dates.train_end_date)
AS STRING))
UNION ALL
SELECT CONCAT('Val samples: ', CAST(
  (SELECT COUNT(*) FROM `streaming-systems-245.mta_historical.e_train_training_samples` samples, `streaming-systems-245.mta_historical.split_dates` dates
   WHERE samples.trip_date > dates.train_end_date AND samples.trip_date <= dates.val_end_date)
AS STRING))
UNION ALL
SELECT CONCAT('Test samples: ', CAST(
  (SELECT COUNT(*) FROM `streaming-systems-245.mta_historical.e_train_training_samples` samples, `streaming-systems-245.mta_historical.split_dates` dates
   WHERE samples.trip_date > dates.val_end_date AND samples.trip_date <= dates.max_date)
AS STRING))
UNION ALL
SELECT '═══════════════════════════════════════════════════';
