import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2 as cv
import numpy as np
from helper import callback
from helper import draw_landmarks_on_image
from helper import calculate_angle
import time
from flask import Flask, request, render_template, Response, redirect, url_for
import tempfile
import os
from pathlib import Path
from uuid import uuid4
from flask import jsonify

app = Flask(__name__)
UPLOAD_DIR = Path(app.root_path) / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
current_video_path = None
bench_angle = None    
baseline_shoulder_angle = None         # at each run it can't meet both conditions at once thats why cheating isn't detected 
cheating = False
latest_results = {"reps": 0, "feedback": ""}


app.config["MAX_CONTENT_LENGTH"] = 105 * 1024 * 1024

@app.post("/process")
def get_video_input():
    global current_video_path
    if request.form.get("exercise", "curl") != "curl":
        return jsonify(error="This server processes Bicep curl. Please select Bicep curl."), 400
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

    latest_results.update(reps=0, feedback="")
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
            baseline_shoulder_angle = None
            cheating = False
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
                    hip = (lm[23].x, lm[23].y)
    
                    left_elbow_angle = calculate_angle(shoulder, elbow, wrist)
                    left_shoulder_angle = calculate_angle(hip, shoulder, elbow)
    
                    h, w, _ = frame.shape
                    ex = int(lm[13].x * w)
                    ey = int(lm[13].y * h)
                    ex_shoulder = int(lm[11].x * w)
                    ey_shoulder = int(lm[11].y * h)
    
                    cv.putText(
                        frame,
                        str(int(left_elbow_angle)),
                        (ex, ey),
                        cv.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2,
                        cv.LINE_AA
                    )
    
                    cv.putText(
                        frame,
                        str(int(left_shoulder_angle)),
                        (ex_shoulder, ey_shoulder),
                        cv.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2,
                        cv.LINE_AA
                    )
    
                    # detect cheating through shoulder angle         # at each run it can't meet both conditions at once thats why cheating isn't detected 
    
    
                    # curl counter
                    if left_elbow_angle > 150:
                        stage = "down"
                        baseline_shoulder_angle = left_shoulder_angle
                        # print("Baseline shoulder angle set to: ", baseline_shoulder_angle)
                    if left_elbow_angle < 40 and stage == 'down':
                        stage="up"
                        counter +=1
                        print("Curl count: ", counter)
                        if baseline_shoulder_angle is not None:
                            print("Baseline shoulder angle: ", baseline_shoulder_angle)
                            print("Current shoulder angle: ", left_shoulder_angle)
                            if abs(left_shoulder_angle - baseline_shoulder_angle) > 5:
                                cheating = True
                                print("Cheating detected! Shoulder angle changed by more than 5 degrees.")
                            else:
                                cheating = False
                    
                    color = (0,0,255) if cheating else (0,255,0)
                    cv.putText(frame, "Shoulder stable" if not cheating else "Shoulder moving!",
                                (50,50), cv.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                    if cheating:
                        print("Cheating occurs at curl: ", counter) # ( len(list(set(cheatingAtCurl)) / counter ) * 100 Accuracy 
                        cheatingAtCurl.append(counter)
    
                    # print curl count
                    cv.putText(
                        frame,
                        f"Curls: {counter}",
                        (30, 100),                     # x, y position
                        cv.FONT_HERSHEY_SIMPLEX,
                        1.2,
                        (255, 255, 255),               # white text
                        3,
                        cv.LINE_AA)

                    latest_results["reps"] = counter
                    latest_results["feedback"] = "Cheating detected!" if cheating else "Good form"
    
                rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                annotated = draw_landmarks_on_image(rgb, result) if result.pose_landmarks else rgb
                output_frame = cv.cvtColor(annotated, cv.COLOR_RGB2BGR)
                encoded, buffer = cv.imencode('.jpg', output_frame)
                if encoded:
                    yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                           + buffer.tobytes() + b'\r\n')
        finally:
            cap.release()


@app.get("/results")
def results():
    return jsonify(latest_results)


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