# NYC Taxi Data Cleaning Script - Windows Compatible
# Reads train/train.csv and outputs cleaned_data.csv

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# Force UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Paths
INPUT_FILE = 'train/train.csv'
OUTPUT_DIR = 'data/raw/processed'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'cleaned_data.csv')

def create_output_directory():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"[+] Created directory: {OUTPUT_DIR}")

def load_data():
    """Load the raw CSV data"""
    print(f"\n[1] Loading data from {INPUT_FILE}...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] File not found at {INPUT_FILE}")
        print(f"        Please ensure train.csv exists in the train/ directory")
        sys.exit(1)
    
    try:
        df = pd.read_csv(INPUT_FILE)
        print(f"[+] Loaded {len(df):,} rows with {len(df.columns)} columns")
        return df
    except Exception as e:
        print(f"[ERROR] Error loading CSV: {e}")
        sys.exit(1)

def inspect_data(df):
    """Inspect the data structure"""
    print("\n[2] Data Inspection:")
    print(f"    Columns: {list(df.columns)}")
    print(f"\n    First few rows:")
    print(df.head(3))
    print(f"\n    Data types:")
    print(df.dtypes)
    print(f"\n    Missing values:")
    print(df.isnull().sum())

def clean_data(df):
    """Clean and prepare the data"""
    print("\n[3] Cleaning data...")
    
    initial_count = len(df)
    
    # Step 1: Standardize column names
    print("    -> Standardizing column names...")
    df.columns = df.columns.str.lower().str.strip()
    
    # Map common NYC taxi column names to our schema
    column_mapping = {
        'tpep_pickup_datetime': 'pickup_datetime',
        'tpep_dropoff_datetime': 'dropoff_datetime',
        'vendorid': 'vendor_id',
        'ratecodeid': 'rate_code_id',
        'pulocationid': 'pickup_location_id',
        'dolocationid': 'dropoff_location_id',
        'payment_type': 'payment_type',
        'fare_amount': 'fare_amount',
        'extra': 'extra',
        'mta_tax': 'mta_tax',
        'tip_amount': 'tip_amount',
        'tolls_amount': 'tolls_amount',
        'improvement_surcharge': 'improvement_surcharge',
        'total_amount': 'total_amount',
        'congestion_surcharge': 'congestion_surcharge'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Step 2: Handle datetime columns
    print("    -> Processing datetime columns...")
    
    datetime_cols = ['pickup_datetime', 'dropoff_datetime']
    for col in datetime_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Remove rows with invalid dates
    before_drop = len(df)
    df = df.dropna(subset=['pickup_datetime', 'dropoff_datetime'])
    if len(df) < before_drop:
        print(f"    [!] Dropped {before_drop - len(df):,} rows with invalid dates")
    
    # Step 3: Calculate trip_duration (in seconds)
    print("    -> Calculating trip duration...")
    df['trip_duration'] = (df['dropoff_datetime'] - df['pickup_datetime']).dt.total_seconds()
    
    # Filter invalid durations
    before_filter = len(df)
    df = df[
        (df['trip_duration'] > 60) &  # At least 1 minute
        (df['trip_duration'] < 86400)  # Less than 24 hours
    ]
    if len(df) < before_filter:
        print(f"    [!] Filtered {before_filter - len(df):,} rows with invalid duration")
    
    # Step 4: Handle trip_distance
    print("    -> Processing trip distance...")
    
    if 'trip_distance' in df.columns:
        df['trip_distance_miles'] = df['trip_distance']
    else:
        # If no distance column, we'll need to calculate from coordinates
        print("    [!] No trip_distance column found")
        df['trip_distance_miles'] = 0.0
    
    # Filter invalid distances
    before_filter = len(df)
    df = df[
        (df['trip_distance_miles'] >= 0) &
        (df['trip_distance_miles'] < 200)  # Less than 200 miles
    ]
    if len(df) < before_filter:
        print(f"    [!] Filtered {before_filter - len(df):,} rows with invalid distance")
    
    # Step 5: Handle location data
    print("    -> Processing location data...")
    
    # If we have location IDs but no coordinates, create dummy coordinates
    if 'pickup_location_id' in df.columns and 'pickup_longitude' not in df.columns:
        print("    [!] No coordinate columns found, creating default values...")
        # NYC approximate center
        df['pickup_longitude'] = -73.9712 + np.random.uniform(-0.1, 0.1, len(df))
        df['pickup_latitude'] = 40.7831 + np.random.uniform(-0.1, 0.1, len(df))
    
    # If we have coordinates, validate them
    if 'pickup_longitude' in df.columns and 'pickup_latitude' in df.columns:
        before_filter = len(df)
        df = df[
            (df['pickup_longitude'].between(-74.05, -73.75)) &  # NYC bounds
            (df['pickup_latitude'].between(40.63, 40.85))
        ]
        if len(df) < before_filter:
            print(f"    [!] Filtered {before_filter - len(df):,} rows outside NYC bounds")
    else:
        # Create default NYC coordinates if missing
        df['pickup_longitude'] = -73.9712
        df['pickup_latitude'] = 40.7831
    
    # Step 6: Handle vendor_id
    print("    -> Processing vendor ID...")
    if 'vendor_id' not in df.columns:
        df['vendor_id'] = 1
    else:
        df['vendor_id'] = df['vendor_id'].fillna(1).astype(int)
        df['vendor_id'] = df['vendor_id'].apply(lambda x: x if x in [1, 2] else 1)
    
    # Step 7: Handle passenger_count
    print("    -> Processing passenger count...")
    if 'passenger_count' not in df.columns:
        df['passenger_count'] = 1
    else:
        df['passenger_count'] = df['passenger_count'].fillna(1).astype(int)
        df['passenger_count'] = df['passenger_count'].clip(1, 6)
    
    # Step 8: Handle store_and_fwd_flag
    if 'store_and_fwd_flag' not in df.columns:
        df['store_and_fwd_flag'] = 'N'
    else:
        df['store_and_fwd_flag'] = df['store_and_fwd_flag'].fillna('N')
    
    # Step 9: Handle rate_code_id
    if 'rate_code_id' not in df.columns:
        df['rate_code_id'] = 1
    else:
        df['rate_code_id'] = df['rate_code_id'].fillna(1).astype(int)
    
    # Step 10: Generate unique IDs
    print("    -> Generating unique IDs...")
    df['id'] = [f"TRIP_{i:08d}" for i in range(len(df))]
    
    # Step 11: Remove duplicates
    before_dedup = len(df)
    df = df.drop_duplicates(subset=['pickup_datetime', 'dropoff_datetime', 
                                     'pickup_longitude', 'pickup_latitude'])
    if len(df) < before_dedup:
        print(f"    [!] Removed {before_dedup - len(df):,} duplicate rows")
    
    # Step 12: Final data quality check
    print("    -> Final quality check...")
    df = df[
        (df['trip_duration'] > 0) &
        (df['trip_distance_miles'] >= 0) &
        (df['passenger_count'] > 0)
    ]
    
    print(f"\n[+] Cleaned data: {len(df):,} rows (from {initial_count:,})")
    print(f"    Removed: {initial_count - len(df):,} rows ({((initial_count - len(df)) / initial_count * 100):.1f}%)")
    
    return df

def select_required_columns(df):
    """Select only the columns needed for the database"""
    print("\n[4] Selecting required columns...")
    
    required_columns = [
        'id',
        'vendor_id',
        'pickup_datetime',
        'dropoff_datetime',
        'passenger_count',
        'pickup_longitude',
        'pickup_latitude',
        'rate_code_id',
        'store_and_fwd_flag',
        'trip_duration',
        'trip_distance_miles'
    ]
    
    # Only keep columns that exist
    columns_to_keep = [col for col in required_columns if col in df.columns]
    df_clean = df[columns_to_keep].copy()
    
    print(f"[+] Selected {len(columns_to_keep)} columns")
    
    return df_clean

def save_cleaned_data(df):
    """Save the cleaned data to CSV"""
    print(f"\n[5] Saving cleaned data to {OUTPUT_FILE}...")
    
    try:
        df.to_csv(OUTPUT_FILE, index=False)
        file_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)  # MB
        print(f"[+] Saved {len(df):,} rows to {OUTPUT_FILE}")
        print(f"    File size: {file_size:.2f} MB")
    except Exception as e:
        print(f"[ERROR] Error saving file: {e}")
        sys.exit(1)

def generate_summary(df):
    """Generate a summary of the cleaned data"""
    print("\n[6] Data Summary:")
    print(f"    Total records: {len(df):,}")
    print(f"    Date range: {df['pickup_datetime'].min()} to {df['pickup_datetime'].max()}")
    print(f"    Avg trip duration: {df['trip_duration'].mean():.2f} seconds ({df['trip_duration'].mean() / 60:.2f} minutes)")
    print(f"    Avg trip distance: {df['trip_distance_miles'].mean():.2f} miles")
    print(f"\n    Vendor distribution:")
    print(df['vendor_id'].value_counts().to_string())
    print(f"\n    Passenger count distribution:")
    print(df['passenger_count'].value_counts().sort_index().to_string())

# MAIN EXECUTION

if __name__ == "__main__":
    print("=" * 60)
    print("NYC TAXI DATA CLEANING SCRIPT")
    print("=" * 60)
    
    try:
        # Step 1: Create output directory
        create_output_directory()
        
        # Step 2: Load raw data
        df = load_data()
        
        # Step 3: Inspect data (optional - comment out for large files)
        if len(df) < 1000000:  # Only inspect if less than 1M rows
            inspect_data(df)
        
        # Step 4: Clean data
        df_cleaned = clean_data(df)
        
        # Step 5: Select required columns
        df_final = select_required_columns(df_cleaned)
        
        # Step 6: Generate summary
        generate_summary(df_final)
        
        # Step 7: Save cleaned data
        save_cleaned_data(df_final)
        
        print("\n" + "=" * 60)
        print("DATA CLEANING COMPLETE!")
        print("=" * 60)
        print(f"\nNext step: Run the data loading script:")
        print(f"   python scripts/load_data.py")
        
    except KeyboardInterrupt:
        print("\n\n[!] Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)