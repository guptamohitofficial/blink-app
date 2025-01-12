import signal
import sys
from blink_app.logging import log

def signal_handler(cap, signum, frame):
    """Handle cleanup when receiving interrupt signal"""
    log.info("Interrupt received, cleaning up...")
    if cap is not None:
        cap.release()
    sys.exit(0)

def setup_signal_handler(cap):
    """Set up the signal handler for graceful shutdown"""
    signal.signal(signal.SIGINT, lambda signum, frame: signal_handler(cap, signum, frame))
