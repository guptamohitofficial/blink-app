import cv2
import time
import psutil
import numpy as np
from blink_app.config import FRAME_WIDTH, FRAME_HEIGHT, FPS
from blink_app.logging import log
from blink_app.face_analyzer import FaceAnalyzer
from blink_app.database import DBHandler
from blink_app.utils import setup_signal_handler
from collections import deque
import subprocess
import os
import json


def get_thread_usage_via_cli(pid):
    try:
        # Insert relevant system commands to profile CPU - can adjust based on need
        # Example: using 'ps' to view threads, though not perfect for CPU monitoring
        result = subprocess.run(['ps', '-M', str(pid)], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error: {e}")

def capture_and_save_frame(file_path, frame):
    cv2.imwrite(file_path, frame)
    print(f"Frame saved to {file_path}")

def process_saved_frame(file_path):
    # Read the saved image
    return cv2.imread(file_path)

class FrameHandler:

    def __init__(self, frame_rate=30, camera_index=0):
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
            return None

    def append_list_to_json_file(self, file_path, new_list):
        new_list = new_list.tolist()
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        raise ValueError("JSON data is not a list")
                except json.JSONDecodeError:
                    data = []
        else: data = []
        data.append(new_list)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    
    def monitor_blinks(self):
        self.running = True
        analyzer = FaceAnalyzer()
        analyzer.start_time = time.time()
        cpu_readings = deque(maxlen=30)  # Store last 30 readings (1 second at 30 FPS)
        last_epoch = int(time.time())
        last_epoch_per_fps = int(time.time())
        try:
            frame_count = 0
            frame_count_per_sec = 0
            while True:
                # Capture frame-by-frame
                ret, self.current_frame = self.capture.read()
                if not ret:
                    log.warning("Failed to capture frame. Exiting...")
                    break
                frame_count += 1
                processed_frame = analyzer.process_frame(self.current_frame)
                self.runtime = time.time() - analyzer.start_time
                current_cpu = psutil.cpu_percent()
                cpu_readings.append(current_cpu)
                avg_cpu = np.mean(cpu_readings) if cpu_readings else current_cpu
                memory_usage = psutil.Process().memory_percent()
                avg_cpu_val = float(f"{avg_cpu:.1f}")
                memory_usage_val = float(f"{memory_usage:.1f}")
                
                if last_epoch != int(time.time()):
                    log.info("1 sec frame : %s", str(frame_count_per_sec))
                    frame_count_per_sec = 0
                    last_epoch = int(time.time())

                if frame_count == FPS:
                    blinks = analyzer.get_and_reset_blink_count()
                    self.total_blinks += blinks
                    self.db.log_metrics(blinks, avg_cpu_val, memory_usage_val)
                    time_took = int(time.time()) - last_epoch_per_fps
                    last_epoch_per_fps = int(time.time())
                    # log.info("in last second -> blinks : %s, avg cpu (per) : %s, memory (per) : %s", str(blinks), str(avg_cpu_val), str(memory_usage_val))
                    # log.info("no cv blinks : %s - %s", str(blinks), str(self.total_blinks))
                    log.info("blinks : %s - %s", str(blinks), str(self.total_blinks))
                    log.info("time / 30 frames : %s", f"{time_took:.2f}")
                    frame_count = 0
                frame_count_per_sec += 1
                cv2.imshow('Face Analysis', processed_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or self.running is False:
                    break
        except Exception as err:
            log.error(f"Failed in monitoring blinks : {str(err)}")
        finally:
            self.running = False
            self.capture.release()
            cv2.destroyAllWindows()
