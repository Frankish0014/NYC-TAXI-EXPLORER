-- Database schema for NYC Taxi Explorer
-- This schema defines the structure of the database tables
-- used to store and analyze NYC taxi trip data.

-- NOTE: Before running this schema, first create a MySQL database:
-- Example: CREATE DATABASE nyc_taxi_db;
-- Then run: SOURCE PATH/TO/THE/schema.sql;

-- Vendors Table (Parent)
CREATE TABLE vendors (
    vendor_id VARCHAR(15) PRIMARY KEY,
    vendor_name VARCHAR(100) NOT NULL,
    total_trips INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Sample data for vendors
INSERT INTO vendors (vendor_id, vendor_name) VALUES 
('1', 'Vendor-1'),
('2', 'Vendor-2');


-- NYC Taxi Trips Table (Child)
CREATE TABLE nyc_taxi_trips (
    id VARCHAR(50) PRIMARY KEY,
    vendor_id VARCHAR(15) NOT NULL,
    dropoff_datetime TIMESTAMP NOT NULL,
    passenger_count INT NOT NULL,
    pickup_longitude FLOAT NOT NULL,
    pickup_latitude FLOAT NOT NULL,
    rate_code_id INT NOT NULL,
    store_and_fwd_flag VARCHAR(5) NOT NULL,
    trip_duration INTEGER NOT NULL CHECK (trip_duration > 0),
    trip_distance_miles FLOAT NOT NULL CHECK (trip_distance_miles >= 0),

    -- Derived features
    pickup_hour INTEGER CHECK (pickup_hour BETWEEN 0 AND 23),
    pickup_day_of_week INTEGER CHECK (pickup_day_of_week BETWEEN 0 AND 6),
    pickup_date DATE,
    is_weekend BOOLEAN,
    time_period VARCHAR(20),

    -- Derived speed
    average_speed_mph FLOAT CHECK (average_speed_mph >= 0),
    distance_category VARCHAR(20),
    duration_category VARCHAR(20),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_trips_dropoff_datetime (dropoff_datetime),
    INDEX idx_trips_datetime_vendor_id (pickup_date, vendor_id),
    INDEX idx_trips_pickup_hour (pickup_hour),
    INDEX idx_trips_is_weekend (is_weekend),
    INDEX idx_trips_time_period (time_period),
    INDEX idx_trips_distance_category (distance_category),
    INDEX idx_trips_duration_category (duration_category),
    INDEX idx_trips_average_speed_mph (average_speed_mph),
    INDEX idx_trips_trip_distance_duration (trip_distance_miles, trip_duration),

    -- Foreign key constraint
    CONSTRAINT fk_vendor_trip FOREIGN KEY (vendor_id)
        REFERENCES vendors(vendor_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ==============================
-- Trip Statistics Table
-- ==============================
CREATE TABLE trip_statistics (
    stat_id INT AUTO_INCREMENT PRIMARY KEY,
    total_trips INT NOT NULL,
    average_trip_distance FLOAT,
    average_trip_duration FLOAT,
    average_speed_mph FLOAT,
    most_common_pickup_hour INT,
    most_common_day_of_week INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


--Hourly Statistics Table
CREATE TABLE hourly_statistics (
    hour_stat_id INT AUTO_INCREMENT PRIMARY KEY,
    pickup_hour INTEGER CHECK (pickup_hour BETWEEN 0 AND 23),
    total_trips INTEGER,
    average_duration DECIMAL(10, 2),
    average_distance DECIMAL(10, 2),
    average_speed DECIMAL(10, 2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_pickup_hour (pickup_hour)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


--  VIEWS for Common Queries

-- View: Trips by hour
CREATE OR REPLACE VIEW trips_by_hour AS
SELECT 
    pickup_hour,
    COUNT(*) AS trip_count,
    AVG(trip_duration) AS avg_duration_seconds,
    AVG(trip_distance_miles) AS avg_distance_miles,
    AVG(average_speed_mph) AS avg_speed_mph,
    AVG(passenger_count) AS avg_passengers
FROM nyc_taxi_trips
WHERE pickup_hour IS NOT NULL
GROUP BY pickup_hour
ORDER BY pickup_hour;

-- View: Trips by day of week
CREATE OR REPLACE VIEW trips_by_day AS
SELECT 
    pickup_day_of_week,
    CASE pickup_day_of_week
        WHEN 0 THEN 'Monday'
        WHEN 1 THEN 'Tuesday'
        WHEN 2 THEN 'Wednesday'
        WHEN 3 THEN 'Thursday'
        WHEN 4 THEN 'Friday'
        WHEN 5 THEN 'Saturday'
        WHEN 6 THEN 'Sunday'
    END AS day_name,
    COUNT(*) AS trip_count,
    AVG(trip_duration) AS avg_duration_seconds,
    AVG(trip_distance_miles) AS avg_distance_miles
FROM nyc_taxi_trips
WHERE pickup_day_of_week IS NOT NULL
GROUP BY pickup_day_of_week
ORDER BY pickup_day_of_week;

-- View: Weekend vs Weekday
CREATE OR REPLACE VIEW weekend_vs_weekday AS
SELECT 
    CASE WHEN is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END AS period_type,
    COUNT(*) AS trip_count,
    AVG(trip_duration) AS avg_duration_seconds,
    AVG(trip_distance_miles) AS avg_distance_miles,
    AVG(passenger_count) AS avg_passengers,
    AVG(average_speed_mph) AS avg_speed_mph
FROM nyc_taxi_trips
WHERE is_weekend IS NOT NULL
GROUP BY is_weekend;

-- View: Distance distribution
CREATE OR REPLACE VIEW distance_distribution AS
SELECT 
    distance_category,
    COUNT(*) AS trip_count,
    AVG(trip_duration) AS avg_duration_seconds,
    AVG(average_speed_mph) AS avg_speed_mph,
    MIN(trip_distance_miles) AS min_distance,
    MAX(trip_distance_miles) AS max_distance
FROM nyc_taxi_trips
WHERE distance_category IS NOT NULL
GROUP BY distance_category
ORDER BY 
    CASE distance_category
        WHEN 'Short' THEN 1
        WHEN 'Medium' THEN 2
        WHEN 'Long' THEN 3
    END;

-- View: Time period analysis
CREATE OR REPLACE VIEW time_period_analysis AS
SELECT
    time_period,
    COUNT(*) AS trip_count,
    AVG(trip_duration) AS avg_duration_seconds,
    AVG(trip_distance_miles) AS avg_distance_miles,
    AVG(passenger_count) AS avg_passengers
FROM nyc_taxi_trips
WHERE time_period IS NOT NULL
GROUP BY time_period
ORDER BY 
    CASE time_period
        WHEN 'Morning' THEN 1
        WHEN 'Afternoon' THEN 2
        WHEN 'Evening' THEN 3
        WHEN 'Night' THEN 4
    END;

-- View: Vendor comparison
CREATE OR REPLACE VIEW vendor_comparison AS
SELECT 
    v.vendor_id,
    v.vendor_name,
    COUNT(t.id) AS total_trips,
    AVG(t.trip_duration) AS avg_duration_seconds,
    AVG(t.trip_distance_miles) AS avg_distance_miles,
    AVG(t.average_speed_mph) AS avg_speed_mph,
    AVG(t.passenger_count) AS avg_passengers
FROM vendors v
LEFT JOIN nyc_taxi_trips t ON v.vendor_id = t.vendor_id
GROUP BY v.vendor_id, v.vendor_name;