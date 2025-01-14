
import av
import numpy as np
from PIL import Image
import time

def capture_camera_fps(fps=30, duration=5):
    container = av.open("/dev/video0")  # For Mac, use appropriate device or use 'default'
    stream = container.streams.video[0]
    stream.thread_type = 'AUTO'
    start_time = time.time()
    frame_interval = 1.0 / fps
    frame_count = 0

    try:
        for frame in container.decode(stream):
            current_time = time.time()
            if current_time - start_time > duration:
                break
            start = current_time
            img = frame.to_image()
            frame_array = np.array(img)
            frame_count += 1
            if frame_count == 1:
                img.save('captured_image.jpg')
            print(f"Captured frame {frame_count}")
            elapsed = time.time() - start
            time_to_wait = frame_interval - elapsed
            if time_to_wait > 0:
                time.sleep(time_to_wait)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        container.close()

if __name__ == "__main__":
    capture_camera_fps()