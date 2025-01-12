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

    def monitor_blinks(self):
        self.running = True
        analyzer = FaceAnalyzer()
        analyzer.start_time = time.time()

        cpu_readings = deque(maxlen=30)  # Store last 30 readings (1 second at 30 FPS)

        try:
            frame_count = 0
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

                if frame_count == FPS:
                    blinks = analyzer.get_and_reset_blink_count()
                    self.total_blinks += blinks
                    self.db.log_metrics(blinks, avg_cpu_val, memory_usage_val)
                    log.info("in last second -> blinks : %s, avg cpu (per) : %s, memory (per) : %s", str(blinks), str(avg_cpu_val), str(memory_usage_val))
                    frame_count = 0

                # Display the frame
                cv2.imshow('Face Analysis', processed_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or self.running is False:
                    break
        except Exception as err:
            raise err
        finally:
            # self.running = False
            # self.capture.release()
            # cv2.destroyAllWindows()
            pass
