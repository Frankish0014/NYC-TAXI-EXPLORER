# NYC Taxi Trip Explorer - Backend

A Flask backend API for analyzing NYC taxi trip data with custom algorithms.

## Setup

1. **Clone and setup environment:**
   \\\ash
   git clone <repo-url>
   cd NYC-TAXI-EXPLORER
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   \\\

2. **Download dataset from Kaggle NYC Taxi Trip Duration competition**
3. **Place train.csv in data/raw/**
4. **Initialize database:**
   \\\ash
   python scripts/create_nyc_database.py
   python scripts/process_nyc_data.py
   \\\
5. **Start backend:**
   \\\ash
   cd backend
   python app.py
   \\\

## API Endpoints
- GET /api/health
- GET /api/trips
- GET /api/statistics
- GET /api/insights
- GET /api/trips/filter
- GET /api/vendors

