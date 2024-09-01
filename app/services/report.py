import os
import uuid
import pandas as pd
import pytz
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Directory to store reports
REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:mysecretpassword@db:5432/test_db')

# Create a database engine
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def get_db_connection():
    """Create and return a database connection."""
    try:
        return engine.connect()
    except SQLAlchemyError as e:
        print(f"An error occurred while connecting to the database: {e}")
        raise

def generate_report():
    report_id = str(uuid.uuid4())

    try:
        # Generate report data
        report_data = compute_report_data()
        report_file_path = os.path.join(REPORT_DIR, f"{report_id}.csv")

        # Save report data to CSV file
        df = pd.DataFrame(report_data)
        df.to_csv(report_file_path, index=False)

        # Save report status to DB
        with get_db_connection() as conn:
            # Ensure the report_status table exists
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS report_status (
                    report_id TEXT PRIMARY KEY,
                    status TEXT,
                    file_path TEXT
                )
            """))

            # Insert or update report status
            query = text("""
                INSERT INTO report_status (report_id, status, file_path)
                VALUES (:report_id, :status, :file_path)
                ON CONFLICT (report_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    file_path = EXCLUDED.file_path
            """)
            conn.execute(query, {"report_id": report_id, "status": "Complete", "file_path": report_file_path})
        
        return report_id
    except SQLAlchemyError as e:
        print(f"An error occurred while generating the report: {e}")
        return None

def compute_report_data():
    # Define the timezone (UTC)
    utc = pytz.UTC

    # Get current time and time intervals with timezone awareness
    now = datetime.now(utc)
    last_hour_start = now - timedelta(hours=1)
    last_day_start = now - timedelta(days=1)
    last_week_start = now - timedelta(weeks=1)

    try:
        with get_db_connection() as conn:
            # Load data from database
            store_data = pd.read_sql_query("SELECT * FROM store_data", conn)
            business_hours = pd.read_sql_query("SELECT * FROM business_hours", conn)
            timezones = pd.read_sql_query("SELECT * FROM timezones", conn)

        # Merge tables to have all needed information in one DataFrame
        data = store_data.merge(timezones, on="store_id", how="left")
        data = data.merge(business_hours, on="store_id", how="left")

        # Fill missing timezones and business hours with defaults
        data["timezone_str"] = data["timezone_str"].fillna("America/Chicago")
        data["start_time_local"] = data["start_time_local"].fillna("00:00")
        data["end_time_local"] = data["end_time_local"].fillna("23:59")

        def calculate_uptime_downtime(store_df):
            # Convert status timestamps to datetime
            store_df['timestamp_utc'] = pd.to_datetime(store_df['timestamp_utc']).dt.tz_localize('UTC')
            
            # Filter data for the last hour, day, week
            df_last_hour = store_df[store_df['timestamp_utc'] >= last_hour_start]
            df_last_day = store_df[store_df['timestamp_utc'] >= last_day_start]
            df_last_week = store_df[store_df['timestamp_utc'] >= last_week_start]
            
            def calculate_period(df):
                uptime = df[df['status'] == 'active'].shape[0]
                downtime = df[df['status'] == 'inactive'].shape[0]
                return uptime, downtime
            
            # Calculate uptime and downtime for each period
            uptime_last_hour, downtime_last_hour = calculate_period(df_last_hour)
            uptime_last_day, downtime_last_day = calculate_period(df_last_day)
            uptime_last_week, downtime_last_week = calculate_period(df_last_week)
            
            # Assuming 60 minutes per hour, 1440 minutes per day, 10080 minutes per week
            uptime_last_hour = (uptime_last_hour / 60)  # in minutes
            uptime_last_day = (uptime_last_day / 1440)  # in hours
            uptime_last_week = (uptime_last_week / 10080)  # in hours
            
            downtime_last_hour = (downtime_last_hour / 60)  # in minutes
            downtime_last_day = (downtime_last_day / 1440)  # in hours
            downtime_last_week = (downtime_last_week / 10080)  # in hours

            return {
                'store_id': store_df['store_id'].iloc[0],
                'uptime_last_hour': uptime_last_hour,
                'uptime_last_day': uptime_last_day,
                'uptime_last_week': uptime_last_week,
                'downtime_last_hour': downtime_last_hour,
                'downtime_last_day': downtime_last_day,
                'downtime_last_week': downtime_last_week
            }

        # Group by store_id and calculate metrics
        report_data = []
        for store_id, group in data.groupby('store_id'):
            report_data.append(calculate_uptime_downtime(group))

        return report_data
    except Exception as e:
        print(f"An error occurred while computing report data: {e}")
        return []

def get_report_status(report_id: str):
    try:
        with get_db_connection() as conn:
            # Ensure the table exists
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS report_status (
                    report_id TEXT PRIMARY KEY,
                    status TEXT,
                    file_path TEXT
                );
                """)
            )
            # Check report status
            query = text("""
                SELECT status, file_path
                FROM report_status
                WHERE report_id = :report_id
            """)
            result = conn.execute(query, {"report_id": report_id}).fetchone()

            if result:
                status, file_path = result
                if status == "Complete":
                    # Check if file exists
                    if os.path.exists(file_path):
                        return {"status": status, "file_path": file_path}
                    else:
                        return {"status": "Error", "message": "Report file not found"}
                else:
                    return {"status": "Running"}
            else:
                return {"status": "Unknown", "message": "Report ID not found"}
    except Exception as e:
        print(f"An error occurred while getting report status: {e}")
        return {"status": "Error", "message": str(e)}
