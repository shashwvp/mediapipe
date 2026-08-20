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

app = Flask(__name__)
current_video_path = None
bench_angle = None    


@app.post("/process")
def get_video_input():
    global current_video_path
    global bench_angle
    uploaded = request.files["video"]
    bench_angle = int(request.form.get("benchAngle"))
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp:
        uploaded.save(temp.name)
        current_video_path = os.path.abspath(temp.name)
    return redirect(url_for("results"))

@app.route("/results")
def results():
    return render_template("results.html")

def generate_frames(video_path):
    model_path = "/Users/shashwatpatel/Downloads/mediapose/pose_landmarker_lite.task"
        
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
        frame_count = 0
        fps = cap.get(cv.CAP_PROP_FPS)
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

            # Press 'q' on keyboard to exit the loop early
            if cv.waitKey(25) & 0xFF == ord('q'):
                print("q on keyboard quit")
                break

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
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

                # detect cheating through shoulder angle
                baseline_shoulder_angle = bench_angle           # based on bench angle (prompt user in future) 
                
                if abs(left_shoulder_angle - baseline_shoulder_angle) > 15:
                    cheating = True
                else:
                    cheating = False
                
                color = (0,0,255) if cheating else (0,255,0)
                cv.putText(frame, "Shoulder stable" if not cheating else "Shoulder moving!",
                            (50,50), cv.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                if cheating:
                    print("Cheating occurs at curl: ", counter) # ( len(list(set(cheatingAtCurl)) / counter ) * 100 Accuracy 
                    cheatingAtCurl.append(counter)
                
                # curl counter
                if left_elbow_angle > 150:
                    stage = "down"
                if left_elbow_angle < 40 and stage =='down':
                    stage="up"
                    counter +=1
                    print(counter)

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

                rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                annotated = draw_landmarks_on_image(rgb, result)

                output_frame = cv.cvtColor(annotated, cv.COLOR_RGB2BGR)
                # cv.imshow("Pose", output_frame)
                cv.waitKey(1)

                _, buffer = cv.imencode('.jpg', output_frame)
                frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(generate_frames(current_video_path),
                mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True)