
import dlib
import numpy as np
import logging
from collections import deque
import time
from scipy.spatial import distance

class FaceAnalyzer:
    def __init__(self):
        # Initialize face detector and facial landmarks predictor
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
        
        # Constants for blink detection
        self.EYE_AR_THRESH = 0.25
        self.EYE_AR_CONSEC_FRAMES = 3
        self.BLINK_COOLDOWN = 10  # frames to wait before detecting next blink
        
        # Performance monitoring
        self.frame_times = deque(maxlen=30)
        self.blink_counter = 0
        self.frame_counter = 0
        
        # State tracking
        self.blink_cooldown_counter = 0
        self.is_eye_closed = False
        
        # Initialize metrics with default values to prevent empty sequence errors
        self.metrics = {
            'latency': [0.0]
        }
        
        # Start time
        self.start_time = time.time()

    def process_frame(self, frame):
        """Process a single frame and return analyzed metrics"""
        if frame is None:
            return frame, self.metrics
            
        frame_start = time.time()
        
        # Assuming `frame` is already a grayscale (2D: height x width) numpy array
        gray = frame
        
        # Detect faces
        faces = self.detector(gray)
        
        # Process each face (assuming single face for now)
        for face in faces:
            # Get facial landmarks
            landmarks = self.predictor(gray, face)
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

        # Update performance metrics
        self.metrics['latency'].append((time.time() - frame_start) * 1000)  # Convert to ms
        
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
        """Will be called periodically to return blink count in that period and reset to 0"""
        blinks = self.blink_counter
        self.blink_counter = 0
        return blinks