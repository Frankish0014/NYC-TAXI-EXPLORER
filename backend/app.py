from flask import Flask, jsonify, request
from flask_cors import CORS
import pymysql
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)

# MySQL connection configuration
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "nyc_taxi_db")
DB_PORT = int(os.getenv("MYSQL_PORT", 3306))

def get_db_connection():
    """Create and return a MySQL database connection"""
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn

def handle_errors(f):
    """Decorator to handle errors consistently"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            app.logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({"error": str(e)}), 500
    return decorated_function

# HEALTH CHECK

@app.route('/api/health', methods=['GET'])
@handle_errors
def health_check():
    """Check if API and database are working"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    conn.close()
    return jsonify({
        "status": "healthy",
        "database": "connected",
        "timestamp": datetime.now().isoformat()
    })

# STATISTICS & KPIs

@app.route('/api/stats', methods=['GET'])
@handle_errors
def get_stats():
    """Get overall statistics - FIXED to return km/h and km"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total_rows FROM nyc_taxi_trips')
    total_rows = cursor.fetchone()['total_rows']
    
    # Convert MPH to KM/H and miles to KM (1 mile = 1.60934 km)
    cursor.execute('''
        SELECT 
            AVG(average_speed_mph * 1.60934) as avg_speed_kmh,
            AVG(trip_distance_miles * 1.60934) as avg_distance_km
        FROM nyc_taxi_trips
    ''')
    stats = cursor.fetchone()
    
    conn.close()
    
    return jsonify({
        "total_rows": total_rows,
        "avg_speed_kmh": round(stats['avg_speed_kmh'], 2) if stats['avg_speed_kmh'] else 0,
        "avg_distance_km": round(stats['avg_distance_km'], 2) if stats['avg_distance_km'] else 0
    })

@app.route('/api/summary', methods=['GET'])
@handle_errors
def get_summary():
    """Get summary statistics for a specific date"""
    date = request.args.get('date')
    
    if not date:
        return jsonify({"error": "Date parameter required"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            DATE(pickup_date) as date,
            COUNT(*) as trips,
            AVG(average_speed_mph * 1.60934) as avg_speed_kmh,
            AVG(trip_distance_miles * 1.60934) as avg_distance_km,
            AVG(trip_duration / 60.0) as avg_duration_min
        FROM nyc_taxi_trips
        WHERE DATE(pickup_date) = %s
        GROUP BY DATE(pickup_date)
    ''', (date,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result or result['trips'] == 0:
        return jsonify(None), 200
    
    return jsonify({
        "date": str(result['date']),
        "trips": result['trips'],
        "avg_speed_kmh": round(result['avg_speed_kmh'], 2) if result['avg_speed_kmh'] else 0,
        "avg_distance_km": round(result['avg_distance_km'], 2) if result['avg_distance_km'] else 0,
        "avg_duration_min": round(result['avg_duration_min'], 2) if result['avg_duration_min'] else 0
    })

# INSIGHTS & ANALYTICS

@app.route('/api/insights/hourly', methods=['GET'])
@handle_errors
def get_hourly_insights():
    """Get trip distribution by hour of day"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            pickup_hour,
            COUNT(*) as trips
        FROM nyc_taxi_trips
        WHERE pickup_hour IS NOT NULL
        GROUP BY pickup_hour
        ORDER BY pickup_hour
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return jsonify(results)

@app.route('/api/insights/weekday-speed', methods=['GET'])
@handle_errors
def get_weekday_speed():
    """Get average speed by day of week"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            pickup_day_of_week,
            AVG(average_speed_mph * 1.60934) as avg_speed_kmh,
            COUNT(*) as trips
        FROM nyc_taxi_trips
        WHERE pickup_day_of_week IS NOT NULL
        GROUP BY pickup_day_of_week
        ORDER BY pickup_day_of_week
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    # Format results
    for row in results:
        row['avg_speed_kmh'] = round(row['avg_speed_kmh'], 2) if row['avg_speed_kmh'] else 0
    
    return jsonify(results)

@app.route('/api/insights/slow-hours', methods=['GET'])
@handle_errors
def get_slow_hours():
    """Get slowest traffic hours (seconds per km)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            pickup_hour,
            AVG(trip_duration / (trip_distance_miles * 1.60934)) as avg_sec_per_km,
            COUNT(*) as trips
        FROM nyc_taxi_trips
        WHERE pickup_hour IS NOT NULL 
            AND trip_distance_miles > 0
        GROUP BY pickup_hour
        ORDER BY pickup_hour
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    # Format results
    for row in results:
        row['avg_sec_per_km'] = round(row['avg_sec_per_km'], 2) if row['avg_sec_per_km'] else 0
    
    return jsonify(results)

@app.route('/api/insights/near', methods=['GET'])
@handle_errors
def get_nearby_trips():
    """Get trips near a specific location using Haversine formula"""
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        radius = float(request.args.get('radius', 1000))  # meters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 100))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid parameters"}), 400
    
    offset = (page - 1) * page_size
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Haversine formula for distance calculation
    # Result in meters
    cursor.execute('''
        SELECT 
            id,
            pickup_latitude,
            pickup_longitude,
            pickup_date as pickup_datetime,
            trip_distance_miles * 1.60934 as distance_km,
            average_speed_mph * 1.60934 as speed_kmh,
            (
                6371000 * acos(
                    cos(radians(%s)) * cos(radians(pickup_latitude)) * 
                    cos(radians(pickup_longitude) - radians(%s)) + 
                    sin(radians(%s)) * sin(radians(pickup_latitude))
                )
            ) as meters_away
        FROM nyc_taxi_trips
        HAVING meters_away <= %s
        ORDER BY meters_away
        LIMIT %s OFFSET %s
    ''', (lat, lon, lat, radius, page_size, offset))
    
    trips = cursor.fetchall()
    
    # Get total count
    cursor.execute('''
        SELECT COUNT(*) as total
        FROM (
            SELECT 
                (
                    6371000 * acos(
                        cos(radians(%s)) * cos(radians(pickup_latitude)) * 
                        cos(radians(pickup_longitude) - radians(%s)) + 
                        sin(radians(%s)) * sin(radians(pickup_latitude))
                    )
                ) as meters_away
            FROM nyc_taxi_trips
            HAVING meters_away <= %s
        ) as nearby_trips
    ''', (lat, lon, lat, radius))
    
    total = cursor.fetchone()['total']
    conn.close()
    
    # Format datetime fields
    for trip in trips:
        if trip.get('pickup_datetime'):
            trip['pickup_datetime'] = str(trip['pickup_datetime'])
    
    return jsonify({
        "page": page,
        "pageSize": page_size,
        "total": total,
        "data": trips
    })

# TRIPS - WITH FILTERING & SORTING

@app.route('/api/trips', methods=['GET'])
@handle_errors
def get_trips():
    """Get paginated trips with filtering and sorting"""
    # Pagination
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    offset = (page - 1) * page_size
    
    # Sorting
    sort_by = request.args.get('sortBy', 'pickup_date')
    sort_order = request.args.get('sortOrder', 'desc').upper()
    
    # Validate sort order
    if sort_order not in ['ASC', 'DESC']:
        sort_order = 'DESC'
    
    # Validate sort field (prevent SQL injection)
    valid_sort_fields = [
        'pickup_date', 'dropoff_datetime', 'trip_distance_miles',
        'trip_duration', 'average_speed_mph', 'passenger_count'
    ]
    if sort_by not in valid_sort_fields:
        sort_by = 'pickup_date'
    
    # Filters
    filters = []
    params = []
    
    # Date range filter
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    if start_date:
        filters.append('DATE(pickup_date) >= %s')
        params.append(start_date)
    if end_date:
        filters.append('DATE(pickup_date) <= %s')
        params.append(end_date)
    
    # Vendor filter
    vendor_id = request.args.get('vendorId')
    if vendor_id:
        filters.append('vendor_id = %s')
        params.append(vendor_id)
    
    # Passenger count filter
    passenger_count = request.args.get('passengerCount')
    if passenger_count:
        filters.append('passenger_count = %s')
        params.append(int(passenger_count))
    
    # Speed filters (convert km/h to mph for database query)
    min_speed = request.args.get('minSpeed')
    if min_speed:
        min_speed_mph = float(min_speed) / 1.60934
        filters.append('average_speed_mph >= %s')
        params.append(min_speed_mph)
    
    max_speed = request.args.get('maxSpeed')
    if max_speed:
        max_speed_mph = float(max_speed) / 1.60934
        filters.append('average_speed_mph <= %s')
        params.append(max_speed_mph)
    
    # Bounding box filter
    bbox = request.args.get('bbox')
    if bbox:
        try:
            west, south, east, north = map(float, bbox.split(','))
            filters.append('''
                pickup_longitude BETWEEN %s AND %s 
                AND pickup_latitude BETWEEN %s AND %s
            ''')
            params.extend([west, east, south, north])
        except ValueError:
            pass  # Invalid bbox format, skip
    
    # Build WHERE clause
    where_clause = ''
    if filters:
        where_clause = 'WHERE ' + ' AND '.join(filters)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get trips with conversions
    query = f'''
        SELECT 
            id, 
            vendor_id, 
            pickup_date as pickup_datetime,
            dropoff_datetime, 
            passenger_count,
            pickup_longitude, 
            pickup_latitude, 
            pickup_longitude as dropoff_longitude,
            pickup_latitude as dropoff_latitude,
            trip_duration, 
            trip_distance_miles * 1.60934 as distance_km,
            store_and_fwd_flag, 
            average_speed_mph * 1.60934 as speed_kmh,
            distance_category, 
            duration_category,
            time_period, 
            pickup_day_of_week, 
            is_weekend
        FROM nyc_taxi_trips
        {where_clause}
        ORDER BY {sort_by} {sort_order}
        LIMIT %s OFFSET %s
    '''
    
    params.extend([page_size, offset])
    cursor.execute(query, tuple(params))
    trips = cursor.fetchall()
    
    # Get total count with same filters
    count_query = f'''
        SELECT COUNT(*) as total 
        FROM nyc_taxi_trips
        {where_clause}
    '''
    cursor.execute(count_query, tuple(params[:-2]))  # Exclude LIMIT params
    total = cursor.fetchone()['total']
    
    conn.close()
    
    # Format results
    for trip in trips:
        if trip.get('pickup_datetime'):
            trip['pickup_datetime'] = str(trip['pickup_datetime'])
        if trip.get('dropoff_datetime'):
            trip['dropoff_datetime'] = str(trip['dropoff_datetime'])
        trip['distance_km'] = round(trip['distance_km'], 2) if trip['distance_km'] else 0
        trip['speed_kmh'] = round(trip['speed_kmh'], 2) if trip['speed_kmh'] else 0
    
    return jsonify({
        "page": page,
        "pageSize": page_size,
        "total": total,
        "data": trips
    })

@app.route('/api/trips/<trip_id>', methods=['GET'])
@handle_errors
def get_trip(trip_id):
    """Get a single trip by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            id, 
            vendor_id, 
            pickup_date as pickup_datetime,
            dropoff_datetime, 
            passenger_count,
            pickup_longitude, 
            pickup_latitude,
            trip_duration, 
            trip_distance_miles * 1.60934 as distance_km,
            store_and_fwd_flag, 
            average_speed_mph * 1.60934 as speed_kmh,
            distance_category, 
            duration_category,
            time_period, 
            pickup_day_of_week, 
            is_weekend
        FROM nyc_taxi_trips 
        WHERE id = %s
    ''', (trip_id,))
    
    trip = cursor.fetchone()
    conn.close()
    
    if trip:
        # Format datetime fields
        if trip.get('pickup_datetime'):
            trip['pickup_datetime'] = str(trip['pickup_datetime'])
        if trip.get('dropoff_datetime'):
            trip['dropoff_datetime'] = str(trip['dropoff_datetime'])
        trip['distance_km'] = round(trip['distance_km'], 2) if trip['distance_km'] else 0
        trip['speed_kmh'] = round(trip['speed_kmh'], 2) if trip['speed_kmh'] else 0
        return jsonify(trip)
    else:
        return jsonify({"error": "Trip not found"}), 404

# VENDOR STATISTICS

@app.route('/api/vendors', methods=['GET'])
@handle_errors
def get_vendor_stats():
    """Get statistics grouped by vendor"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            vendor_id, 
            COUNT(*) as total_trips, 
            AVG(trip_duration) as avg_duration,
            AVG(trip_distance_miles * 1.60934) as avg_distance_km, 
            AVG(average_speed_mph * 1.60934) as avg_speed_kmh,
            AVG(passenger_count) as avg_passengers
        FROM nyc_taxi_trips
        GROUP BY vendor_id
        ORDER BY total_trips DESC
    ''')
    
    vendors = cursor.fetchall()
    conn.close()
    
    # Format results
    for vendor in vendors:
        vendor['avg_duration'] = round(vendor['avg_duration'], 2) if vendor['avg_duration'] else 0
        vendor['avg_distance_km'] = round(vendor['avg_distance_km'], 2) if vendor['avg_distance_km'] else 0
        vendor['avg_speed_kmh'] = round(vendor['avg_speed_kmh'], 2) if vendor['avg_speed_kmh'] else 0
        vendor['avg_passengers'] = round(vendor['avg_passengers'], 2) if vendor['avg_passengers'] else 0
    
    return jsonify({"vendors": vendors})

# RUN SERVER
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    