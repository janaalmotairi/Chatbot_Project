"""
db.py

Initializes and executes SQL queries on a local SQLite database.
"""

import sqlite3
import pandas as pd
import os

DB_PATH = "hr.db"
CSV_PATH = "WA_Fn-UseC_-HR-Employee-Attrition.csv"


def init_db():
    """Create SQLite database from CSV if it does not exist."""
    if os.path.exists(DB_PATH):
        return

    df = pd.read_csv(CSV_PATH)
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("employees", conn, index=False, if_exists="replace")
    conn.close()


def execute_sql(sql: str):
    """Execute SELECT SQL and return columns and rows."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [d[0] for d in cursor.description]
    conn.close()
    return columns, rows
