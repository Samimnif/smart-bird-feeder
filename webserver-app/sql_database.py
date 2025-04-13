import sqlite3
from typing import List, Tuple

class VoltageDB:
    def __init__(self, db_path="battery_data.db"):
        self.db_path = db_path
        self._create_table()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS battery_voltage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    voltage REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def insert_voltage(self, voltage: float):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO battery_voltage (voltage) VALUES (?)", (voltage,))
            conn.commit()

    def get_voltages_last_24_hours(self) -> List[Tuple[float, str]]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT voltage, timestamp FROM battery_voltage WHERE timestamp >= datetime('now', '-1 day') AND voltage < 5")
            return cursor.fetchall()

    def get_voltages_last_7_days(self) -> List[Tuple[float, str]]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT AVG(voltage) as avg_voltage, DATE(timestamp) as day
            FROM battery_voltage
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY day
            ORDER BY day
            """)
            return cursor.fetchall()
