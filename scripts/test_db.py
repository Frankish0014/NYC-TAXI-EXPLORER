import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'database': os.getenv('DB_NAME', 'nyc_taxi_db'),
    'user': os.getenv('DB_USER', 'frank'),
    'password': os.getenv('DB_PASSWORD', '')
}

def test_database():
    """Test database queries"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        print("DATABASE TEST - NYC TAXI DATA")
        
        # Test 1: Total trips
        print("\n[Test 1] Total Trips:")
        cursor.execute("SELECT COUNT(*) as total FROM nyc_taxi_trips")
        result = cursor.fetchone()
        print(f" Total trips: {result['total']:,}")
        
        # Test 2: Sample trip
        print("\n[Test 2] Sample Trip Data:")
        cursor.execute("SELECT * FROM nyc_taxi_trips LIMIT 1")
        trip = cursor.fetchone()
        for key, value in trip.items():
            print(f"  - {key}: {value}")
        
        # Test 3: Trips by hour
        print("\n[Test 3] Trips by Hour (Top 5):")
        cursor.execute("""
            SELECT pickup_hour, COUNT(*) as count 
            FROM nyc_taxi_trips 
            GROUP BY pickup_hour 
            ORDER BY count DESC 
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"  - Hour {row['pickup_hour']:02d}:00 = {row['count']:,} trips")
        
        # Test 4: Distance categories
        print("\n[Test 4] Distance Categories:")
        cursor.execute("""
            SELECT distance_category, COUNT(*) as count 
            FROM nyc_taxi_trips 
            WHERE distance_category IS NOT NULL
            GROUP BY distance_category
        """)
        for row in cursor.fetchall():
            print(f"  - {row['distance_category']}: {row['count']:,} trips")
        
        # Test 5: Vendors
        print("\n[Test 5] Vendor Statistics:")
        cursor.execute("SELECT * FROM vendors")
        for vendor in cursor.fetchall():
            print(f"  - {vendor['vendor_name']}: {vendor['total_trips']:,} trips")
        
        # Test 6: Statistics
        print("\n[Test 6] Overall Statistics:")
        cursor.execute("SELECT * FROM trip_statistics LIMIT 1")
        stats = cursor.fetchone()
        if stats:
            print(f"  - Total Trips: {stats['total_trips']:,}")
            print(f"  - Avg Distance: {stats['average_trip_distance']:.2f} miles")
            print(f"  - Avg Duration: {stats['average_trip_duration']:.2f} seconds")
            print(f"  - Avg Speed: {stats['average_speed_mph']:.2f} mph")
            print(f"  - Busiest Hour: {stats['most_common_pickup_hour']}")
        
        cursor.close()
        conn.close()
        
        print("ALL TESTS PASSED!")
        
        print("\nYour database is ready for the backend API!")
        
    except Error as e:
        print(f"\nDatabase Error: {e}")

if __name__ == "__main__":
    test_database()