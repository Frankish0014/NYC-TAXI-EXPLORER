-- NYC Taxi Explorer - Fixed Database Schema
-- This schema is optimized for MySQL and fixes all foreign key issues
-- 
-- SETUP INSTRUCTIONS:
-- 1. Create database: CREATE DATABASE nyc_taxi_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- 2. Use database: USE nyc_taxi_db;
-- 3. Run this file: SOURCE /path/to/schema.sql;

-- Drop existing tables if they exist (in correct order due to foreign keys)
DROP TABLE IF EXISTS hourly_statistics;
DROP TABLE IF EXISTS trip_statistics;
DROP TABLE IF EXISTS nyc_taxi_trips;
DROP TABLE IF EXISTS vendors;

-- Drop existing views if they exist
DROP VIEW IF EXISTS trips_by_hour;
DROP VIEW IF EXISTS trips_by_day;
DROP VIEW IF EXISTS weekend_vs_weekday;
DROP VIEW IF EXISTS distance_distribution;
DROP VIEW IF EXISTS time_period_analysis;
DROP VIEW IF EXISTS vendor_comparison;

-- VENDORS TABLE (Parent)
CREATE TABLE vendors (
    vendor_id VARCHAR(15) PRIMARY KEY,
    vendor_name VARCHAR(100) NOT NULL,
    total_trips INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_vendor_name (vendor_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert sample vendor data
INSERT INTO vendors (vendor_id, vendor_name) VALUES 
('1', 'Creative Mobile Technologies'),
('2', 'VeriFone Inc.');

-- NYC TAXI TRIPS TABLE (Main Data Table)
CREATE TABLE nyc_taxi_trips (
    -- Primary Key
    id VARCHAR(50) PRIMARY KEY,
    
    -- Foreign Key to Vendors
    vendor_id VARCHAR(15) NOT NULL,
    
    -- Trip Details
    pickup_date DATETIME NOT NULL,
    dropoff_datetime DATETIME NOT NULL,
    passenger_count INT NOT NULL CHECK (passenger_count > 0 AND passenger_count <= 9),
    
    -- Location Data
    pickup_longitude DECIMAL(10, 7) NOT NULL,
    pickup_latitude DECIMAL(10, 7) NOT NULL,
    
    -- Trip Metadata
    rate_code_id INT DEFAULT 1,
    store_and_fwd_flag VARCHAR(5) DEFAULT 'N',
    
    -- Trip Measurements
    trip_duration INT NOT NULL CHECK (trip_duration > 0),
    trip_distance_miles DECIMAL(10, 3) NOT NULL CHECK (trip_distance_miles >= 0),
    
    -- Derived Time Features
    pickup_hour INT CHECK (pickup_hour BETWEEN 0 AND 23),
    pickup_day_of_week INT CHECK (pickup_day_of_week BETWEEN 0 AND 6),
    is_weekend BOOLEAN DEFAULT FALSE,
    time_period VARCHAR(20),
    
    -- Derived Speed and Categories
    average_speed_mph DECIMAL(10, 2) CHECK (average_speed_mph >= 0),
    distance_category VARCHAR(20),
    duration_category VARCHAR(20),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for Performance
    INDEX idx_vendor (vendor_id),
    INDEX idx_pickup_date (pickup_date),
    INDEX idx_dropoff_datetime (dropoff_datetime),
    INDEX idx_pickup_hour (pickup_hour),
    INDEX idx_pickup_day (pickup_day_of_week),
    INDEX idx_weekend (is_weekend),
    INDEX idx_time_period (time_period),
    INDEX idx_speed (average_speed_mph),
    INDEX idx_distance (trip_distance_miles),
    INDEX idx_duration (trip_duration),
    INDEX idx_distance_cat (distance_category),
    INDEX idx_duration_cat (duration_category),
    INDEX idx_location (pickup_latitude, pickup_longitude),
    INDEX idx_date_vendor (pickup_date, vendor_id),
    INDEX idx_composite_analysis (pickup_hour, pickup_day_of_week, is_weekend),
    
    -- Foreign Key Constraint
    CONSTRAINT fk_vendor_trip 
        FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- TRIP STATISTICS TABLE (Aggregated Stats)
CREATE TABLE trip_statistics (
    stat_id INT AUTO_INCREMENT PRIMARY KEY,
    vendor_id VARCHAR(15) NULL,
    total_trips INT NOT NULL DEFAULT 0,
    average_trip_distance DECIMAL(10, 3),
    average_trip_duration DECIMAL(10, 2),
    average_speed_mph DECIMAL(10, 2),
    most_common_pickup_hour INT,
    most_common_day_of_week INT,
    calculation_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_calc_date (calculation_date),
    INDEX idx_vendor_stat (vendor_id),
    
    CONSTRAINT fk_trip_stats_vendor
        FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- HOURLY STATISTICS TABLE (Pre-aggregated)
CREATE TABLE hourly_statistics (
    hour_stat_id INT AUTO_INCREMENT PRIMARY KEY,
    pickup_hour INT NOT NULL CHECK (pickup_hour BETWEEN 0 AND 23),
    total_trips INT DEFAULT 0,
    average_duration DECIMAL(10, 2),
    average_distance DECIMAL(10, 3),
    average_speed DECIMAL(10, 2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_pickup_hour (pickup_hour),
    INDEX idx_hour (pickup_hour)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- VIEWS FOR COMMON QUERIES

-- View: Trips by Hour
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

-- View: Trips by Day of Week
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
    AVG(trip_distance_miles) AS avg_distance_miles,
    AVG(average_speed_mph) AS avg_speed_mph
FROM nyc_taxi_trips
WHERE pickup_day_of_week IS NOT NULL
GROUP BY pickup_day_of_week
ORDER BY pickup_day_of_week;

-- View: Weekend vs Weekday Comparison
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

-- View: Distance Distribution
CREATE OR REPLACE VIEW distance_distribution AS
SELECT 
    distance_category,
    COUNT(*) AS trip_count,
    AVG(trip_duration) AS avg_duration_seconds,
    AVG(average_speed_mph) AS avg_speed_mph,
    MIN(trip_distance_miles) AS min_distance,
    MAX(trip_distance_miles) AS max_distance,
    AVG(trip_distance_miles) AS avg_distance
FROM nyc_taxi_trips
WHERE distance_category IS NOT NULL
GROUP BY distance_category
ORDER BY 
    CASE distance_category
        WHEN 'Short' THEN 1
        WHEN 'Medium' THEN 2
        WHEN 'Long' THEN 3
        ELSE 4
    END;

-- View: Time Period Analysis
CREATE OR REPLACE VIEW time_period_analysis AS
SELECT
    time_period,
    COUNT(*) AS trip_count,
    AVG(trip_duration) AS avg_duration_seconds,
    AVG(trip_distance_miles) AS avg_distance_miles,
    AVG(passenger_count) AS avg_passengers,
    AVG(average_speed_mph) AS avg_speed_mph
FROM nyc_taxi_trips
WHERE time_period IS NOT NULL
GROUP BY time_period
ORDER BY 
    CASE time_period
        WHEN 'Morning' THEN 1
        WHEN 'Afternoon' THEN 2
        WHEN 'Evening' THEN 3
        WHEN 'Night' THEN 4
        ELSE 5
    END;

-- View: Vendor Comparison
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
GROUP BY v.vendor_id, v.vendor_name
ORDER BY total_trips DESC;

-- STORED PROCEDURES

-- Procedure: Update Hourly Statistics
DELIMITER $$
CREATE PROCEDURE update_hourly_statistics()
BEGIN
    TRUNCATE TABLE hourly_statistics;
    
    INSERT INTO hourly_statistics (pickup_hour, total_trips, average_duration, average_distance, average_speed)
    SELECT 
        pickup_hour,
        COUNT(*) as total_trips,
        AVG(trip_duration) as average_duration,
        AVG(trip_distance_miles) as average_distance,
        AVG(average_speed_mph) as average_speed
    FROM nyc_taxi_trips
    WHERE pickup_hour IS NOT NULL
    GROUP BY pickup_hour;
END$$
DELIMITER ;

-- Procedure: Update Vendor Trip Counts
DELIMITER $$
CREATE PROCEDURE update_vendor_counts()
BEGIN
    UPDATE vendors v
    SET total_trips = (
        SELECT COUNT(*) 
        FROM nyc_taxi_trips t 
        WHERE t.vendor_id = v.vendor_id
    );
END$$
DELIMITER ;

-- TRIGGERS

-- Trigger: Update vendor count after insert
DELIMITER $$
CREATE TRIGGER after_trip_insert
AFTER INSERT ON nyc_taxi_trips
FOR EACH ROW
BEGIN
    UPDATE vendors 
    SET total_trips = total_trips + 1,
        last_updated = CURRENT_TIMESTAMP
    WHERE vendor_id = NEW.vendor_id;
END$$
DELIMITER ;

-- Trigger: Update vendor count after delete
DELIMITER $$
CREATE TRIGGER after_trip_delete
AFTER DELETE ON nyc_taxi_trips
FOR EACH ROW
BEGIN
    UPDATE vendors 
    SET total_trips = total_trips - 1,
        last_updated = CURRENT_TIMESTAMP
    WHERE vendor_id = OLD.vendor_id;
END$$
DELIMITER ;

-- SAMPLE DATA (Optional - for testing)

-- Insert sample trip (uncomment to use)
/*
INSERT INTO nyc_taxi_trips (
    id, vendor_id, pickup_date, dropoff_datetime, passenger_count,
    pickup_longitude, pickup_latitude, rate_code_id, store_and_fwd_flag,
    trip_duration, trip_distance_miles, pickup_hour, pickup_day_of_week,
    is_weekend, time_period, average_speed_mph, distance_category, duration_category
) VALUES (
    'SAMPLE001', '1', '2024-01-15 08:30:00', '2024-01-15 08:45:00', 1,
    -73.9851, 40.7580, 1, 'N', 900, 2.5, 8, 0, FALSE, 'Morning', 10.0, 'Short', 'Medium'
);
*/

-- UTILITY QUERIES (for verification)

-- Check table structure
-- DESCRIBE nyc_taxi_trips;
-- DESCRIBE vendors;

-- Check foreign keys
-- SELECT * FROM information_schema.KEY_COLUMN_USAGE 
-- WHERE TABLE_SCHEMA = 'nyc_taxi_db' AND REFERENCED_TABLE_NAME IS NOT NULL;

-- Check indexes
-- SHOW INDEX FROM nyc_taxi_trips;

-- Verify views
-- SELECT * FROM trips_by_hour LIMIT 5;
-- SELECT * FROM vendor_comparison;

-- PERFORMANCE OPTIMIZATION NOTES

/*
For large datasets (millions of rows), consider:

1. Partitioning by date:
   ALTER TABLE nyc_taxi_trips 
   PARTITION BY RANGE (YEAR(pickup_date)) (
       PARTITION p2023 VALUES LESS THAN (2024),
       PARTITION p2024 VALUES LESS THAN (2025),
       PARTITION p2025 VALUES LESS THAN (2026)
   );

2. Add full-text search if needed:
   ALTER TABLE nyc_taxi_trips ADD FULLTEXT(distance_category, duration_category);

3. Regular maintenance:
   OPTIMIZE TABLE nyc_taxi_trips;
   ANALYZE TABLE nyc_taxi_trips;
*/

-- SUCCESS MESSAGE
SELECT 'Database schema created successfully!' AS Status;
SELECT 'Tables created: vendors, nyc_taxi_trips, trip_statistics, hourly_statistics' AS Info;
SELECT 'Views created: 6 analytical views' AS Views;
SELECT 'Procedures created: update_hourly_statistics, update_vendor_counts' AS Procedures;
SELECT 'Triggers created: after_trip_insert, after_trip_delete' AS Triggers;