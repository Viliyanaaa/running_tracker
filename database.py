import sqlite3
from datetime import datetime

DB_NAME = "lauf_tracker.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            distance_km REAL NOT NULL,
            duration_min REAL NOT NULL,
            pace REAL NOT NULL,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_run(date, distance_km, duration_min, notes=""):
    pace = round(duration_min / distance_km, 2)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO runs (date, distance_km, duration_min, pace, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (date, distance_km, duration_min, pace, notes))
    conn.commit()
    conn.close()

def get_all_runs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM runs ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_run(run_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM runs WHERE id = ?", (run_id,))
    conn.commit()
    conn.close()

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total_runs,
            ROUND(SUM(distance_km), 2) as total_km,
            ROUND(AVG(pace), 2) as avg_pace,
            ROUND(MIN(pace), 2) as best_pace
        FROM runs
    """)
    stats = cursor.fetchone()
    conn.close()
    return stats

def format_pace(pace_decimal):
    minutes = int(pace_decimal)
    seconds = round((pace_decimal - minutes) * 60)
    return f"{minutes}:{seconds:02d}"

def get_best_month():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT strftime('%Y-%m', date) as month,
               ROUND(SUM(distance_km), 2) as total_km
        FROM runs
        GROUP BY month
        ORDER BY total_km DESC
        LIMIT 1
    """)
    result = cursor.fetchone()
    conn.close()
    return result

def get_best_race(min_km, max_km):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MIN(duration_min) as best_time
        FROM runs
        WHERE distance_km BETWEEN ? AND ?
    """, (min_km, max_km))
    result = cursor.fetchone()
    conn.close()
    return result

def format_time(duration_min):
    total_seconds = int(duration_min * 60)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"
