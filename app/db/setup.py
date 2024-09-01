import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from sqlalchemy.orm import sessionmaker
import pandas as pd

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:mysecretpassword@db:5432/test_db')
STORE_DATA_CSV = os.getenv('STORE_DATA_CSV')
BUSINESS_HOURS_CSV = os.getenv('BUSINESS_HOURS_CSV')
TIMEZONES_CSV = os.getenv('TIMEZONES_CSV')
print(f"Using database at {DATABASE_URL}, store data CSV at {STORE_DATA_CSV}, business hours CSV at {BUSINESS_HOURS_CSV}, and timezones CSV at {TIMEZONES_CSV}")

# Create a database engine
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
metadata = MetaData()

def create_tables():
    """Create tables in the PostgreSQL database if they don't exist."""
    store_data = Table('store_data', metadata,
                       Column('store_id', String, primary_key=True),
                       Column('timestamp_utc', String),
                       Column('status', String)
                       )

    business_hours = Table('business_hours', metadata,
                           Column('store_id', String),
                           Column('dayOfWeek', Integer),
                           Column('start_time_local', String),
                           Column('end_time_local', String)
                           )

    timezones = Table('timezones', metadata,
                      Column('store_id', String, primary_key=True),
                      Column('timezone_str', String)
                      )

    metadata.create_all(engine)

def load_csv_to_db(csv_path, table_name):
    """Load data from a CSV file into a specified database table."""
    if not csv_path:
        print(f"Warning: No CSV path specified for table {table_name}.")
        return

    df = pd.read_csv(csv_path)
    
    # Save DataFrame to PostgreSQL
    df.to_sql(table_name, engine, if_exists='append', index=False)

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

