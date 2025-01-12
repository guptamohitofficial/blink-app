import tkinter as tk
from threading import Thread
import sqlite3
import time
from blink_app.database import DBHandler

class BlinkMetricsApp():
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Blink Metrics")
        self.root.geometry("300x200")

        self.blink_label = tk.Label(self.root, text="Blinks: ")
        self.blink_label.pack(pady=10)

        self.cpu_label = tk.Label(self.root, text="CPU Usage: ")
        self.cpu_label.pack(pady=10)

        self.memory_label = tk.Label(self.root, text="Memory Usage: ")
        self.memory_label.pack(pady=10)

        self.running = True
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.db = DBHandler()

    def update_metrics(self):
        while self.running:
            recent_records = self.db.fetch_recent()

            if recent_records:
                blinks, avg_cpu, memory_usage = recent_records[0]
                self.root.after(0, self.update_ui, blinks, avg_cpu, memory_usage)
            else:
                self.root.after(0, self.update_ui, "N/A", "N/A", "N/A")
            time.sleep(1)

    def update_ui(self, blinks, avg_cpu, memory_usage):
        self.blink_label.config(text=f"Blinks: {blinks}")
        self.cpu_label.config(text=f"CPU Usage: {avg_cpu:.2f}%")
        self.memory_label.config(text=f"Memory Usage: {memory_usage:.2f}%")

    def on_closing(self):
        self.running = False
        self.root.quit()
        self.root.destroy()
