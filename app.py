import threading
import sys
from blink_app.capture import FrameHandler
# from blink_app.server import app
from blink_app.logging import log
import psutil
import time
import os
# def run_server():
#     try:
#         app.run(host='0.0.0.0', port=8080)
#     except KeyboardInterrupt:
#         server_thread.join()
#         sys.exit(0)

def get_process_cpu_usage():
    process = psutil.Process(os.getpid())
    cpu_percent = process.cpu_percent(interval=1)
    return cpu_percent
try:
    def get_threads_cpu_percent(p, interval=0.1):
        total_percent = p.cpu_percent(interval)
        total_time = sum(p.cpu_times())
        return [total_percent * ((t.system_time + t.user_time)/total_time) for t in p.threads()]
    # server_thread = threading.Thread(target=run_server, name="server_thread")
    # server_thread.daemon=True
    # server_thread.start()
    # cpu_usage = get_process_cpu_usage()
    # print(f"Total Process CPU Usage: {cpu_usage}%")



    frame_handler = FrameHandler()
    frame_handler.monitor_blinks()
except KeyError as err:
    log.error(f"Failed in main app : {str(err)}")

# finally:
#     sys.exit(0)
