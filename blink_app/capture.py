import time
import psutil
import numpy as np
from blink_app.config import FPS
from blink_app.logging import log
from blink_app.face_analyzer import FaceAnalyzer
# from blink_app.database import DBHandler
from collections import deque
import imageio
class FrameHandler:

    def __init__(self, frame_rate=30, camera_index=0):
        self.camera_index = camera_index
        self.frame_rate = frame_rate
        self.running = False
        self.total_blinks = 0
        self.runtime = None
        # self.db = DBHandler()

    def monitor_blinks(self):
        self.running = True
        analyzer = FaceAnalyzer()
        analyzer.start_time = time.time()

        cpu_readings = deque(maxlen=30)  # Store last 30 readings (1 second at 30 FPS)

        try:
            frame_count = 0
            reader = imageio.get_reader('<video>', 'ffmpeg')
            for frame in reader:
                frame_count += 1
                analyzer.process_frame(frame)
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
                    # self.db.log_metrics(blinks, avg_cpu_val, memory_usage_val)
                    # log.info("in last second -> blinks : %s, avg cpu (per) : %s, memory (per) : %s", str(blinks), str(avg_cpu_val), str(memory_usage_val))
                    log.info("blinks : %s - %s", str(blinks), str(self.total_blinks))
                    frame_count = 0
        except KeyError as err:
            log.error(f"Failed in monitoring blinks : {str(err)}")
        # finally:
        #     self.running = False
