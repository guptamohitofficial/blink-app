
import cv2
import time

# Open a connection to the webcam (0 is usually the default camera)
video_capture = cv2.VideoCapture(0)

# Set the resolution to 1280x720 for 720p quality
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Optional: Set desired FPS (not all cameras will respect this)
video_capture.set(cv2.CAP_PROP_FPS, 30)

try:
    # Capture video until interrupted
    while True:
        start_time = time.time()
        
        # Capture frame-by-frame
        ret, frame = video_capture.read()
        
        if not ret:
            print("Failed to capture frame from camera. Exiting...")
            break

        # Display the resulting frame
        cv2.imshow('Video Feed', frame)

        # Wait for 1ms and check if 'q' has been pressed to quit
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

finally:
    # Release the capture and close any OpenCV windows
    video_capture.release()
    cv2.destroyAllWindows()