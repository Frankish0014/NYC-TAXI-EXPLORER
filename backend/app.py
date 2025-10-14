from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'nyc_taxi.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/api/trips', methods=['GET'])
def get_trips():
    conn = get_db_connection()
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    offset = (page - 1) * limit
    
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trips ORDER BY pickup_datetime DESC LIMIT ? OFFSET ?', (limit, offset))
    trips = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('SELECT COUNT(*) as total FROM trips')
    total = cursor.fetchone()['total']
    conn.close()
    
    return jsonify({
        "trips": trips,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    })

@app.route('/api/trips/<trip_id>', methods=['GET'])
def get_trip(trip_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trips WHERE id = ?', (trip_id,))
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
        SELECT COUNT(*) as total_trips, AVG(trip_duration) as avg_duration,
               AVG(calculated_distance) as avg_distance, AVG(trip_speed) as avg_speed,
               AVG(passenger_count) as avg_passengers
        FROM trips
    ''')
    stats = dict(cursor.fetchone())
    
    cursor.execute('''
        SELECT time_period, COUNT(*) as trip_count, AVG(trip_duration) as avg_duration,
               AVG(trip_speed) as avg_speed
        FROM trips GROUP BY time_period ORDER BY trip_count DESC
    ''')
    time_stats = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('''
        SELECT day_of_week, COUNT(*) as trip_count, AVG(trip_duration) as avg_duration
        FROM trips GROUP BY day_of_week ORDER BY trip_count DESC
    ''')
    day_stats = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({"overall": stats, "time_periods": time_stats, "days": day_stats})

@app.route('/api/insights', methods=['GET'])
def get_insights():
    try:
        import sys
        sys.path.append(os.path.dirname(__file__))
        from nyc_analyzer import NYCTripAnalyzer
        analyzer = NYCTripAnalyzer()
        traffic_patterns = analyzer.analyze_traffic_patterns()
        return jsonify({"traffic_pattern_analysis": traffic_patterns})
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
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    query = f"SELECT * FROM trips WHERE {where_clause} ORDER BY pickup_datetime DESC LIMIT 100"
    
    cursor.execute(query, params)
    trips = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({"trips": trips, "count": len(trips)})

@app.route('/api/vendors', methods=['GET'])
def get_vendor_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT vendor_id, COUNT(*) as total_trips, AVG(trip_duration) as avg_duration,
               AVG(calculated_distance) as avg_distance, AVG(trip_speed) as avg_speed
        FROM trips GROUP BY vendor_id ORDER BY total_trips DESC
    ''')
    vendors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({"vendors": vendors})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
