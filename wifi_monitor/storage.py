"""
Storage module for saving and retrieving test results using SQLite.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path


# Database file location
DB_PATH = Path(__file__).parent.parent / "data" / "results.db"


def init_db():
    """
    Initialize the SQLite database with required schema.
    Creates the database and table if they don't already exist.
    """
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            test_type TEXT NOT NULL,
            status TEXT NOT NULL,
            data TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_result(result: dict):
    """
    Save a test result to the database.
    
    Args:
        result: Dictionary containing test result data with keys like
                'status', 'test_type', and other test-specific fields
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    timestamp = datetime.now().isoformat()
    test_type = result.get("test_type", "unknown")
    status = result.get("status", "UNKNOWN")
    data = json.dumps(result)

    cursor.execute("""
        INSERT INTO results (timestamp, test_type, status, data)
        VALUES (?, ?, ?, ?)
    """, (timestamp, test_type, status, data))

    conn.commit()
    conn.close()


def get_results(limit: int = 10, test_type: str = "all") -> list:
    """
    Retrieve recent test results from the database.
    
    Args:
        limit: Maximum number of results to retrieve
        test_type: Filter by test type ('ping', 'throughput', or 'all')
    
    Returns:
        List of result dictionaries
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if test_type == "all":
        cursor.execute("""
            SELECT timestamp, test_type, status, data
            FROM results
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
    else:
        cursor.execute("""
            SELECT timestamp, test_type, status, data
            FROM results
            WHERE test_type = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (test_type, limit))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        timestamp, test_type, status, data = row
        result_dict = json.loads(data)
        result_dict["timestamp"] = timestamp
        results.append(result_dict)

    return results
