import cv2
import signal
import sys
from blink_app.logging import log

def find_working_camera():
    """
    Find the best working camera by testing indices from 0 to 5.
    Prefers external cameras (higher indices) over built-in cameras.
    Returns the highest index of a working camera or 0 if none found.
    """
    working_cameras = []
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                working_cameras.append(i)
                log.info(f"Found working camera at index {i}")
    
    if working_cameras:
        # Prefer the highest index (usually external cameras)
        selected_camera = working_cameras[-1]
        log.info(f"Selected camera at index {selected_camera}")
        return selected_camera
    
    log.warning("No working camera found, defaulting to camera 0")
    return 0

def signal_handler(cap, signum, frame):
    """Handle cleanup when receiving interrupt signal"""
    log.info("Interrupt received, cleaning up...")
    if cap is not None:
        cap.release()
    sys.exit(0)

def setup_signal_handler(cap):
    """Set up the signal handler for graceful shutdown"""
    signal.signal(signal.SIGINT, lambda signum, frame: signal_handler(cap, signum, frame))
