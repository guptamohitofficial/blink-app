import sqlite3
import time

class DBHandler:
    def __init__(self, db_path='metrics.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS BlinkMetrics
                          (epoch_time INTEGER, blinks INTEGER,
                           avg_cpu REAL, memory_usage REAL)''')
        self.conn.commit()

    def log_metrics(self, blinks, avg_cpu, memory_usage):
        epoch_time = int(time.time())
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO BlinkMetrics (epoch_time, blinks, avg_cpu, memory_usage)
                          VALUES (?, ?, ?, ?)''', 
                          (epoch_time, blinks, avg_cpu, memory_usage))
        self.conn.commit()

    def fetch_recent(self, limit=10):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT * FROM BlinkMetrics ORDER BY epoch_time DESC LIMIT ?''', (limit,))
        return cursor.fetchall()

    def query_by_timestamp(self, start_time=None, end_time=None):
        # Set default time range if not provided
        if start_time is None:
            start_time = int(time.time()) - 60  # 1 minute ago
        if end_time is None:
            end_time = int(time.time())  # current time

        cursor = self.conn.cursor()
        query = 'SELECT * FROM BlinkMetrics WHERE epoch_time BETWEEN ? AND ? ORDER BY epoch_time'
        conditions = [start_time, end_time]
        cursor.execute(query, conditions)
        return cursor.fetchall()
