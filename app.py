import threading
import sys
from blink_app.capture import FrameHandler
from blink_app.server import app
from blink_app.logging import log

def run_server():
    try:
        app.run(host='0.0.0.0', port=8080)
    except KeyboardInterrupt:
        server_thread.join()
        sys.exit(0)

try:
    server_thread = threading.Thread(target=run_server, name="server_thread")
    server_thread.daemon=True
    server_thread.start()

    frame_handler = FrameHandler()
    frame_handler.monitor_blinks()
except Exception as err:
    log.error(f"Failed in main app : {str(err)}")
finally:
    sys.exit(0)
