from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'nyc_taxi_db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def haversine_distance(lat1, lon1, lat2, lon2):
    import math
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return c * 6371

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total_rows FROM trips')
    total_rows = cursor.fetchone()['total_rows']
    
    cursor.execute('SELECT AVG(trip_speed) as avg_speed_kmh, AVG(calculated_distance) as avg_distance_km FROM trips')
    stats = cursor.fetchone()
    
    conn.close()
    
    return jsonify({
        "total_rows": total_rows,
        "avg_speed_kmh": round(stats['avg_speed_kmh'], 2) if stats['avg_speed_kmh'] else 0,
        "avg_distance_km": round(stats['avg_distance_km'], 2) if stats['avg_distance_km'] else 0
    })

@app.route('/api/summary', methods=['GET'])
def get_summary():
    date = request.args.get('date')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) as trips, 
               AVG(trip_speed) as avg_speed_kmh,
               AVG(calculated_distance) as avg_distance_km,
               AVG(trip_duration) as avg_duration_sec
        FROM trips 
        WHERE date(pickup_datetime) = ?
    ''', (date,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result or result['trips'] == 0:
        return jsonify(None)
    
    return jsonify({
        "date": date,
        "trips": result['trips'],
        "avg_speed_kmh": round(result['avg_speed_kmh'], 2) if result['avg_speed_kmh'] else 0,
        "avg_distance_km": round(result['avg_distance_km'], 2) if result['avg_distance_km'] else 0,
        "avg_duration_min": round(result['avg_duration_sec'] / 60, 2) if result['avg_duration_sec'] else 0
    })

@app.route('/api/insights/hourly', methods=['GET'])
def get_hourly_insights():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT strftime('%H', pickup_datetime) as pickup_hour, 
               COUNT(*) as trips
        FROM trips 
        GROUP BY strftime('%H', pickup_datetime)
        ORDER BY pickup_hour
    ''')
    
    hourly_data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(hourly_data)

@app.route('/api/insights/weekday', methods=['GET'])
def get_weekday_insights():
    """Get trips by weekday for D3 visualization"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT day_of_week, COUNT(*) as trips
        FROM trips 
        WHERE day_of_week IS NOT NULL
        GROUP BY day_of_week
        ORDER BY 
            CASE day_of_week
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
            END
    ''')
    
    weekday_data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(weekday_data)

@app.route('/api/insights/weekday-speed', methods=['GET'])
def get_weekday_speed():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT day_of_week, 
               AVG(trip_speed) as avg_speed_kmh
        FROM trips 
        GROUP BY day_of_week
        ORDER BY 
            CASE day_of_week
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
            END
    ''')
    
    weekday_data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(weekday_data)

@app.route('/api/insights/slow-hours', methods=['GET'])
def get_slow_hours():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT strftime('%H', pickup_datetime) as pickup_hour, 
               AVG(trip_duration / calculated_distance) as avg_sec_per_km
        FROM trips 
        WHERE calculated_distance > 0
        GROUP BY strftime('%H', pickup_datetime)
        ORDER BY pickup_hour
    ''')
    
    slow_data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(slow_data)

@app.route('/api/insights/time-periods', methods=['GET'])
def get_time_period_insights():
    """Get trips by time period for D3 visualization"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT time_period, COUNT(*) as trips
        FROM trips 
        WHERE time_period IS NOT NULL
        GROUP BY time_period
        ORDER BY 
            CASE time_period
                WHEN 'late_night' THEN 1
                WHEN 'morning_rush' THEN 2
                WHEN 'midday' THEN 3
                WHEN 'evening_rush' THEN 4
                WHEN 'night' THEN 5
            END
    ''')
    
    time_data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(time_data)

@app.route('/api/trips', methods=['GET'])
def get_trips():
    conn = get_db_connection()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    offset = (page - 1) * page_size
    
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, vendor_id, pickup_datetime, dropoff_datetime, passenger_count,
               pickup_longitude, pickup_latitude, dropoff_longitude, dropoff_latitude,
               store_and_fwd_flag, trip_duration, trip_speed as speed_kmh,
               calculated_distance as distance_km, time_period, day_of_week,
               is_weekend, efficiency_ratio
        FROM trips 
        ORDER BY pickup_datetime DESC 
        LIMIT ? OFFSET ?
    ''', (page_size, offset))
    
    trips = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('SELECT COUNT(*) as total FROM trips')
    total = cursor.fetchone()['total']
    conn.close()
    
    return jsonify({
        "page": page,
        "pageSize": page_size,
        "total": total,
        "data": trips
    })

@app.route('/api/trips/<trip_id>', methods=['GET'])
def get_trip(trip_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, vendor_id, pickup_datetime, dropoff_datetime, passenger_count,
               pickup_longitude, pickup_latitude, dropoff_longitude, dropoff_latitude,
               store_and_fwd_flag, trip_duration, trip_speed as speed_kmh,
               calculated_distance as distance_km, time_period, day_of_week,
               is_weekend, efficiency_ratio
        FROM trips WHERE id = ?
    ''', (trip_id,))
    
    trip = cursor.fetchone()
    conn.close()
    
    if trip:
        return jsonify(dict(trip))
    else:
        return jsonify({"error": "Trip not found"}), 404

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) as total_trips, 
               AVG(trip_duration) as avg_duration,
               AVG(calculated_distance) as avg_distance, 
               AVG(trip_speed) as avg_speed,
               AVG(passenger_count) as avg_passengers,
               AVG(efficiency_ratio) as avg_efficiency
        FROM trips
    ''')
    stats = dict(cursor.fetchone())
    
    cursor.execute('''
        SELECT time_period, COUNT(*) as trip_count, 
               AVG(trip_duration) as avg_duration,
               AVG(trip_speed) as avg_speed
        FROM trips 
        WHERE time_period IS NOT NULL
        GROUP BY time_period 
        ORDER BY trip_count DESC
    ''')
    time_stats = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('''
        SELECT day_of_week, COUNT(*) as trip_count, 
               AVG(trip_duration) as avg_duration
        FROM trips 
        WHERE day_of_week IS NOT NULL
        GROUP BY day_of_week 
        ORDER BY trip_count DESC
    ''')
    day_stats = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({
        "overall": stats, 
        "time_periods": time_stats, 
        "days": day_stats
    })

@app.route('/api/insights', methods=['GET'])
def get_insights():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT time_period, day_of_week, is_weekend,
                   COUNT(*) as total_trips,
                   AVG(trip_duration) as avg_duration,
                   AVG(calculated_distance) as avg_distance,
                   AVG(trip_speed) as avg_speed,
                   AVG(efficiency_ratio) as avg_efficiency
            FROM trips 
            GROUP BY time_period, day_of_week, is_weekend
            ORDER BY total_trips DESC
        ''')
        
        patterns = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({"traffic_pattern_analysis": patterns})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/trips/filter', methods=['GET'])
def filter_trips():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    time_period = request.args.get('time_period')
    day_of_week = request.args.get('day_of_week')
    vendor_id = request.args.get('vendor_id')
    min_passengers = request.args.get('min_passengers')
    min_speed = request.args.get('minSpeed')
    max_speed = request.args.get('maxSpeed')
    
    if time_period:
        conditions.append("time_period = ?")
        params.append(time_period)
    if day_of_week:
        conditions.append("day_of_week = ?")
        params.append(day_of_week)
    if vendor_id:
        conditions.append("vendor_id = ?")
        params.append(int(vendor_id))
    if min_passengers:
        conditions.append("passenger_count >= ?")
        params.append(int(min_passengers))
    if min_speed:
        conditions.append("trip_speed >= ?")
        params.append(float(min_speed))
    if max_speed:
        conditions.append("trip_speed <= ?")
        params.append(float(max_speed))
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    query = f'''
        SELECT id, vendor_id, pickup_datetime, dropoff_datetime, passenger_count,
               pickup_longitude, pickup_latitude, dropoff_longitude, dropoff_latitude,
               store_and_fwd_flag, trip_duration, trip_speed as speed_kmh,
               calculated_distance as distance_km, time_period, day_of_week
        FROM trips WHERE {where_clause} 
        ORDER BY pickup_datetime DESC 
        LIMIT 100
    '''
    
    cursor.execute(query, params)
    trips = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({"trips": trips, "count": len(trips)})

@app.route('/api/vendors', methods=['GET'])
def get_vendor_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT vendor_id, COUNT(*) as total_trips, 
               AVG(trip_duration) as avg_duration,
               AVG(calculated_distance) as avg_distance, 
               AVG(trip_speed) as avg_speed,
               AVG(passenger_count) as avg_passengers
        FROM trips 
        GROUP BY vendor_id 
        ORDER BY total_trips DESC
    ''')
    
    vendors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({"vendors": vendors})

@app.route('/api/insights/near', methods=['GET'])
def get_near_trips():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius = request.args.get('radius', 1000, type=float)
    
    if not lat or not lon:
        return jsonify({"error": "Latitude and longitude required"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, pickup_datetime, pickup_latitude, pickup_longitude,
               (6371 * acos(cos(radians(?)) * cos(radians(pickup_latitude)) * 
               cos(radians(pickup_longitude) - radians(?)) + 
               sin(radians(?)) * sin(radians(pickup_latitude)))) as meters_away
        FROM trips
        WHERE meters_away < ?
        ORDER BY meters_away
        LIMIT 100
    ''', (lat, lon, lat, radius/1000))
    
    nearby_trips = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        "data": nearby_trips,
        "count": len(nearby_trips)
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)