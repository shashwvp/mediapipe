

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2 as cv
import numpy as np
from helper import callback
from helper import draw_landmarks_on_image
from helper import calculate_angle
from helper import calculate_angle_vertical
import time
from flask import Flask, request, render_template, Response, redirect, url_for
import tempfile
import os
from pathlib import Path
from uuid import uuid4
from flask import jsonify


# standing shoulder press
# Track reps for shoulder press exercise and detect cheating based on torso lean and knee angle changes.
app = Flask(__name__)
UPLOAD_DIR = Path(app.root_path) / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
current_video_path = None    
cheating = False
baseline_torso_angle = None         # at each run it can't meet both conditions at once thats why cheating isn't detected
baseline_knee_angle = None

# incline bench uses angle of torso and knee to detect cheating
# shoulder press will display cheating occuring once rep is done, but it will not display cheating during the rep. This is because the torso and knee angles can change during the rep, but they should return to baseline at the end of the rep. If they don't return to baseline, then cheating has occurred.
message_start_time = 0
message_duration = 2.0

app.config["MAX_CONTENT_LENGTH"] = 105 * 1024 * 1024

@app.post("/process")
def get_video_input():
    global current_video_path
    if request.form.get("exercise", "press") != "press":
        return jsonify(error="This server processes Shoulder press. Please select Shoulder press."), 400
    uploaded = request.files.get("video")
    if not uploaded or not uploaded.filename:
        return jsonify(error="Choose a video first."), 400
    suffix = Path(uploaded.filename).suffix.lower()
    if suffix not in {".mp4", ".mov", ".webm", ".m4v", ".avi"}:
        return jsonify(error="Choose an MP4, MOV, WebM, M4V or AVI video."), 400
    path = UPLOAD_DIR / f"{uuid4().hex}{suffix}"
    uploaded.save(str(path))
    cap = cv.VideoCapture(str(path))
    try:
        readable, _ = cap.read()
    finally:
        cap.release()
    if not readable:
        path.unlink(missing_ok=True)
        return jsonify(error="OpenCV could not read this video. Try another MP4 file."), 400
    current_video_path = str(path)
    return jsonify(stream_url=url_for("video_feed", video_id=path.name))

def generate_frames(video_path):
    model_path = str(Path(__file__).with_name("pose_landmarker_lite.task"))
        
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
        cap = cv.VideoCapture(video_path)
        try:
            frame_count = 0
            fps = cap.get(cv.CAP_PROP_FPS)
            if not np.isfinite(fps) or fps <= 0:
                fps = 30.0
            fps = min(fps, 1000.0)
            baseline_torso_angle = None
            baseline_knee_angle = None
            cheating = {"Leg drive": False, "Excessive back lean": False}
            cheat_reason = ""
            message_start_time = 0
            message_duration = 2.0
            counter = 0
            cheatingAtCurl = []
            stage = ""
            while True:
                # Capture frame-by-frame
                ret, frame = cap.read()
    
                # If ret is False, the video has ended
                if not ret:
                    print("ret is false")
                    break
    
                # --- Process the frame here (e.g., display it) ---
                # cv.imshow('Frame', frame)
    
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv.cvtColor(frame, cv.COLOR_BGR2RGB))
                timestamp = int((frame_count / fps) * 1000)
    
                frame_count += 1
    
                pose_landmarker_result = landmarker.detect_for_video(mp_image, timestamp)
                result = pose_landmarker_result
                latest_frame = frame
                if latest_frame is None:
                    print("latest frame is none")
                    break
    
                frame = latest_frame.copy()
    
                if not result.pose_landmarks:
                    print("result not found")
                else:
    
                    lm = result.pose_landmarks[0]
    
                    shoulder = (lm[11].x, lm[11].y)
                    elbow    = (lm[13].x, lm[13].y)
                    wrist    = (lm[15].x, lm[15].y)
                    knee = (lm[25].x, lm[25].y)
                    ankle = (lm[27].x, lm[27].y)
                    hip = (lm[23].x, lm[23].y)
    
                    elbow_angle = calculate_angle(shoulder, elbow, wrist)
                    knee_angle = calculate_angle(hip,knee,ankle)
                    torso_lean = calculate_angle_vertical(hip, shoulder)
    
                    h, w, _ = frame.shape
                    ex = int(lm[13].x * w)
                    ey = int(lm[13].y * h)
                    ex_shoulder = int(lm[11].x * w)
                    ey_shoulder = int(lm[11].y * h)
    
                    hip_x = int(lm[23].x * w)
                    hip_y = int(lm[23].y * h)
    
                    shoulder_x = shoulder[0]
                    shoulder_y = shoulder[1]
    
    
                    cheating = {"Leg drive": False, "Excessive back lean": False}
    
                    if baseline_torso_angle is None:
                        baseline_torso_angle = torso_lean
    
                    if baseline_knee_angle is None:
                        baseline_knee_angle = knee_angle
                        print("Baseline knee angle set to: ", baseline_knee_angle)
    
                    if 70 <= elbow_angle <= 105:
                        stage = "down"
                    elif elbow_angle >= 160 and stage == 'down':
                        stage = "up"
                        counter += 1
                        print("Reps: ", counter)
                        lean_change = abs(torso_lean - baseline_torso_angle)
                        if lean_change > 12:
                            cheating["Excessive back lean"] = True
                            cheat_reason = "Excessive back lean"
                            message_start_time = time.time()
                        knee_change = abs(baseline_knee_angle - knee_angle)
                        if knee_change > 15:
                            cheating["Leg drive"] = True
                            cheat_reason = "Leg drive"
                            message_start_time = time.time()
    
    
                    # torso
                    cv.circle(frame, (hip_x, hip_y), 6, (0, 255, 0), -1)
    
                    # cv.line(frame, (hip_x, hip_y), (int(shoulder_x), int(shoulder_y)), (255, 255, 0), 2)
                    cv.putText(frame, f"{torso_lean:.1f} deg", (hip_x + 10, hip_y - 10),
                    cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
                    # knee
                    kx = int(lm[25].x * w)
                    ky = int(lm[25].y * h)
                    cv.circle(frame, (kx, ky), 6, (0, 255, 0), -1)
                    cv.putText(
                    frame,
                    str(int(knee_angle)),
                    (kx, ky),
                    cv.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                    cv.LINE_AA
                    )
    
                    # elbow
                    cv.circle(frame, (ex, ey), 6, (0, 255, 0), -1)
                    cv.putText(
                    frame,
                    str(int(elbow_angle)),
                    (ex, ey),
                    cv.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                    cv.LINE_AA
                    )  
    
                    # print rep counter on the frame
                    cv.putText(
                    frame,
                    f"Reps: {counter}",
                    (30, 100),                     # x, y position
                    cv.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (255, 255, 255),               # white text
                    3,
                    cv.LINE_AA)     
    
                    # print cheating status on the frame
                    if time.time() - message_start_time < message_duration:
                        if cheating["Excessive back lean"]:
                            # Get the size of the text
                            (text_width, text_height), baseline = cv.getTextSize(
                                f"Cheating detected: {cheat_reason}",
                                cv.FONT_HERSHEY_SIMPLEX,
                                1.2,
                                2
                            )
                            x, y = (30, 150)  # Position where you want to place the text
                            # Draw black background rectangle
                            cv.rectangle(
                                frame,
                                (x - 10, y - text_height - 10),
                                (x + text_width + 10, y + baseline + 10),
                                (0, 0, 0),
                                -1
                            )
    
                            cv.putText(
                            frame,
                            f"Cheating detected: {cheat_reason}",
                            (30, 150),                     # x, y position
                            cv.FONT_HERSHEY_SIMPLEX,
                            1.2,
                            (0, 0, 255),               # red text
                            2,
                            cv.LINE_AA)
    
                    if time.time() - message_start_time < message_duration:
                        if cheating["Leg drive"]:
    
                            # Get the size of the text
                            (text_width, text_height), baseline = cv.getTextSize(
                                f"Cheating detected: {cheat_reason}",
                                cv.FONT_HERSHEY_SIMPLEX,
                                1.2,
                                2
                            )
    
                            x, y = (30, 150)  # Position where you want to place the text
                            # Draw black background rectangle
                            cv.rectangle(
                                frame,
                                (x - 10, y - text_height - 10),
                                (x + text_width + 10, y + baseline + 10),
                                (0, 0, 0),
                                -1
                            )
    
                            cv.putText(
                            frame,
                            f"Cheating detected: {cheat_reason}",
                            (30, 150),                     # x, y position
                            cv.FONT_HERSHEY_SIMPLEX,
                            1.2,
                            (0, 0, 255),               # red text
                            2,
                            cv.LINE_AA)
    
                rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                annotated = draw_landmarks_on_image(rgb, result) if result.pose_landmarks else rgb
                output_frame = cv.cvtColor(annotated, cv.COLOR_RGB2BGR)
                encoded, buffer = cv.imencode('.jpg', output_frame)
                if encoded:
                    yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                           + buffer.tobytes() + b'\r\n')
        finally:
            cap.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    video_id = request.args.get("video_id", "")
    if not video_id or Path(video_id).name != video_id:
        return "Upload a video first", 400
    path = UPLOAD_DIR / video_id
    if not path.is_file():
        return "Video not found", 404
    if not Path(__file__).with_name("pose_landmarker_lite.task").is_file():
        return "Pose model file is missing", 503
    return Response(generate_frames(str(path)),
                    mimetype='multipart/x-mixed-replace; boundary=frame',
                    headers={"Cache-Control": "no-store"})

if __name__ == "__main__":
    app.run(debug=True)