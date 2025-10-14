import csv
import sqlite3
from datetime import datetime
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on Earth"""
    # Convert coordinates from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Earth radius in kilometers
    return c * r

def get_time_period(hour):
    """Categorize time into periods relevant for NYC traffic"""
    if 0 <= hour < 6:
        return "late_night"
    elif 6 <= hour < 10:
        return "morning_rush"
    elif 10 <= hour < 16:
        return "midday"
    elif 16 <= hour < 20:
        return "evening_rush"
    else:
        return "night"

def is_weekend(day_name):
    """Check if day is weekend"""
    return day_name in ['Saturday', 'Sunday']

def process_nyc_taxi_data():
    """Process the NYC Taxi Trip Duration dataset"""
    
    conn = sqlite3.connect('nyc_taxi.db')
    cursor = conn.cursor()
    
    processed_count = 0
    error_count = 0
    
    print("Processing NYC Taxi Trip Duration dataset...")
    
    with open('data/raw/train.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for i, row in enumerate(reader):
            try:
                # Parse datetime
                pickup_dt = datetime.strptime(row['pickup_datetime'], '%Y-%m-%d %H:%M:%S')
                dropoff_dt = datetime.strptime(row['dropoff_datetime'], '%Y-%m-%d %H:%M:%S')
                
                # Extract time features
                hour = pickup_dt.hour
                time_period = get_time_period(hour)
                day_of_week = pickup_dt.strftime('%A')
                is_weekend_trip = is_weekend(day_of_week)
                month = pickup_dt.month
                day_of_month = pickup_dt.day
                
                # Calculate distance using Haversine
                pickup_lat = float(row['pickup_latitude'])
                pickup_lon = float(row['pickup_longitude'])
                dropoff_lat = float(row['dropoff_latitude'])
                dropoff_lon = float(row['dropoff_longitude'])
                
                distance_km = haversine_distance(pickup_lat, pickup_lon, dropoff_lat, dropoff_lon)
                
                # Calculate speed (km/h)
                trip_duration_hours = int(row['trip_duration']) / 3600
                speed_kmh = distance_km / trip_duration_hours if trip_duration_hours > 0 else 0
                
                # Efficiency metric
                expected_time = distance_km * 3  # rough estimate: 3 min per km in city traffic
                actual_time = int(row['trip_duration']) / 60  # convert to minutes
                efficiency_ratio = expected_time / actual_time if actual_time > 0 else 0
                
                # Insert into database
                cursor.execute('''
                    INSERT INTO trips 
                    (id, vendor_id, pickup_datetime, dropoff_datetime, passenger_count,
                     pickup_longitude, pickup_latitude, dropoff_longitude, dropoff_latitude,
                     store_and_fwd_flag, trip_duration, trip_speed, time_of_day, day_of_week, 
                     calculated_distance, time_period, is_weekend, month, day_of_month, efficiency_ratio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['id'], int(row['vendor_id']), row['pickup_datetime'], row['dropoff_datetime'],
                    int(row['passenger_count']), pickup_lon, pickup_lat, dropoff_lon, dropoff_lat,
                    row['store_and_fwd_flag'], int(row['trip_duration']), speed_kmh, 
                    f"{hour:02d}:00", day_of_week, distance_km, time_period, 
                    is_weekend_trip, month, day_of_month, efficiency_ratio
                ))
                
                processed_count += 1
                
                # Progress indicator
                if processed_count % 10000 == 0:
                    print(f"Processed {processed_count} rows...")
                    
                # Limit for initial testing (remove for full dataset)
                if processed_count >= 50000:
                    break
                    
            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    print(f"Error processing row {i}: {e}")
    
    conn.commit()
    
    # Create summary table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trip_summary AS
        SELECT 
            COUNT(*) as total_trips,
            AVG(trip_duration) as avg_duration,
            AVG(calculated_distance) as avg_distance,
            AVG(trip_speed) as avg_speed,
            time_period,
            day_of_week,
            is_weekend
        FROM trips 
        GROUP BY time_period, day_of_week, is_weekend
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"Data processing completed!")
    print(f"Successfully processed: {processed_count} trips")
    print(f"Errors encountered: {error_count}")

if __name__ == '__main__':
    process_nyc_taxi_data()
