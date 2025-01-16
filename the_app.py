import sys
import cv2
import psutil
import subprocess
import dlib
import os
import json
import logging
import time
import numpy as np
import signal
import sys
from collections import deque
from scipy.spatial import distance


def signal_handler(cap, signum, frame):
    """Handle cleanup when receiving interrupt signal"""
    log.info("Interrupt received, cleaning up...")
    if cap is not None:
        cap.release()
    sys.exit(0)

def setup_signal_handler(cap):
    """Set up the signal handler for graceful shutdown"""
    signal.signal(signal.SIGINT, lambda signum, frame: signal_handler(cap, signum, frame))


log = logging.getLogger(__name__)

logFormatter = logging.Formatter(
    "%(asctime)s [%(threadName)-10.10s] [%(levelname)s]  %(message)s"
)

log.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('runtime.log')
console_handler = logging.StreamHandler()

file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logFormatter)

console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logFormatter)

log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

log.addHandler(file_handler)
log.addHandler(console_handler)

FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS = 30



class FaceAnalyzer:
    def __init__(self):
        # Initialize face detector and facial landmarks predictor
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
        
        # Constants for blink detection
        self.EYE_AR_THRESH = 0.25
        self.EYE_AR_CONSEC_FRAMES = 3
        self.BLINK_COOLDOWN = 10  # frames to wait before detecting next blink
        
        # Constants for frown detection
        self.MOUTH_AR_THRESH = 0.2
        
        # Performance monitoring
        self.frame_times = deque(maxlen=30)
        self.blink_counter = 0
        self.frame_counter = 0
        self.frown_counter = 0
        
        # State tracking
        self.blink_cooldown_counter = 0
        self.is_eye_closed = False
        self.is_frowning = False
        self.distance_alert_cooldown = 0
        self.distance_alert_counter = 0
        # Start time
        self.start_time = time.time()
        
        # Warning settings
        self.warning_timestamp = 0
        self.WARNING_DURATION = 2  # seconds

    def process_frame(self, frame):
        """Process a single frame and return analyzed metrics"""
        if frame is None:
            return frame
            
        frame_start = time.time()
        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # gray = frame
        # print("frame", frame)
        # print("cv2.COLOR_BGR2GRAY", cv2.COLOR_BGR2GRAY)
        # print("gray", gray)
        
        # Detect faces
        faces = self.detector(frame)
        # print("faces", faces)
        # Process each face (assuming single face for now)
        for face in faces:
            # Get facial landmarks
            landmarks = self.predictor(frame, face)
            # print("landmarks", landmarks)
            points = np.array([[p.x, p.y] for p in landmarks.parts()])
            
            # Extract eye coordinates
            left_eye = points[42:48]
            right_eye = points[36:42]
            
            # Calculate eye aspect ratios
            left_ear = self.calculate_eye_aspect_ratio(left_eye)
            right_ear = self.calculate_eye_aspect_ratio(right_eye)
            ear = (left_ear + right_ear) / 2.0
            
            # Blink detection with cooldown
            if ear < self.EYE_AR_THRESH and not self.is_eye_closed and self.blink_cooldown_counter == 0:
                self.is_eye_closed = True
                self.blink_counter += 1
                self.blink_cooldown_counter = self.BLINK_COOLDOWN
            elif ear >= self.EYE_AR_THRESH:
                self.is_eye_closed = False
            
            if self.blink_cooldown_counter > 0:
                self.blink_cooldown_counter -= 1
            
            # Draw facial landmarks
            for point in points:
                cv2.circle(frame, tuple(point), 1, (0, 255, 0), -1)
            
            # Draw eye contours
            cv2.polylines(frame, [left_eye], True, (0, 255, 0), 1)
            cv2.polylines(frame, [right_eye], True, (0, 255, 0), 1)
            
            # Calculate distance (adjusted calibration)
            
            # Draw face rectangle
            x1, y1, x2, y2 = face.left(), face.top(), face.right(), face.bottom()
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Update performance metrics
        # self.metrics['latency'].append((time.time() - frame_start) * 1000)  # Convert to ms
        
        return frame

    def calculate_eye_aspect_ratio(self, eye_points):
        """Calculate the eye aspect ratio for blink detection"""
        # Compute vertical distances
        A = distance.euclidean(eye_points[1], eye_points[5])
        B = distance.euclidean(eye_points[2], eye_points[4])
        # Compute horizontal distance
        C = distance.euclidean(eye_points[0], eye_points[3])
        # Calculate eye aspect ratio
        ear = (A + B) / (2.0 * C)
        return ear

    def get_and_reset_blink_count(self):
        '''Will be called periodically to return blink count in that period and reset to 0'''
        blinks = self.blink_counter
        self.blink_counter = 0
        return blinks



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
                    # self.db.log_metrics(blinks, avg_cpu_val, memory_usage_val)
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



try:

    frame_handler = FrameHandler()
    frame_handler.monitor_blinks()
except Exception as err:
    log.error(f"Failed in main app : {str(err)}")

finally:
    sys.exit(0)
