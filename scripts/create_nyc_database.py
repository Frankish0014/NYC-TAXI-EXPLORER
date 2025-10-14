import sqlite3
import os

def create_nyc_database():
    """Create optimized database for NYC Taxi data"""
    
    if os.path.exists('nyc_taxi.db'):
        os.remove('nyc_taxi.db')
    
    conn = sqlite3.connect('nyc_taxi.db')
    cursor = conn.cursor()
    
    # Main trips table with enhanced fields
    cursor.execute('''
        CREATE TABLE trips (
            id TEXT PRIMARY KEY,
            vendor_id INTEGER,
            pickup_datetime DATETIME,
            dropoff_datetime DATETIME,
            passenger_count INTEGER,
            pickup_longitude REAL,
            pickup_latitude REAL,
            dropoff_longitude REAL,
            dropoff_latitude REAL,
            store_and_fwd_flag TEXT,
            trip_duration INTEGER,
            trip_speed REAL,
            time_of_day TEXT,
            day_of_week TEXT,
            calculated_distance REAL,
            time_period TEXT,
            is_weekend BOOLEAN,
            month INTEGER,
            day_of_month INTEGER,
            efficiency_ratio REAL
        )
    ''')
    
    # Create comprehensive indexes
    indexes = [
        'CREATE INDEX idx_pickup_datetime ON trips(pickup_datetime)',
        'CREATE INDEX idx_trip_duration ON trips(trip_duration)',
        'CREATE INDEX idx_passenger_count ON trips(passenger_count)',
        'CREATE INDEX idx_time_period ON trips(time_period)',
        'CREATE INDEX idx_day_of_week ON trips(day_of_week)',
        'CREATE INDEX idx_is_weekend ON trips(is_weekend)',
        'CREATE INDEX idx_month ON trips(month)',
        'CREATE INDEX idx_efficiency ON trips(efficiency_ratio)'
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    conn.commit()
    conn.close()
    print("NYC Taxi database created with optimized schema!")

if __name__ == '__main__':
    create_nyc_database()
