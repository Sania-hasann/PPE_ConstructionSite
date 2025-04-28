from flask import Flask, request, send_file, jsonify, render_template, Response
import os
import cv2
import cvzone
import tempfile
import numpy as np
import time
from werkzeug.utils import secure_filename
from ultralytics import YOLO
import threading

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
notifications = []
processing_progress = 0  # Global variable for tracking progress
lock = threading.Lock()

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
    batch_notifications = []  # Store notifications for each batch
    video_name = os.path.basename(input_path)  # Get video filename

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
                detections = []
                for r in results[i]:
                    boxes = r.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = round(box.conf[0].item(), 2)
                        cls = int(box.cls[0])
                        currentClass = classNames[cls]

                        if conf > 0.5:
                            detections.append(currentClass)

                            # Assign colors based on object type
                            if currentClass in ['NO-Hardhat', 'NO-Safety Vest', 'NO-Mask']:
                                myColor = (0, 0, 255)  # Red for unsafe PPE
                            elif currentClass in ['Hardhat', 'Safety Vest', 'Mask']:
                                myColor = (0, 255, 0)  # Green for safe PPE
                            else:
                                myColor = (255, 0, 0)  # Blue for other objects

                            # Draw bounding box and label on image
                            cvzone.putTextRect(img, f'{currentClass} {conf}', (max(0, x1), max(35, y1)),
                                               scale=1, thickness=1, colorB=myColor,
                                               colorT=(255, 255, 255), colorR=myColor, offset=5)
                            cv2.rectangle(img, (x1, y1), (x2, y2), myColor, 3)

                if detections:
                    notification_text = f"{os.path.basename(input_path)} - Frame {frame_indices[i]}: {', '.join(detections)}"
                    
                    # Lock to ensure thread-safe access to the notifications list
                    with lock:
                        notifications.append({"text": notification_text, "read": False})
                    # Push the notification to the frontend via SSE
                    send_notification_to_frontend(notification_text)

                out.write(img)

            frame_buffer.clear()

        processed_frames += 1
        processing_progress = int((processed_frames / total_frames) * 100)

    cap.release()
    out.release()
    processing_progress = 100  # Ensure progress reaches 100% at the end
    print(f"Processed video saved at: {output_path}")

def send_notification_to_frontend(notification_text):
    """Push notification to the frontend using SSE"""
    global notifications
    with lock:
        notifications.append({"text": notification_text, "read": False})

@app.route("/upload")
def upload():
    return render_template("upload.html") 


@app.route("/processed")
def processed():
    return render_template("processed.html") 

@app.route("/notifications-page")
def notifications_page():
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

    # Process the video in a separate thread
    processing_thread = threading.Thread(target=process_video_batch, args=(input_path, output_path))
    processing_thread.start()
    processing_thread.join()  # Wait for processing to finish

    # Return the processed video file for download
    return send_file(output_path, as_attachment=True, download_name=filename)

@app.route("/notifications-data")
def get_notifications():
    global notifications
    with lock:
        return jsonify(notifications) 

@app.route('/mark-all-read', methods=['POST'])
def mark_all_read():
    """Marks all notifications as read."""
    global notifications
    with lock:
        for notification in notifications:
            notification["read"] = True
    return jsonify({"success": True})

@app.route('/clear-notifications', methods=['POST'])
def clear_notifications():
    """Clears all notifications."""
    global notifications
    with lock:
        notifications = []  # Empty the list
    return jsonify({"success": True})

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