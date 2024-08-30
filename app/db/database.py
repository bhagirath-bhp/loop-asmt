import sqlite3
from db.setup import load_store_data, load_business_hours, load_timezones, create_tables

def init_db():
    create_tables()
    load_store_data('store_data.csv')
    load_business_hours('business_hours.csv')
    load_timezones('timezones.csv')
