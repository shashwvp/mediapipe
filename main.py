import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2 as cv
import numpy as np
from helper import callback
import time


model_path = r"C:\Users\shash\Downloads\pose_landmarker_lite.task"

    
BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# Create a pose landmarker instance with the video mode:
options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.VIDEO)

with PoseLandmarker.create_from_options(options) as landmarker:
  # The landmarker is initialized. Use it here.
  # ...
  video_path = r"C:\Users\shash\Downloads\Download.mp4"
  cap = cv.VideoCapture(video_path)
  frame_count = 0
  fps = cap.get(cv.CAP_PROP_FPS)

  while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    # If ret is False, the video has ended
    if not ret:
        break

    # --- Process the frame here (e.g., display it) ---
    cv.imshow('Frame', frame)

    # Press 'q' on keyboard to exit the loop early
    if cv.waitKey(25) & 0xFF == ord('q'):
        break

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
    timestamp = int((frame_count / fps) * 1000)

    frame_count += 1

    pose_landmarker_result = landmarker.detect_for_video(mp_image, timestamp)
    callback(pose_landmarker_result, frame)