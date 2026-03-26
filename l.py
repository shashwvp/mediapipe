import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2
import numpy as np
from helper import draw_landmarks_on_image
from helper import calculate_angle

# STEP 2: Create a PoseLandmarker object.
base_options = python.BaseOptions(
    model_asset_path=r"C:\Users\shash\Downloads\pose_landmarker_lite.task"
)

options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    output_segmentation_masks=True
)

detector = vision.PoseLandmarker.create_from_options(options)

# STEP 3: Load the input image.
image = mp.Image.create_from_file(r"C:\Users\shash\Downloads\girl-4051811_960_720.jpg")

# STEP 4: Detect pose landmarks.
detection_result = detector.detect(image)

landmarks = detection_result.pose_landmarks[0]

left_shoulder = [landmarks[11].x, landmarks[11].y]
left_elbow = [landmarks[13].x, landmarks[13].y]
left_wrist = [landmarks[15].x, landmarks[15].y]
left_elbow_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
print(left_elbow_angle)

# STEP 5: Visualize.
annotated_image = draw_landmarks_on_image(
    image.numpy_view(), detection_result
)

# Show image on Windows
# show on elbow
# Get image dimensions
h, w, _ = annotated_image.shape

# Convert normalized coordinates to pixel coords
elbow_point = (int(left_elbow[0] * w), int(left_elbow[1] * h))

# Draw angle text
cv2.putText(
    annotated_image,
    str(int(left_elbow_angle)),   # round angle
    elbow_point,
    cv2.FONT_HERSHEY_SIMPLEX,
    0.7,
    (0, 255, 0),
    2,
    cv2.LINE_AA
)

# Show image
cv2.imshow("Pose Landmarks", cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
cv2.waitKey(0)
cv2.destroyAllWindows()





