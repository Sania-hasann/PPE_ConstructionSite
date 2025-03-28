from flask import Flask, request, send_file, jsonify, render_template, Response
import os
import cv2
import cvzone
import tempfile
import numpy as np
import time
from werkzeug.utils import secure_filename
from ultralytics import YOLO

app = Flask(__name__)

UPLOAD_FOLDER = "Uploaded_videos"
PROCESSED_FOLDER = "Processed_videos"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Load YOLO model (Using CPU)
model = YOLO("model/ppe.pt")

# Define class names
classNames = ['Hardhat', 'Mask', 'NO-Hardhat', 'NO-Mask', 'NO-Safety Vest', 'Person', 'Safety Cone',
              'Safety Vest', 'machinery', 'vehicle']

# Global variable to store the input path
current_input_path = None


processing_progress = 0  # Global variable for tracking progress

def process_video_batch(input_path, output_path, batch_size=8, skip_frames=1):
    global current_input_path, processing_progress
    current_input_path = input_path
    processing_progress = 0  # Reset progress

    cap = cv2.VideoCapture(input_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_buffer = []
    frame_indices = []
    processed_frames = 0

    while True:
        success, img = cap.read()
        if not success:
            break

        if processed_frames % skip_frames == 0:
            frame_buffer.append(img)
            frame_indices.append(processed_frames)

        if len(frame_buffer) >= batch_size:
            results = model(frame_buffer, stream=False)

            for i, img in enumerate(frame_buffer):
                for r in results[i]:
                    boxes = r.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = round(box.conf[0].item(), 2)
                        cls = int(box.cls[0])
                        currentClass = classNames[cls]

                        if conf > 0.5:
                            if currentClass in ['NO-Hardhat', 'NO-Safety Vest', 'NO-Mask']:
                                myColor = (0, 0, 255)
                            elif currentClass in ['Hardhat', 'Safety Vest', 'Mask']:
                                myColor = (0, 255, 0)
                            else:
                                myColor = (255, 0, 0)

                            cvzone.putTextRect(img, f'{currentClass} {conf}', (max(0, x1), max(35, y1)),
                                               scale=1, thickness=1, colorB=myColor,
                                               colorT=(255, 255, 255), colorR=myColor, offset=5)
                            cv2.rectangle(img, (x1, y1), (x2, y2), myColor, 3)

                out.write(img)

            frame_buffer.clear()

        processed_frames += 1
        processing_progress = int((processed_frames / total_frames) * 100)  # Update global progress

    cap.release()
    out.release()
    processing_progress = 100  # Ensure progress reaches 100% at the end
    print(f"Processed video saved at: {output_path}")


@app.route("/upload")
def upload():
    return render_template("upload.html") 


@app.route("/processed")
def processed():
    return render_template("processed.html") 

@app.route("/notifications")
def notifications():
    return render_template("notifications.html")

@app.route('/')
def upload_form():
    """Render the upload form."""
    return render_template("index.html")

@app.route('/uploaded/<filename>')
def uploaded_video(filename):
    """Serve the uploaded video."""
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

@app.route('/video', methods=['POST'])
def handle_video():
    """Handles video upload, processes it, and returns the processed file."""
    global current_input_path

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    input_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    output_path = os.path.join(PROCESSED_FOLDER, filename)

    file.save(input_path)  # Save uploaded video

    # Process the video with batch processing
    process_video_batch(input_path, output_path, batch_size=8, skip_frames=1)

    # Return processed video
    return send_file(output_path, as_attachment=True, download_name=filename)

@app.route('/stream')
def stream():
    def generate():
        global processing_progress
        while processing_progress < 100:
            yield f"data: {processing_progress}\n\n"
            time.sleep(0.5)  # Update every 0.5 seconds

        yield "data: 100\n\n"  # Ensure it ends at 100%

    return Response(generate(), mimetype="text/event-stream")

if __name__ == '__main__':
    APP_HOST = "0.0.0.0"
    APP_PORT = 8080
    app.run(host=APP_HOST, port=APP_PORT)