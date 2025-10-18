# NYC Taxi Data Load Script

import os
import sys
from datetime import datetime

import pandas as pd
import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME', 'nyc_taxi_db'),
    'user': os.getenv('DB_USER', 'frank'),
    'password': os.getenv('DB_PASSWORD', '')
}

# FEATURE ENGINEERING FUNCTIONS

def get_time_period(hour):
    """Return time period based on hour"""
    if pd.isna(hour):
        return None
    hour = int(hour)
    if 6 <= hour < 12:
        return 'Morning'
    elif 12 <= hour < 17:
        return 'Afternoon'
    elif 17 <= hour < 21:
        return 'Evening'
    else:
        return 'Night'

def get_distance_category(distance):
    """Categorize trip distance (in miles)"""
    if pd.isna(distance) or distance < 0:
        return None
    if distance < 1:
        return 'Short'
    elif distance < 5:
        return 'Medium'
    else:
        return 'Long'

def get_duration_category(duration):
    """Categorize trip duration in seconds"""
    if pd.isna(duration) or duration <= 0:
        return None
    minutes = duration / 60
    if minutes < 10:
        return 'Quick'
    elif minutes < 30:
        return 'Average'
    else:
        return 'Extended'

def calculate_speed(distance_miles, duration_seconds):
    """Calculate average speed (mph)"""
    if pd.isna(distance_miles) or pd.isna(duration_seconds) or duration_seconds == 0:
        return 0.0
    speed = distance_miles / (duration_seconds / 3600)
    # Cap unrealistic speeds (likely data errors)
    return min(speed, 120.0)


# DATA PREPARATION


def prepare_data(df):
    """Prepare dataframe with derived features"""
    print("\n Preparing derived features...")
    
    initial_count = len(df)
    
    # Schema expects: pickup_date (DATETIME) 
    # Handle different possible column names
    if 'tpep_dropoff_datetime' in df.columns:
        df['dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'], errors='coerce')
    elif 'dropoff_datetime' in df.columns:
        df['dropoff_datetime'] = pd.to_datetime(df['dropoff_datetime'], errors='coerce')
    else:
        print("Error: No dropoff_datetime column found!")
        sys.exit(1)
    
    # Create pickup_date from dropoff (or use pickup if available)
    if 'tpep_pickup_datetime' in df.columns:
        df['pickup_date'] = pd.to_datetime(df['tpep_pickup_datetime'], errors='coerce')
    elif 'pickup_datetime' in df.columns:
        df['pickup_date'] = pd.to_datetime(df['pickup_datetime'], errors='coerce')
    else:
        # Estimate pickup from dropoff minus duration
        df['pickup_date'] = df['dropoff_datetime'] - pd.to_timedelta(df['trip_duration'], unit='s')
    
    # Remove rows with invalid dates
    before_drop = len(df)
    df = df.dropna(subset=['pickup_date', 'dropoff_datetime'])
    if len(df) < before_drop:
        print(f"Dropped {before_drop - len(df)} rows with invalid dates")
    
    # Temporal features
    df['pickup_hour'] = df['pickup_date'].dt.hour
    df['pickup_day_of_week'] = df['pickup_date'].dt.dayofweek
    df['is_weekend'] = df['pickup_day_of_week'].isin([5, 6]).astype(int)
    df['time_period'] = df['pickup_hour'].apply(get_time_period)
    
    # Handle vendor_id (might be VendorID or vendor_id)
    if 'VendorID' in df.columns:
        df['vendor_id'] = df['VendorID'].astype(str)
    elif 'vendor_id' not in df.columns:
        df['vendor_id'] = '1'  # Default vendor
    else:
        df['vendor_id'] = df['vendor_id'].astype(str)
    
    # Ensure vendor_id is valid (only 1 or 2)
    df['vendor_id'] = df['vendor_id'].apply(lambda x: x if x in ['1', '2'] else '1')
    
    # Handle passenger_count
    if 'passenger_count' not in df.columns:
        df['passenger_count'] = 1
    df['passenger_count'] = pd.to_numeric(df['passenger_count'], errors='coerce').fillna(1).astype(int)
    df['passenger_count'] = df['passenger_count'].clip(1, 6)  # Valid range
    
    # Handle store_and_fwd_flag
    if 'store_and_fwd_flag' not in df.columns:
        df['store_and_fwd_flag'] = 'N'
    df['store_and_fwd_flag'] = df['store_and_fwd_flag'].fillna('N').astype(str)
    
    # Handle rate_code_id
    if 'rate_code_id' not in df.columns and 'RatecodeID' in df.columns:
        df['rate_code_id'] = df['RatecodeID']
    elif 'rate_code_id' not in df.columns:
        df['rate_code_id'] = 1
    df['rate_code_id'] = pd.to_numeric(df['rate_code_id'], errors='coerce').fillna(1).astype(int)
    
    # Average speed
    df['average_speed_mph'] = df.apply(
        lambda row: calculate_speed(row['trip_distance_miles'], row['trip_duration']),
        axis=1
    )
    
    # Categories
    df['distance_category'] = df['trip_distance_miles'].apply(get_distance_category)
    df['duration_category'] = df['trip_duration'].apply(get_duration_category)
    
    # Generate unique IDs if not present
    if 'id' not in df.columns:
        df['id'] = [f"TRIP_{i:08d}" for i in range(len(df))]
    
    # Data quality filters
    before_filter = len(df)
    df = df[
        (df['trip_duration'] > 0) &
        (df['trip_duration'] < 86400) &  # Less than 24 hours
        (df['trip_distance_miles'] >= 0) &
        (df['trip_distance_miles'] < 200) &  # Less than 200 miles
        (df['pickup_longitude'].between(-180, 180)) &
        (df['pickup_latitude'].between(-90, 90))
    ]
    
    if len(df) < before_filter:
        print(f" Filtered out {before_filter - len(df)} rows with invalid data")
    
    print(f"Prepared {len(df):,} records (from {initial_count:,} original)")
    return df

# DATABASE OPERATIONS

def get_db_connection():
    """Create database connection using PyMySQL"""
    return pymysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        cursorclass=pymysql.cursors.DictCursor
    )

def load_data_to_db(df, batch_size=5000):
    """Load data into MySQL database in batches"""
    print(f"\n Loading {len(df):,} records to database...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO nyc_taxi_trips (
            id, vendor_id, pickup_date, dropoff_datetime, passenger_count,
            pickup_longitude, pickup_latitude, rate_code_id,
            store_and_fwd_flag, trip_duration, trip_distance_miles,
            pickup_hour, pickup_day_of_week,
            is_weekend, time_period, average_speed_mph,
            distance_category, duration_category
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            trip_duration = VALUES(trip_duration),
            trip_distance_miles = VALUES(trip_distance_miles)
        """
        
        # Convert dataframe to list of tuples
        data = []
        skipped = 0
        
        for _, row in df.iterrows():
            try:
                data.append((
                    str(row['id']),
                    str(row['vendor_id']),
                    row['pickup_date'].strftime('%Y-%m-%d %H:%M:%S'),
                    row['dropoff_datetime'].strftime('%Y-%m-%d %H:%M:%S'),
                    int(row['passenger_count']),
                    float(row['pickup_longitude']),
                    float(row['pickup_latitude']),
                    int(row['rate_code_id']),
                    str(row['store_and_fwd_flag'])[:5],
                    int(row['trip_duration']),
                    float(row['trip_distance_miles']),
                    int(row['pickup_hour']) if pd.notna(row['pickup_hour']) else None,
                    int(row['pickup_day_of_week']) if pd.notna(row['pickup_day_of_week']) else None,
                    int(row['is_weekend']),
                    str(row['time_period']) if pd.notna(row['time_period']) else None,
                    float(row['average_speed_mph']),
                    str(row['distance_category']) if pd.notna(row['distance_category']) else None,
                    str(row['duration_category']) if pd.notna(row['duration_category']) else None
                ))
            except Exception as e:
                skipped += 1
                if skipped <= 5:  # Only print first 5 errors
                    print(f" Skipping row: {e}")
        
        if skipped > 0:
            print(f" Skipped {skipped} rows due to errors")
        
        total_records = len(data)
        inserted = 0
        
        for i in range(0, total_records, batch_size):
            batch = data[i:i + batch_size]
            cursor.executemany(insert_query, batch)
            conn.commit()
            
            inserted += len(batch)
            progress = min(i + batch_size, total_records)
            percentage = (progress / total_records) * 100
            print(f" Progress: {progress:,}/{total_records:,} ({percentage:.1f}%)", end='\r')
        
        print(f"\n Successfully inserted {inserted:,} records")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n Error loading data: {e}")
        raise

def update_statistics():
    """Update all statistics tables"""
    print("\n Updating statistics...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update vendor statistics
        print("  ↻ Updating vendor statistics...")
        cursor.callproc('update_vendor_counts')
        
        # Update hourly statistics
        print("  ↻ Updating hourly statistics...")
        cursor.callproc('update_hourly_statistics')
        
        # Update trip statistics
        print("  ↻ Updating trip statistics...")
        cursor.execute("TRUNCATE TABLE trip_statistics")
        cursor.execute("""
            INSERT INTO trip_statistics (
                vendor_id, total_trips, average_trip_distance, 
                average_trip_duration, average_speed_mph,
                most_common_pickup_hour, most_common_day_of_week,
                calculation_date
            )
            SELECT 
                vendor_id,
                COUNT(*),
                AVG(trip_distance_miles),
                AVG(trip_duration),
                AVG(average_speed_mph),
                (SELECT pickup_hour FROM nyc_taxi_trips t2 
                 WHERE t2.vendor_id = t1.vendor_id AND pickup_hour IS NOT NULL
                 GROUP BY pickup_hour ORDER BY COUNT(*) DESC LIMIT 1),
                (SELECT pickup_day_of_week FROM nyc_taxi_trips t3
                 WHERE t3.vendor_id = t1.vendor_id AND pickup_day_of_week IS NOT NULL
                 GROUP BY pickup_day_of_week ORDER BY COUNT(*) DESC LIMIT 1),
                CURDATE()
            FROM nyc_taxi_trips t1
            GROUP BY vendor_id
        """)
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print("Statistics updated successfully")
        
    except Exception as e:
        print(f"Error updating statistics: {e}")
        raise
    
    
def verify_data_load():
    """Verify data was loaded correctly"""
    print("\nVerifying data load...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total trips
        cursor.execute("SELECT COUNT(*) as count FROM nyc_taxi_trips")
        total_trips = cursor.fetchone()['count']
        print(f"Total trips: {total_trips:,}")
        
        # Statistics
        cursor.execute("""
            SELECT 
                AVG(trip_duration) as avg_duration,
                AVG(trip_distance_miles) as avg_distance,
                AVG(average_speed_mph) as avg_speed
            FROM nyc_taxi_trips
        """)
        stats = cursor.fetchone()
        print(f"  Avg duration: {stats['avg_duration']:.2f} seconds")
        print(f"  Avg distance: {stats['avg_distance']:.2f} miles")
        print(f"  Avg speed: {stats['avg_speed']:.2f} mph")
        
        # Distance distribution
        cursor.execute("""
            SELECT distance_category, COUNT(*) as count
            FROM nyc_taxi_trips
            WHERE distance_category IS NOT NULL
            GROUP BY distance_category
            ORDER BY 
                CASE distance_category
                    WHEN 'Short' THEN 1
                    WHEN 'Medium' THEN 2
                    WHEN 'Long' THEN 3
                END
        """)
        print("\n  Distance distribution:")
        for row in cursor.fetchall():
            print(f"     {row['distance_category']}: {row['count']:,}")
        
        # Vendor statistics
        cursor.execute("SELECT vendor_id, vendor_name, total_trips FROM vendors ORDER BY total_trips DESC")
        print("\n  Vendor statistics:")
        for row in cursor.fetchall():
            print(f"     {row['vendor_name']} (ID: {row['vendor_id']}): {row['total_trips']:,} trips")
        
        cursor.close()
        conn.close()
        
        print("\nVerification complete!")
        
    except Exception as e:
        print(f"Error verifying data: {e}")
        raise

# MAIN EXECUTION

if __name__ == "__main__":
    
    print("NYC TAXI DATA LOADER")
    
    # Check for CSV file
    data_path = os.getenv('CSV_FILE_PATH', 'data/raw/processed/cleaned_data.csv')
    
    if not os.path.exists(data_path):
        print(f"\nError: File not found at {data_path}")
        print(f"   Please ensure your CSV file exists at this location")
        print(f"   Or set CSV_FILE_PATH environment variable")
        sys.exit(1)
    
    try:
        # Step 1: Load CSV
        print(f"\n[1/5] Loading data from {data_path}...")
        df = pd.read_csv(data_path)
        print(f"Loaded {len(df):,} records")
        
        # Step 2: Prepare data
        print("\n[2/5] Preparing data...")
        df_prepared = prepare_data(df)
        
        # Step 3: Load to database
        print("\n[3/5] Loading to database...")
        load_data_to_db(df_prepared)
        
        # Step 4: Update statistics
        print("\n[4/5] Updating statistics...")
        update_statistics()
        
        # Step 5: Verify
        print("\n[5/5] Verifying data...")
        verify_data_load()
        
        print("\n" + "=" * 60)
        print("DATA LOADING COMPLETE!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)