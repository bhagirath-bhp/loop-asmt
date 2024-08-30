import sqlite3
import pandas as pd

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS store_data (
        store_id TEXT,
        timestamp_utc TEXT,
        status TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS business_hours (
        store_id TEXT,
        dayOfWeek INTEGER,
        start_time_local TEXT,
        end_time_local TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS timezones (
        store_id TEXT,
        timezone_str TEXT
    )
    """
    )

    conn.commit()
    conn.close()

def load_store_data(csv_path):
    df = pd.read_csv(csv_path)
    conn = get_db_connection()
    df.to_sql('store_data', conn, if_exists='append', index=False)
    conn.close()

def load_business_hours(csv_path):
    df = pd.read_csv(csv_path)
    conn = get_db_connection()
    df.to_sql('business_hours', conn, if_exists='append', index=False)
    conn.close()

def load_timezones(csv_path):
    df = pd.read_csv(csv_path)
    conn = get_db_connection()
    df.to_sql('timezones', conn, if_exists='append', index=False)
    conn.close()