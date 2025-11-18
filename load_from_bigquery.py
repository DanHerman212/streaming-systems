#!/usr/bin/env python3
"""
Load training data directly from BigQuery into TensorFlow datasets.
No intermediate files needed - streams data on-demand.
Best for production environments.
"""

import tensorflow as tf
import tensorflow_io as tfio

# Configuration
PROJECT_ID = "streaming-systems-245"
DATASET_ID = "mta_historical"
TABLE_ID = "e_train_training_samples"

def create_bq_dataset(split_filter, batch_size=32):
    """
    Create TensorFlow dataset directly from BigQuery.
    
    Args:
        split_filter: SQL WHERE clause for train/val/test split
        batch_size: Batch size for training
    """
    
    # Query to flatten the context_stops array into features
    query = f"""
    SELECT
      -- Target variable
      target_minutes_from_prev,
      
      -- Flatten context stops (5 stops x 8 features = 40 features)
      context_stops[OFFSET(0)].hour_of_day AS ctx0_hour,
      context_stops[OFFSET(0)].day_of_week AS ctx0_day,
      context_stops[OFFSET(0)].is_rush_hour AS ctx0_rush,
      context_stops[OFFSET(0)].is_weekend AS ctx0_weekend,
      context_stops[OFFSET(0)].minutes_since_prev_stop AS ctx0_minutes,
      context_stops[OFFSET(0)].stop_lat AS ctx0_lat,
      context_stops[OFFSET(0)].stop_lon AS ctx0_lon,
      context_stops[OFFSET(0)].stop_sequence AS ctx0_seq,
      
      context_stops[OFFSET(1)].hour_of_day AS ctx1_hour,
      context_stops[OFFSET(1)].day_of_week AS ctx1_day,
      context_stops[OFFSET(1)].is_rush_hour AS ctx1_rush,
      context_stops[OFFSET(1)].is_weekend AS ctx1_weekend,
      context_stops[OFFSET(1)].minutes_since_prev_stop AS ctx1_minutes,
      context_stops[OFFSET(1)].stop_lat AS ctx1_lat,
      context_stops[OFFSET(1)].stop_lon AS ctx1_lon,
      context_stops[OFFSET(1)].stop_sequence AS ctx1_seq,
      
      context_stops[OFFSET(2)].hour_of_day AS ctx2_hour,
      context_stops[OFFSET(2)].day_of_week AS ctx2_day,
      context_stops[OFFSET(2)].is_rush_hour AS ctx2_rush,
      context_stops[OFFSET(2)].is_weekend AS ctx2_weekend,
      context_stops[OFFSET(2)].minutes_since_prev_stop AS ctx2_minutes,
      context_stops[OFFSET(2)].stop_lat AS ctx2_lat,
      context_stops[OFFSET(2)].stop_lon AS ctx2_lon,
      context_stops[OFFSET(2)].stop_sequence AS ctx2_seq,
      
      context_stops[OFFSET(3)].hour_of_day AS ctx3_hour,
      context_stops[OFFSET(3)].day_of_week AS ctx3_day,
      context_stops[OFFSET(3)].is_rush_hour AS ctx3_rush,
      context_stops[OFFSET(3)].is_weekend AS ctx3_weekend,
      context_stops[OFFSET(3)].minutes_since_prev_stop AS ctx3_minutes,
      context_stops[OFFSET(3)].stop_lat AS ctx3_lat,
      context_stops[OFFSET(3)].stop_lon AS ctx3_lon,
      context_stops[OFFSET(3)].stop_sequence AS ctx3_seq,
      
      context_stops[OFFSET(4)].hour_of_day AS ctx4_hour,
      context_stops[OFFSET(4)].day_of_week AS ctx4_day,
      context_stops[OFFSET(4)].is_rush_hour AS ctx4_rush,
      context_stops[OFFSET(4)].is_weekend AS ctx4_weekend,
      context_stops[OFFSET(4)].minutes_since_prev_stop AS ctx4_minutes,
      context_stops[OFFSET(4)].stop_lat AS ctx4_lat,
      context_stops[OFFSET(4)].stop_lon AS ctx4_lon,
      context_stops[OFFSET(4)].stop_sequence AS ctx4_seq
      
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    WHERE {split_filter}
    ORDER BY trip_date, trip_uid
    """
    
    # Create dataset from BigQuery
    feature_names = ['target_minutes_from_prev'] + [
        f'ctx{i}_{feat}' 
        for i in range(5) 
        for feat in ['hour', 'day', 'rush', 'weekend', 'minutes', 'lat', 'lon', 'seq']
    ]
    
    dataset = tfio.experimental.columnar.make_csv_dataset(
        query,
        batch_size=batch_size,
        column_names=feature_names,
        reader='bigquery',
        project_id=PROJECT_ID
    )
    
    # Reshape into (batch, 5, 8) format
    def reshape_features(features):
        # Extract target
        y = features.pop('target_minutes_from_prev')
        
        # Stack context features into (batch, 5, 8) tensor
        X_list = []
        for i in range(5):
            timestep = tf.stack([
                tf.cast(features[f'ctx{i}_hour'], tf.float32),
                tf.cast(features[f'ctx{i}_day'], tf.float32),
                tf.cast(features[f'ctx{i}_rush'], tf.float32),
                tf.cast(features[f'ctx{i}_weekend'], tf.float32),
                tf.cast(features[f'ctx{i}_minutes'], tf.float32),
                tf.cast(features[f'ctx{i}_lat'], tf.float32),
                tf.cast(features[f'ctx{i}_lon'], tf.float32),
                tf.cast(features[f'ctx{i}_seq'], tf.float32)
            ], axis=1)
            X_list.append(timestep)
        
        X = tf.stack(X_list, axis=1)  # (batch, 5, 8)
        return X, y
    
    dataset = dataset.map(reshape_features)
    return dataset


def load_datasets_from_bigquery():
    """Load train/val/test splits directly from BigQuery."""
    
    # Get split dates from BigQuery
    from google.cloud import bigquery
    client = bigquery.Client(project=PROJECT_ID)
    
    split_query = """
    SELECT train_end_date, val_end_date
    FROM `streaming-systems-245.mta_historical.split_dates`
    """
    split_df = client.query(split_query).to_dataframe()
    train_end = split_df['train_end_date'].iloc[0]
    val_end = split_df['val_end_date'].iloc[0]
    
    print(f"Loading datasets from BigQuery...")
    print(f"  Train: up to {train_end}")
    print(f"  Val:   {train_end} to {val_end}")
    print(f"  Test:  after {val_end}")
    
    # Create datasets with appropriate filters
    train_ds = create_bq_dataset(
        f"trip_date <= DATE('{train_end}')",
        batch_size=32
    ).shuffle(1000).prefetch(tf.data.AUTOTUNE)
    
    val_ds = create_bq_dataset(
        f"trip_date > DATE('{train_end}') AND trip_date <= DATE('{val_end}')",
        batch_size=32
    ).prefetch(tf.data.AUTOTUNE)
    
    test_ds = create_bq_dataset(
        f"trip_date > DATE('{val_end}')",
        batch_size=32
    ).prefetch(tf.data.AUTOTUNE)
    
    print("✅ Datasets created!")
    print("   Input shape: (batch, 5, 8)")
    
    return train_ds, val_ds, test_ds


if __name__ == '__main__':
    train_ds, val_ds, test_ds = load_datasets_from_bigquery()
    
    # Test by fetching one batch
    for X_batch, y_batch in train_ds.take(1):
        print(f"\nSample batch:")
        print(f"  X shape: {X_batch.shape}")
        print(f"  y shape: {y_batch.shape}")
        print(f"  Target mean: {tf.reduce_mean(y_batch).numpy():.2f} min")
