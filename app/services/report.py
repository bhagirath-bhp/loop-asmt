import pandas as pd
import sqlite3
from db.database import get_db_connection
import uuid
import os

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
    # Replace with actual logic to compute report data
    # Example placeholder data
    return [
        {
            "store_id": 1,
            "uptime_last_hour": 60,
            "uptime_last_day": 24,
            "uptime_last_week": 168,
            "downtime_last_hour": 0,
            "downtime_last_day": 0,
            "downtime_last_week": 0,
        }
    ]


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
