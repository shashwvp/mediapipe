# STEP 1: Import the necessary modules.
import mediapipe as mp
from helper import draw_landmarks_on_image

model_path = r"C:\Users\shash\Downloads\pose_landmarker_lite.task"
# Load the input image from an image file.
mp_image = mp.Image.create_from_file(r"C:\Users\shash\Downloads\pbrrysxd3jv61.jpg")
    


BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.IMAGE)

with PoseLandmarker.create_from_options(options) as landmarker:
  # The landmarker is initialized. Use it here.
  pose_landmarker_result = landmarker.detect(mp_image)
  print(pose_landmarker_result)