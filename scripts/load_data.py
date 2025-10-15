# NYC Taxi Data Load Script
import os
from datetime import datetime

import pandas as pd
import mysql.connector
from mysql.connector import Error

from dotenv import load_dotenv

load_dotenv()

#Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),  
    'database': os.getenv('DB_NAME', 'nyc_taxi_db'),
    'user': os.getenv('DB_USER', 'frank'),
    'password': os.getenv('DB_PASSWORD')
}

#Feature Engineering
def get_time_period(hour):
    """Return time period based on hour"""
    if 6 <= hour < 12:
        return 'Morning'
    elif 12 <= hour < 17:
        return 'Afternoon'
    elif 17 <= hour < 21:
        return 'Evening'
    else:
        return 'Night'

def get_distance_category(distance):
    """Categorize trip distance"""
    if distance < 1:
        return 'Short'
    elif distance < 5:
        return 'Medium'
    else:
        return 'Long'

def get_duration_category(duration):
    """Categorize trip duration in seconds"""
    minutes = duration / 60
    if minutes < 10:
        return 'Quick'
    elif minutes < 30:
        return 'Average'
    else:
        return 'Extended'

def calculate_speed(distance_miles, duration_seconds):
    """Calculate average speed (mph)"""
    if duration_seconds == 0:
        return 0
    return distance_miles / (duration_seconds / 3600)

def prepare_data(df):
    """Prepare dataframe with derived features"""
    print("Preparing derived features...")

    # Ensure datetime conversion
    df['dropoff_datetime'] = pd.to_datetime(df['dropoff_datetime'], errors='coerce')
    if df['dropoff_datetime'].isna().any():
        print("Warning: Some dropoff_datetime values could not be parsed and will be NaT")

    # Temporal features
    df['pickup_hour'] = df['dropoff_datetime'].dt.hour
    df['pickup_day_of_week'] = df['dropoff_datetime'].dt.dayofweek
    df['pickup_date'] = df['dropoff_datetime'].dt.date
    df['is_weekend'] = df['pickup_day_of_week'].isin([5, 6]).astype(int)
    df['time_period'] = df['pickup_hour'].apply(get_time_period)

    # Average speed
    df['average_speed_mph'] = df.apply(
        lambda row: calculate_speed(row['trip_distance_miles'], row['trip_duration']),
        axis=1
    )

    # Categories
    df['distance_category'] = df['trip_distance_miles'].apply(get_distance_category)
    df['duration_category'] = df['trip_duration'].apply(get_duration_category)

    print(f"Prepared {len(df)} records")
    return df

#Database Load
def load_data_to_db(df, batch_size=100000000):
    """Load data into MySQL database in batches"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO nyc_taxi_trips (
            id, vendor_id, dropoff_datetime, passenger_count,
            pickup_longitude, pickup_latitude, rate_code_id,
            store_and_fwd_flag, trip_duration, trip_distance_miles,
            pickup_hour, pickup_day_of_week, pickup_date,
            is_weekend, time_period, average_speed_mph,
            distance_category, duration_category
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Convert dataframe to list of tuples
        data = []
        for _, row in df.iterrows():
            try:
                data.append((
                    str(row['id']),
                    str(row['vendor_id']),
                    row['dropoff_datetime'],
                    int(row['passenger_count']),
                    float(row['pickup_longitude']),
                    float(row['pickup_latitude']),
                    int(row.get('rate_code_id', 1)),  # default 1
                    str(row['store_and_fwd_flag']),
                    int(row['trip_duration']),
                    float(row['trip_distance_miles']),
                    int(row['pickup_hour']),
                    int(row['pickup_day_of_week']),
                    row['pickup_date'],
                    int(row['is_weekend']),
                    row['time_period'],
                    float(row['average_speed_mph']),
                    row['distance_category'],
                    row['duration_category']
                ))
            except Exception as e:
                print(f"Skipping row due to error: {e}")

        total_records = len(data)
        print(f"\nInserting {total_records} records in batches of {batch_size}...")

        for i in range(0, total_records, batch_size):
            batch = data[i:i + batch_size]
            cursor.executemany(insert_query, batch)
            conn.commit()
            
            progress = min(i + batch_size, total_records)
            print(f"Progress: {progress}/{total_records} ({(progress / total_records) * 100:.1f}%)")

        print("Data loaded successfully")
        cursor.close()
        conn.close()

    except Error as e:
        print(f"Error loading data: {e}")
        raise

#Statistics Updates 
def update_vendor_stats():
    """Update vendor statistics"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\nUpdating vendor statistics...")
        
        cursor.execute("""
            UPDATE vendors v
            SET total_trips = (
                SELECT COUNT(*)
                FROM nyc_taxi_trips t
                WHERE t.vendor_id = v.vendor_id
            )
        """)
        
        conn.commit()
        print("Vendor statistics updated")
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"Error updating vendor stats: {e}")
        raise

def update_trip_statistics():
    """Update overall trip statistics"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\nUpdating trip statistics...")
        
        cursor.execute(" TRUNCATE TABLE trip_statistics")
        
        cursor.execute( """
            INSERT INTO trip_statistics (
                total_trips, average_trip_distance, average_trip_duration, average_speed_mph,
                most_common_pickup_hour, most_common_day_of_week
            )
            SELECT 
                COUNT(*),
                AVG(trip_distance_miles),
                AVG(trip_duration),
                AVG(average_speed_mph),
                (SELECT pickup_hour FROM nyc_taxi_trips 
                 WHERE pickup_hour IS NOT NULL
                 GROUP BY pickup_hour 
                 ORDER BY COUNT(*) DESC LIMIT 1),
                (SELECT pickup_day_of_week FROM nyc_taxi_trips 
                 WHERE pickup_day_of_week IS NOT NULL
                 GROUP BY pickup_day_of_week 
                 ORDER BY COUNT(*) DESC LIMIT 1)
            FROM nyc_taxi_trips
        """)
        
        conn.commit()
        print("Trip statistics updated")
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"Error updating trip statistics: {e}")
        raise

def update_hourly_statistics():
    """Update hourly statistics"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\nUpdating hourly statistics...")
        
        cursor.execute(" DELETE FROM hourly_statistics ")
        
        cursor.execute( """
            INSERT INTO hourly_statistics (
                pickup_hour, total_trips, average_duration, average_distance, average_speed
            )
            SELECT 
                pickup_hour,
                COUNT(*),
                AVG(trip_duration),
                AVG(trip_distance_miles),
                AVG(average_speed_mph)
            FROM nyc_taxi_trips
            WHERE pickup_hour IS NOT NULL
            GROUP BY pickup_hour
        """ )
        conn.commit()
        print("Hourly statistics updated")
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"Error updating hourly statistics: {e}")
        raise

# Verification
def verify_data_load():
    """Verify data was loaded correctly"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM nyc_taxi_trips")
        total_trips = cursor.fetchone()[0]
        print(f"\nTotal trips in database: {total_trips:,}")

        cursor.execute("""
            SELECT COUNT(*), AVG(trip_duration), AVG(trip_distance_miles), AVG(average_speed_mph)
            FROM nyc_taxi_trips
        """)
        stats = cursor.fetchone()
        print(f"Statistics:\n  - Total trips: {stats[0]:,}\n  - Avg duration: {stats[1]:.2f} s\n  - Avg distance: {stats[2]:.2f} mi\n  - Avg speed: {stats[3]:.2f} mph")

        cursor.execute("""
            SELECT distance_category, COUNT(*) 
            FROM nyc_taxi_trips 
            WHERE distance_category IS NOT NULL
            GROUP BY distance_category
        """)
        print("\nDistance distribution:")
        for category, count in cursor.fetchall():
            print(f"  - {category}: {count:,}")

        cursor.execute("SELECT vendor_id, vendor_name, total_trips FROM vendors")
        print("\nVendor statistics:")
        for vendor_id, name, trips in cursor.fetchall():
            print(f"  - {name} (ID: {vendor_id}): {trips:,} trips")

        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"✗ Error verifying data: {e}")
        raise

# Main Execution

if __name__ == "__main__":
    
    print("NYC TAXI DATA LOADING (MySQL)")

    cleaned_data_path = 'data/raw/processed/cleaned_data.csv'
    if not os.path.exists(cleaned_data_path):
        print(f"Error: File not found at {cleaned_data_path}")
        exit(1)

    print(f"\n[1/6] Loading cleaned data from {cleaned_data_path}...")
    df = pd.read_csv(cleaned_data_path)
    print(f"Loaded {len(df)} records")

    print("\n[2/6] Preparing derived features...")
    df_prepared = prepare_data(df)

    print("\n[3/6] Loading data to database...")
    load_data_to_db(df_prepared)

    print("\n[4/6] Updating vendor statistics...")
    update_vendor_stats()

    print("\n[5/6] Updating trip statistics...")
    update_trip_statistics()
    update_hourly_statistics()

    print("\n[6/6] Verifying data load...")
    verify_data_load()

    print("DATA LOADING COMPLETE!")
