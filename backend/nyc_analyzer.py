import sqlite3
import math
import os

class NYCTripAnalyzer:
    def __init__(self, db_path=None):
        if db_path is None:
            self.db_path = os.path.join(os.path.dirname(__file__), '..', 'nyc_taxi.db')
        else:
            self.db_path = db_path
    
    def manual_percentile(self, data, percentile):
        if not data:
            return 0
        sorted_data = self.manual_bubble_sort(data.copy())
        k = (len(sorted_data) - 1) * percentile / 100
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_data[int(k)]
        else:
            return sorted_data[int(f)] * (c - k) + sorted_data[int(c)] * (k - f)
    
    def manual_bubble_sort(self, data):
        n = len(data)
        for i in range(n):
            for j in range(0, n - i - 1):
                if data[j] > data[j + 1]:
                    data[j], data[j + 1] = data[j + 1], data[j]
        return data
    
    def analyze_traffic_patterns(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT time_period, trip_duration, calculated_distance, efficiency_ratio FROM trips LIMIT 10000')
        data = cursor.fetchall()
        
        time_periods = {}
        for row in data:
            time_period, duration, distance, efficiency = row
            if time_period not in time_periods:
                time_periods[time_period] = {
                    'durations': [],
                    'distances': [],
                    'efficiencies': []
                }
            time_periods[time_period]['durations'].append(duration)
            time_periods[time_period]['distances'].append(distance)
            time_periods[time_period]['efficiencies'].append(efficiency)
        
        results = {}
        for period, values in time_periods.items():
            durations = values['durations']
            total = 0
            count = 0
            for duration in durations:
                total += duration
                count += 1
            mean_duration = total / count if count > 0 else 0
            median = self.manual_percentile(durations, 50)
            p75 = self.manual_percentile(durations, 75)
            p90 = self.manual_percentile(durations, 90)
            
            results[period] = {
                'mean_duration': mean_duration,
                'median_duration': median,
                'p75_duration': p75,
                'p90_duration': p90,
                'trip_count': count
            }
        
        conn.close()
        return results

if __name__ == '__main__':
    analyzer = NYCTripAnalyzer()
    traffic_patterns = analyzer.analyze_traffic_patterns()
    
    print("=== NYC TRAFFIC PATTERN ANALYSIS ===")
    for period, stats in traffic_patterns.items():
        print(f"\n{period.upper()}:")
        print(f"  Trips: {stats['trip_count']}")
        print(f"  Avg Duration: {stats['mean_duration']/60:.1f} min")
        print(f"  Median Duration: {stats['median_duration']/60:.1f} min")
        print(f"  75th Percentile: {stats['p75_duration']/60:.1f} min")
