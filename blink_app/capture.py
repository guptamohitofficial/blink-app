import cv2
import time
import psutil
import threading
import multiprocessing
import numpy as np
import os
import sys
from blink_app.config import FRAME_WIDTH, FRAME_HEIGHT, FPS
from blink_app.logging import log
# from blink_app.face_analyzer import FaceAnalyzer
from blink_app.no_cv_face_analyzer import FaceAnalyzer
from blink_app.database import DBHandler
from blink_app.utils import setup_signal_handler
from collections import deque
import subprocess


def get_thread_usage_via_cli(pid):
    try:
        # Insert relevant system commands to profile CPU - can adjust based on need
        # Example: using 'ps' to view threads, though not perfect for CPU monitoring
        result = subprocess.run(['ps', '-M', str(pid)], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error: {e}")


def list_threads():
    """Lists all active threads and processes."""
    all_threads = threading.enumerate()
    print(f"Total Threads: {len(all_threads)}", end=" : ")
    for i, thread in enumerate(all_threads, start=1):
        print(f"Thread {i}: Name = {thread.name}, ID = {thread.ident}")

    active_processes = multiprocessing.active_children()
    print(f"Total Active Processes: {len(active_processes)}", end=" : ")
    for i, process in enumerate(active_processes, start=1):
        print(f"Process {i}: Name = {process.name}, PID = {process.pid}")

class FrameHandler:

    def __init__(self, frame_rate=5, camera_index=0):
        self.camera_index = camera_index
        self.frame_rate = frame_rate
        self.running = False
        self.current_frame = None
        self.total_blinks = 0
        self.runtime = None
        self.db = DBHandler()

        self.capture = cv2.VideoCapture(self.camera_index)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.capture.set(cv2.CAP_PROP_FPS, FPS)
        setup_signal_handler(self.capture)

        if not self.capture.isOpened():
            log.error("Camera not accessible")

    def monitor_blinks(self):
        """Monitors and logs blink metrics."""
        if not self.capture.isOpened():
            log.error("Cannot start blink monitoring. Camera is not accessible.")
            return

        self.running = True
        analyzer = FaceAnalyzer()
        analyzer.start_time = time.time()
        cpu_readings = deque(maxlen=30)
        try:
            frame_count = 0
            last_epoch_sec = int(time.time())
            current_pid = os.getpid()
            proc = psutil.Process(current_pid)
            proc.cpu_percent(interval=0.1)  

            while self.running:
                ret, self.current_frame = self.capture.read()
                if not ret:
                    log.warning("Failed to capture frame. Exiting...")
                    break

                # processed_frame = analyzer.process_frame(self.current_frame)
                current_cpu = psutil.cpu_percent()
                cpu_readings.append(current_cpu)
                avg_cpu_val = np.mean(cpu_readings) if cpu_readings else current_cpu
                memory_usage_val = psutil.Process().memory_percent()

                # Calculate frames per second logic
                frame_count += 1
                if frame_count >= FPS:
                    num_threads = cv2.getNumThreads()
                    blinks = analyzer.get_and_reset_blink_count()
                    self.total_blinks += blinks
                    self.db.log_metrics(blinks, avg_cpu_val, memory_usage_val)
                    cpu_usage = proc.cpu_percent(interval=None)
                    # print("cv2.getNumberOfCPUs()", cv2.getNumberOfCPUs())
                    # log.info("blinks : %d, total : %d, pid : %d, cpu : %d, cpu 2 : %d, threads : %d", blinks, self.total_blinks, current_pid, cpu_usage, current_cpu, num_threads)
                    info = {
                                "pid": current_pid,
                                "name": proc.name(),
                                "status": proc.status(),
                                "cpu_percent": proc.cpu_percent(interval=1.0),  # CPU usage
                                "memory_info": proc.memory_info(),
                                "num_threads": proc.num_threads(),
                                "open_files": proc.open_files(),
                                "connections": proc.connections(),
                                "nice": proc.nice(),
                                "username": proc.username(),
                                "num_fds": proc.num_fds() if hasattr(proc, "num_fds") else "N/A",
                            }
                    
                    memory_info = proc.memory_info()
                    bytes_to_megabytes = 1024 ** 2
                    bytes_to_gb = 1024 ** 3
                    # Return detailed memory usage

                    rss_in_mb = memory_info.rss / bytes_to_megabytes
                    vms_in_mb = memory_info.vms / bytes_to_gb
                    info ={
                        "rss": f"{rss_in_mb:.2f} MB",  # Resident Set Size
                        "vms": f"{vms_in_mb:.2f} GB",  # Virtual Memory Size
                    }
                    sys.stdout.write("\r")
                    for k, v in info.items():
                        sys.stdout.write(f" {k} : {v} \n")
                    sys.stdout.flush()
                    # get_thread_usage_via_cli(current_pid)
                    threads__ = proc.threads()

                    print(f"Process ID: {current_pid}, Number of Threads: {len(threads__)}")

                    # Display information about each thread
                    # for i, thread in enumerate(threads__):
                    #     user_time = thread.user_time
                    #     system_time = thread.system_time
                    #     thread_id = thread.id
                    #     print(f"Thread {i+1}: ID = {thread_id}, User Time = {user_time}, System Time = {system_time}")

                    # Reset for next period
                    frame_count = 0
                    last_epoch_sec = int(time.time())

                cv2.imshow('Face Analysis', self.current_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except Exception as e:
            log.error("Failed in monitoring blinks: %s", str(e))
        finally:
            self.running = False
            self.cleanup()

    def cleanup(self):
        """Releases resources and closes windows."""
        self.capture.release()
        cv2.destroyAllWindows()