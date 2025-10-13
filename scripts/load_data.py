# This is a data load script
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Databse confug

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_HOST', 8000)),
    'database': os.getenv('DB_NAME', 'nyc_taxi_trips'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'frank0014')
}

def get_time_period(hour):
    """time period from hour """
    if 6 <= hour < 12:
        return 'Morning'
    elif 12 <= hour < 17:
        return 'Afternoon'
    elif 17 <= hour < 21:
        return 'Evening'
    else:
        return 'Night'

def get_distance_category(distance):
    """trip distace by category"""
    if distance < 1:
        return 'Short'
    elif distance < 5:
        return 'Medium'
    else:
        return 'Long'
    
def get_duration_category(duration):
    """trip duration category"""
    minutes = duration / 60
    if minutes < 10:
        return 'Quick'
    elif minutes < 30:
        return 'Average'
    else:
        return 'Extended'
    
def calculate_speed(distance_miles, duration_seconds):
    """ getting average speed """
    if duration_seconds == 0:
        return 0
    hours = duration_seconds / 3600
    return distance_miles / hours

def prepare_data(my_data):
    """ getting all the data ready to match with the schema """
    print("Prentind derived features....")
    
    # convert datetime columns
    my_data['dropoff_datetime'] = pd.get_datetime(my_data['dropoff_datetime'])
    
    # Get temprol features from dropoff_datetime
    my_data['pickup_hour'] = my_data['dropoff_datetime'].dt.hour
    my_data['pickup_day_of_week'] = my_data['dropoff_datetime'].dt.dayofweek
    my_data['pickup_date'] = my_data['dropoff_datetime'].dt.date
    my_data['is_weekend'] = my_data['pickup_day)of_week'].isin([5,6]).astype(int)
    #apply time period
    my_data['time_period'] = my_data['pickup_hour'].apply(get_time_period)
    # calcualte averag speed
    my_data['average_speed_mph'] = my_data.app( lambda row: calculate_speed(['trip_distance_miles'], row['trip_duration']), axis=1)
    # Help get the categories
    my_data['distance_category'] = my_data['trip_distance_miles'].apply(get_distance_category)
    my_data['duration_category'] = my_data['trip_duration'].apply(get_duration_category)
    
    print(f"we prepared a number of {len(my_data)} records")
    return my_data

def load_data_to_db(my_data, batch_size=10000):
    """ Helps loaddata into MySql database but matching the schema"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # Prepare insert query for the table structure
        insert_query = """
        INSERT INTO nyc_taxi_trips (
            id, vendor_id, dropoff_datetime, passenger_count,
            pickup_longitude, pickup_latitude, rate_code_id,
            store_and_fwd_flag, trip_duration, trip_distance_miles,
            pickup_hour, pickup_day_of_week, pickup_date,
            is_weekend, time_period, average_speed_mph,
            distance_category, duration_category
            ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s
            ) 
            """
            # Convert data frame(my_data) to a list of tuples
            
        data = []
        for _, row in my_data.iterrow():
            data.append((
                str(row['id']),
                str(row['vendor_id']),
                row['dropoff_datetime'],
                int(row['passenger_count']),
                float(row['pickup_longitude']),
                float(row['pickup_latitude']),
                int(row.get('rate_code_id', 1)),  # Default to 1 if not present
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
            
            # Insert data in batches
            total_records = len(data)
            print(f"\n Inserting {total_records} records in batches of {batch_size}.")
            
            for i in range(0, total_records, batch_size):
                batch = data[i:i + batch_size]
            cursor.executemany(insert_query, batch)
            conn.commit()
            
            progress = min(i + batch_size, total_records)
            percentage = (progress / total_records) * 100
            print(f"Progress: {progress}/{total_records} ({percentage:.1f}%)")
        
        print("✓ Data loaded successfully")
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"✗ Error loading data: {e}")
        raise

def update_vendor_stats():
    """Update vendor statistics after loading data"""
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
        print("✓ Vendor statistics updated")
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"✗ Error updating vendor stats: {e}")
        raise

def update_trip_statistics():
    """Update overall trip statistics"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\nUpdating trip statistics...")
        
        # Clear existing stats
        cursor.execute("TRUNCATE TABLE trip_statistics")
        
        # Insert new stats
        cursor.execute("""
            INSERT INTO trip_statistics (
                total_trips,
                average_trip_distance,
                average_trip_duration,
                average_speed_mph,
                most_common_pickup_hour,
                most_common_day_of_week
            )
            SELECT 
                COUNT(*) as total_trips,
                AVG(trip_distance_miles) as avg_distance,
                AVG(trip_duration) as avg_duration,
                AVG(average_speed_mph) as avg_speed,
                (SELECT pickup_hour FROM nyc_taxi_trips 
                 WHERE pickup_hour IS NOT NULL
                 GROUP BY pickup_hour 
                 ORDER BY COUNT(*) DESC LIMIT 1) as common_hour,
                (SELECT pickup_day_of_week FROM nyc_taxi_trips 
                 WHERE pickup_day_of_week IS NOT NULL
                 GROUP BY pickup_day_of_week 
                 ORDER BY COUNT(*) DESC LIMIT 1) as common_day
            FROM nyc_taxi_trips
        """)
        
        conn.commit()
        print("✓ Trip statistics updated")
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"✗ Error updating trip statistics: {e}")
        raise

def update_hourly_statistics():
    """Update hourly statistics"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\nUpdating hourly statistics...")
        
        # Clear existing stats
        cursor.execute("DELETE FROM hourly_statistics")
        
        # Insert new stats
        cursor.execute("""
            INSERT INTO hourly_statistics (
                pickup_hour,
                total_trips,
                average_duration,
                average_distance,
                average_speed
            )
            SELECT 
                pickup_hour,
                COUNT(*) as total_trips,
                AVG(trip_duration) as avg_duration,
                AVG(trip_distance_miles) as avg_distance,
                AVG(average_speed_mph) as avg_speed
            FROM nyc_taxi_trips
            WHERE pickup_hour IS NOT NULL
            GROUP BY pickup_hour
        """)
        
        conn.commit()
        print("✓ Hourly statistics updated")
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"✗ Error updating hourly statistics: {e}")
        raise

def verify_data_load():
    """Verify data was loaded correctly"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Count total records
        cursor.execute("SELECT COUNT(*) FROM nyc_taxi_trips")
        total_trips = cursor.fetchone()[0]
        print(f"\n✓ Total trips in database: {total_trips:,}")
        
        # Check derived features
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(trip_duration) as avg_duration,
                AVG(trip_distance_miles) as avg_distance,
                AVG(average_speed_mph) as avg_speed
            FROM nyc_taxi_trips
        """)
        stats = cursor.fetchone()
        print(f"\n✓ Statistics:")
        print(f"  - Total trips: {stats[0]:,}")
        print(f"  - Avg duration: {stats[1]:.2f} seconds")
        print(f"  - Avg distance: {stats[2]:.2f} miles")
        print(f"  - Avg speed: {stats[3]:.2f} mph")
        
        # Check categories
        cursor.execute("""
            SELECT distance_category, COUNT(*) 
            FROM nyc_taxi_trips 
            WHERE distance_category IS NOT NULL
            GROUP BY distance_category
        """)
        print(f"\n✓ Distance distribution:")
        for category, count in cursor.fetchall():
            print(f"  - {category}: {count:,}")
        
        # Check vendors
        cursor.execute("SELECT vendor_id, vendor_name, total_trips FROM vendors")
        print(f"\n✓ Vendor statistics:")
        for vendor_id, name, trips in cursor.fetchall():
            print(f"  - {name} (ID: {vendor_id}): {trips:,} trips")
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"✗ Error verifying data: {e}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("NYC TAXI DATA LOADING (MySQL)")
    print("=" * 60)
    
    # File path
    cleaned_data_path = 'data/processed/cleaned_trips.csv'
    
    if not os.path.exists(cleaned_data_path):
        print(f"✗ Error: File not found at {cleaned_data_path}")
        print("Please ensure your cleaned data is at the correct location.")
        exit(1)
    
    print(f"\n[1/6] Loading cleaned data from {cleaned_data_path}...")
    df = pd.read_csv(cleaned_data_path)
    print(f"✓ Loaded {len(df)} records")
    
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
    
    print("\n" + "=" * 60)
    print("DATA LOADING COMPLETE!")
    print("=" * 60)


# Here is the way you could execute this

# Run your ubuntu and then
# Step 1: Make sure MySQL is running
# mysql -u root -p

# Step 2: Create database
# mysql -u root -p -e "CREATE DATABASE nyc_taxi_db;"

# Step 3: Run schema
# mysql -u root -p nyc_taxi_db < database/schema.sql

# Step 4: Verify tables created
# mysql -u root -p nyc_taxi_db -e "SHOW TABLES;"

# Step 5: Load your data
# python scripts/load_data.py