import numpy as np
from mediapipe.tasks.python.vision import drawing_utils
from mediapipe.tasks.python.vision import drawing_styles
from mediapipe.tasks.python import vision
import cv2

def draw_landmarks_on_image(rgb_image, detection_result):
  pose_landmarks_list = detection_result.pose_landmarks
  annotated_image = np.copy(rgb_image)

  pose_landmark_style = drawing_styles.get_default_pose_landmarks_style()
  pose_connection_style = drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2)

  for pose_landmarks in pose_landmarks_list:
    drawing_utils.draw_landmarks(
        image=annotated_image,
        landmark_list=pose_landmarks,
        connections=vision.PoseLandmarksConnections.POSE_LANDMARKS,
        landmark_drawing_spec=pose_landmark_style,
        connection_drawing_spec=pose_connection_style)

  return annotated_image


def calculate_angle(a,b,c):
    a = np.array(a) # First
    b = np.array(b) # Mid
    c = np.array(c) # End
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle >180.0:
        angle = 360-angle
        
    return angle 


latest_frame = None

def callback(result, output_image, timestamp_ms):
    global latest_frame

    if latest_frame is None:
        return

    frame = latest_frame.copy()

    if not result.pose_landmarks:
        return

    lm = result.pose_landmarks[0]

    # calculate angles
    shoulder = (lm[11].x, lm[11].y)
    elbow    = (lm[13].x, lm[13].y)
    wrist    = (lm[15].x, lm[15].y)
    hip = (lm[23].x, lm[23].y)

    left_elow_angle = calculate_angle(shoulder, elbow, wrist)
    left_shoulder_angle = calculate_angle(hip, shoulder, elbow)

    h, w, _ = frame.shape
    ex = int(lm[13].x * w)
    ey = int(lm[13].y * h)
    ex_shoulder = int(lm[11].x * w)
    ey_shoulder = int(lm[11].y * h)

    cv2.putText(
        frame,
        str(int(left_elow_angle)),
        (ex, ey),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2,
        cv2.LINE_AA
    )

    cv2.putText(
        frame,
        str(int(left_shoulder_angle)),
        (ex_shoulder, ey_shoulder),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2,
        cv2.LINE_AA
    )

    

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    annotated = draw_landmarks_on_image(rgb, result)

    cv2.imshow("Pose", cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
    cv2.waitKey(1)
