import pandas as pd
from db.setup import get_db_connection
from datetime import datetime, timedelta 
import sqlite3
import uuid
import os
import pytz

# Directory to store reports
REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)


def generate_report():
    report_id = str(uuid.uuid4())

    # Generate report data
    report_data = compute_report_data()  # Function that computes the report data
    report_file_path = os.path.join(REPORT_DIR, f"{report_id}.csv")

    # Save report data to CSV file
    df = pd.DataFrame(report_data)
    df.to_csv(report_file_path, index=False)

    # Save report status to DB
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO report_status (report_id, status, file_path)
            VALUES (?, ?, ?)
        """,
            (report_id, "Complete", report_file_path),
        )
        conn.commit()

    return report_id


def compute_report_data():
    # Define the timezone (UTC)
    utc = pytz.UTC

    # Get current time and time intervals with timezone awareness
    now = datetime.now(utc)
    last_hour_start = now - timedelta(hours=1)
    last_day_start = now - timedelta(days=1)
    last_week_start = now - timedelta(weeks=1)

    # Convert to string format for SQL queries
    now_str = now.isoformat()
    last_hour_start_str = last_hour_start.isoformat()
    last_day_start_str = last_day_start.isoformat()
    last_week_start_str = last_week_start.isoformat()

    with get_db_connection() as conn:
        # Load data from database
        store_data = pd.read_sql_query("SELECT * FROM store_data", conn)
        business_hours = pd.read_sql_query("SELECT * FROM business_hours", conn)
        timezones = pd.read_sql_query("SELECT * FROM timezones", conn)

    # Merge tables to have all needed information in one DataFrame
    data = store_data.merge(timezones, on="store_id", how="left")
    data = data.merge(business_hours, on="store_id", how="left")

    # Fill missing timezones and business hours with defaults
    data["timezone_str"].fillna("America/Chicago", inplace=True)
    data["start_time_local"].fillna("00:00", inplace=True)
    data["end_time_local"].fillna("23:59", inplace=True)

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



def get_report_status(report_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check report status
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS report_status (
                report_id TEXT PRIMARY KEY,
                status TEXT,
                file_path TEXT
            );
            """
        )
        cursor.execute(
            """
            SELECT status, file_path
            FROM report_status
            WHERE report_id = ?
        """,
            (report_id,),
        )
        row = cursor.fetchone()

        if row:
            status, file_path = row
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
