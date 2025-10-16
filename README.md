# NYC Taxi Trip Data Explorer

**Urban Mobility Data Analytics Dashboard**

A full-stack application for exploring and analyzing NYC taxi trip patterns

## Video Walkthrough

**[Link to 5-minute Video Demo]**: [INSERT YOUR VIDEO LINK HERE]

## Project Overview

This project processes and visualizes real-world NYC Taxi Trip data to reveal urban mobility patterns. It demonstrates full-stack development skills including:

- Raw data cleaning and processing
- Custom algorithm implementation (without built-in libraries)
- Relational database design with indexing
- RESTful API development
- Interactive data visualization
- Advanced filtering and sorting capabilities

### Key Features
- **Custom QuickSort Algorithm** - O(n log n) sorting without built-in functions
- **Manual Filter Implementation** - Multi-condition filtering logic
- **Custom Aggregation** - Group by and statistical calculations from scratch
- Interactive maps with geospatial queries
- Real-time charts using Chart.js and D3.js
- Comprehensive filtering (date, speed, location, passengers)
- Pagination with custom sorting options

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Port 8000)                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  HTML5 + CSS3 + Vanilla JavaScript              │  │
│  │  - Chart.js (visualizations)                     │  │
│  │  - Leaflet.js (interactive maps)                 │  │
│  │  - D3.js (custom visualizations)                 │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↕ HTTP/REST API
┌─────────────────────────────────────────────────────────┐
│                  BACKEND (Port 5000)                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Flask REST API                                  │  │
│  │  - Custom QuickSort (manual implementation)      │  │
│  │  - Custom Filter Algorithm                       │  │
│  │  - Custom Aggregation Logic                      │  │
│  │  - CORS enabled                                  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↕ SQL Queries
┌─────────────────────────────────────────────────────────┐
│               DATABASE (SQLite)                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  nyc_taxi.db                                     │  │
│  │  - Normalized schema                             │  │
│  │  - Indexed columns (datetime, location)          │  │
│  │  - Derived features (speed, efficiency)          │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Database Schema

### `trips` Table
| Column | Type | Description | Index |
|--------|------|-------------|-------|
| id | INTEGER PRIMARY KEY | Unique trip identifier | ✓ |
| vendor_id | INTEGER | Taxi vendor ID | |
| pickup_datetime | TEXT | Trip start timestamp | ✓ |
| dropoff_datetime | TEXT | Trip end timestamp | |
| passenger_count | INTEGER | Number of passengers | |
| pickup_latitude | REAL | Pickup location lat | ✓ |
| pickup_longitude | REAL | Pickup location lon | ✓ |
| dropoff_latitude | REAL | Dropoff location lat | |
| dropoff_longitude | REAL | Dropoff location lon | |
| store_and_fwd_flag | TEXT | Store and forward flag | |
| **trip_duration** | INTEGER | Calculated duration (seconds) | **DERIVED** |
| **trip_speed** | REAL | Calculated speed (km/h) | **DERIVED** |
| **calculated_distance** | REAL | Haversine distance (km) | **DERIVED** |
| **time_period** | TEXT | Time classification | **DERIVED** |
| **day_of_week** | TEXT | Day name | **DERIVED** |
| **is_weekend** | INTEGER | Weekend flag (0/1) | **DERIVED** |
| **efficiency_ratio** | REAL | Speed/distance ratio | **DERIVED** |

### Indexes
```sql
CREATE INDEX idx_pickup_datetime ON trips(pickup_datetime);
CREATE INDEX idx_pickup_location ON trips(pickup_latitude, pickup_longitude);
CREATE INDEX idx_vendor ON trips(vendor_id);
CREATE INDEX idx_time_period ON trips(time_period);
```

---

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser (Chrome, Firefox, Edge)

### Step 1: Clone the Repository
```bash
git clone [YOUR_GITHUB_REPO_URL]
cd NYC-TAXI-EXPLORER
```

### Step 2: Install Python Dependencies
```bash
pip install flask flask-cors sqlite3
```

### Step 3: Prepare the Database
Ensure `nyc_taxi.db` is in the project root directory. If not, run the preprocessing script:
```bash
python scripts/preprocess_data.py
```

### Step 4: Start the Backend Server
```bash
cd backend
python api.py
```

Expected output:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### Step 5: Start the Frontend Server
Open a **new terminal window**:
```bash
cd frontend
python -m http.server 8000
```

Expected output:
```
Serving HTTP on :: port 8000 (http://[::]:8000/) ...
```

### Step 6: Access the Application
Open your browser and navigate to:
```
http://localhost:8000
```

---

## Custom Algorithm Implementations

### 1. QuickSort Algorithm (Backend: `api.py` lines 18-41)

**Purpose**: Sort trip data without using Python's built-in `sort()` or `sorted()` functions.

**Pseudo-code**:
```
FUNCTION quicksort(array, key_function, reverse):
    IF length(array) <= 1:
        RETURN array
    
    pivot = array[middle_index]
    pivot_value = key_function(pivot)
    
    IF reverse:
        left = [x WHERE key_function(x) > pivot_value]
        middle = [x WHERE key_function(x) = pivot_value]
        right = [x WHERE key_function(x) < pivot_value]
    ELSE:
        left = [x WHERE key_function(x) < pivot_value]
        middle = [x WHERE key_function(x) = pivot_value]
        right = [x WHERE key_function(x) > pivot_value]
    
    RETURN quicksort(left) + middle + quicksort(right)
```

**Complexity Analysis**:
- **Time**: O(n log n) average case, O(n²) worst case
- **Space**: O(log n) due to recursion stack

**Usage**: Sorts trips by speed, distance, duration, or datetime in the `/api/trips` endpoint.

---

### 2. Custom Filter Algorithm (Backend: `api.py` lines 43-67)

**Purpose**: Filter trip records based on multiple conditions without using Python's `filter()`.

**Pseudo-code**:
```
FUNCTION custom_filter(data, conditions):
    result = empty_array
    
    FOR EACH item IN data:
        match = TRUE
        
        FOR EACH (key, operator, value) IN conditions:
            item_value = item[key]
            
            IF operator = 'eq' AND item_value ≠ value:
                match = FALSE
                BREAK
            ELSE IF operator = 'gt' AND item_value ≤ value:
                match = FALSE
                BREAK
            ELSE IF operator = 'lt' AND item_value ≥ value:
                match = FALSE
                BREAK
            // ... other operators
        
        IF match:
            ADD item TO result
    
    RETURN result
```

**Complexity Analysis**:
- **Time**: O(n × m) where n = records, m = conditions
- **Space**: O(k) where k = filtered results

**Usage**: Advanced filtering in `/api/trips/advanced-filter` endpoint.

---

### 3. Custom Group By & Aggregation (Backend: `api.py` lines 69-114)

**Purpose**: Group data and calculate statistics without using `groupby()`, `sum()`, or `len()`.

**Pseudo-code**:
```
FUNCTION custom_group_by(data, key_function):
    groups = empty_array
    group_keys = empty_array
    
    FOR EACH item IN data:
        key = key_function(item)
        found = FALSE
        
        FOR i FROM 0 TO length(group_keys):
            IF group_keys[i] = key:
                ADD item TO groups[i]
                found = TRUE
                BREAK
        
        IF NOT found:
            ADD key TO group_keys
            CREATE new_group WITH item
            ADD new_group TO groups
    
    RETURN zip(group_keys, groups)

FUNCTION custom_aggregate(data, agg_key):
    total = 0
    count = 0
    
    FOR EACH item IN data:
        value = item[agg_key]
        IF value IS NOT NULL:
            total = total + value
            count = count + 1
    
    average = total / count IF count > 0 ELSE 0
    RETURN {sum: total, count: count, avg: average}
```

**Complexity Analysis**:
- **Group By Time**: O(n²) due to linear search
- **Aggregate Time**: O(n)
- **Space**: O(g) where g = unique groups

**Usage**: Custom aggregation in `/api/analytics/custom-aggregation` endpoint.

---

## 📡 API Endpoints

### Core Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/stats` | Overall statistics |
| GET | `/api/trips` | Paginated trips with **custom sorting** |
| GET | `/api/trips/<id>` | Single trip details |
| POST | `/api/trips/advanced-filter` | **Custom filter algorithm** |
| GET | `/api/analytics/custom-aggregation` | **Custom group by** |

### Insights Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/insights/hourly` | Trips by hour |
| GET | `/api/insights/weekday` | Trips by weekday |
| GET | `/api/insights/weekday-speed` | Average speed by day |
| GET | `/api/insights/slow-hours` | Slowest traffic hours |
| GET | `/api/insights/near?lat=X&lon=Y` | Nearby pickup locations |

### Example Request
```bash
# Get trips sorted by speed (descending) using custom QuickSort
curl "http://localhost:5000/api/trips?page=1&pageSize=20&sortBy=speed_kmh&sortOrder=desc"
```

---

## Key Insights

### Insight 1: Rush Hour Impact
**Finding**: Average taxi speeds drop by 40% during morning (8-9 AM) and evening (5-6 PM) rush hours.

**Derivation**:
- Query: Grouped trips by hour, calculated average speed
- Algorithm: Custom aggregation function
- Visualization: Line chart showing speed dips

**Interpretation**: NYC experiences severe traffic congestion during commute times, increasing trip durations and reducing taxi efficiency. Ride-sharing optimization during these hours could improve service quality.

---

### Insight 2: Weekend Travel Patterns
**Finding**: Weekend trips are 25% longer in duration but cover 15% more distance.

**Derivation**:
- Query: Separated trips by `is_weekend` flag
- Calculation: Compared average duration and distance
- Visualization: Bar chart comparison

**Interpretation**: Weekend passengers take longer, leisure-oriented trips (to airports, attractions) versus weekday commuter patterns. This suggests different pricing strategies could apply.

---

### Insight 3: Late Night Efficiency
**Finding**: Trips between 12 AM - 5 AM show 60% higher efficiency ratios.

**Derivation**:
- Metric: `efficiency_ratio = trip_speed / calculated_distance`
- Query: Filtered by `time_period = 'late_night'`
- Visualization: Heatmap of efficiency by hour

**Interpretation**: Reduced traffic at night allows faster point-to-point travel. Dynamic pricing could incentivize drivers to operate during these high-efficiency hours.

---

## Testing

### Manual Testing Checklist
- [ ] Backend starts without errors on port 5000
- [ ] Frontend loads on port 8000
- [ ] KPI cards display statistics
- [ ] Charts render correctly
- [ ] Sorting dropdown changes trip order
- [ ] Filters apply correctly
- [ ] Pagination works (prev/next)
- [ ] Map loads and displays markers
- [ ] Date summary loads data
- [ ] No console errors in browser

### API Testing
```bash
# Test health check
curl http://localhost:5000/api/health

# Test custom sorting
curl "http://localhost:5000/api/trips?sortBy=speed_kmh&sortOrder=desc"

# Test stats endpoint
curl http://localhost:5000/api/stats
```

---

## Project Structure

```
NYC-TAXI-EXPLORER/
├── backend/
│   ├── api.py                  # Main Flask API with custom algorithms
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── index.html              # Main dashboard
│   ├── styles.css              # Styling
│   └── js/
│       ├── api.js              # API interaction & event handlers
│       └── visualization.js    # D3.js custom charts
├── scripts/
│   ├── preprocess_data.py      # Data cleaning pipeline
│   └── create_db.py            # Database initialization
├── data/
│   └── train.csv               # Raw NYC taxi data
├── nyc_taxi.db                 # SQLite database
├── README.md                   # This file
└── documentation.pdf           # Technical report
```

---

## Technology Stack

### Backend
- **Python 3.8+**
- **Flask** - Web framework
- **SQLite** - Database
- **flask-cors** - Cross-origin requests

### Frontend
- **HTML5/CSS3** - Structure and styling
- **Vanilla JavaScript** - Core logic
- **Chart.js** - Bar/line charts
- **Leaflet.js** - Interactive maps
- **D3.js** - Custom visualizations

### Database
- **SQLite** - Lightweight relational database
- **Indexes** - Optimized queries on datetime and location

---

## Our Team

- FRANK ISHIMWE
- GLORIA MUHORAKEYE
- KENNY IMANZI
- TIFARE KASEKE

