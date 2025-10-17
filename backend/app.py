from flask import Flask, jsonify, request
from flask_cors import CORS
import pymysql
import os


app = Flask(__name__)
CORS(app)

# MySQL connection configuration (adjust these with your environment variables)
DB_HOST = os.getenv("MYSQL_HOST", "nyc_taxi_db")
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", '')
DB_NAME = os.getenv("MYSQL_DATABASE", "nyc_taxi_db")
DB_PORT = int(os.getenv("MYSQL_PORT", 3306))

def get_db_connection():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn



@app.route('/api/health', methods=['GET'])

def health_check():
    return jsonify({"status": "healthy"})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total_rows FROM nyc_taxi_trips')
    total_rows = cursor.fetchone()['total_rows']
    
    cursor.execute('SELECT AVG(average_speed_mph) as avg_speed_mph, AVG(trip_distance_miles) as avg_distance_miles FROM nyc_taxi_trips')
    stats = cursor.fetchone()
    
    conn.close()
    
    return jsonify({
        "total_rows": total_rows,
        "avg_speed_mph": round(stats['avg_speed_mph'], 2) if stats['avg_speed_mph'] else 0,
        "avg_distance_miles": round(stats['avg_distance_miles'], 2) if stats['avg_distance_miles'] else 0
    })

@app.route('/api/trips', methods=['GET'])
def get_trips():
    conn = get_db_connection()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    offset = (page - 1) * page_size
    
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, vendor_id, pickup_date, dropoff_datetime, passenger_count,
               pickup_longitude, pickup_latitude, trip_duration, trip_distance_miles,
               store_and_fwd_flag, average_speed_mph, distance_category, duration_category,
               time_period, pickup_day_of_week, is_weekend
        FROM nyc_taxi_trips
        ORDER BY pickup_date DESC
        LIMIT %s OFFSET %s
    ''', (page_size, offset))
    
    trips = cursor.fetchall()
    
    cursor.execute('SELECT COUNT(*) as total FROM nyc_taxi_trips')
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
        SELECT id, vendor_id, pickup_date, dropoff_datetime, passenger_count,
               pickup_longitude, pickup_latitude, trip_duration, trip_distance_miles,
               store_and_fwd_flag, average_speed_mph, distance_category, duration_category,
               time_period, pickup_day_of_week, is_weekend
        FROM nyc_taxi_trips WHERE id = %s
    ''', (trip_id,))
    
    trip = cursor.fetchone()
    conn.close()
    
    if trip:
        return jsonify(trip)
    else:
        return jsonify({"error": "Trip not found"}), 404



@app.route('/api/vendors', methods=['GET'])
def get_vendor_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT vendor_id, COUNT(*) as total_trips, 
               AVG(trip_duration) as avg_duration,
               AVG(trip_distance_miles) as avg_distance, 
               AVG(average_speed_mph) as avg_speed,
               AVG(passenger_count) as avg_passengers
        FROM nyc_taxi_trips
        GROUP BY vendor_id
        ORDER BY total_trips DESC
    ''')
    
    vendors = cursor.fetchall()
    conn.close()
    
    return jsonify({"vendors": vendors})



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
