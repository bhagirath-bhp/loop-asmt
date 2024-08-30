import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_PATH = os.getenv('DATABASE_PATH', 'database.db')
STORE_DATA_CSV = os.getenv('STORE_DATA_CSV')
BUSINESS_HOURS_CSV = os.getenv('BUSINESS_HOURS_CSV')
TIMEZONES_CSV = os.getenv('TIMEZONES_CSV')

def get_db_connection():
    """Create and return a new database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Create tables in the SQLite database if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Define table creation SQL statements
        tables = {
            'store_data': """
                CREATE TABLE IF NOT EXISTS store_data (
                    store_id TEXT,
                    timestamp_utc TEXT,
                    status TEXT
                )
            """,
            'business_hours': """
                CREATE TABLE IF NOT EXISTS business_hours (
                    store_id TEXT,
                    dayOfWeek INTEGER,
                    start_time_local TEXT,
                    end_time_local TEXT
                )
            """,
            'timezones': """
                CREATE TABLE IF NOT EXISTS timezones (
                    store_id TEXT,
                    timezone_str TEXT
                )
            """
        }
        
        # Execute each table creation SQL statement
        for table_name, sql in tables.items():
            cursor.execute(sql)
        
        conn.commit()

def load_csv_to_db(csv_path, table_name):
    """Load data from a CSV file into a specified database table."""
    if not csv_path:
        print(f"Warning: No CSV path specified for table {table_name}.")
        return
    
    df = pd.read_csv(csv_path)
    
    with get_db_connection() as conn:
        df.to_sql(table_name, conn, if_exists='append', index=False)

def load_store_data():
    """Load store data from a CSV file into the database."""
    if STORE_DATA_CSV:
        load_csv_to_db(STORE_DATA_CSV, 'store_data')
    else:
        print("Error: STORE_DATA_CSV environment variable not set")

def load_business_hours():
    """Load business hours data from a CSV file into the database."""
    if BUSINESS_HOURS_CSV:
        load_csv_to_db(BUSINESS_HOURS_CSV, 'business_hours')
    else:
        print("Error: BUSINESS_HOURS_CSV environment variable not set")

def load_timezones():
    """Load timezones data from a CSV file into the database."""
    if TIMEZONES_CSV:
        load_csv_to_db(TIMEZONES_CSV, 'timezones')
    else:
        print("Error: TIMEZONES_CSV environment variable not set")

def init():
    """Initialize the database and load data from CSV files."""
    create_tables()
    load_store_data()
    load_business_hours()
    load_timezones()
    print("Database initialized and data loaded.")

init()