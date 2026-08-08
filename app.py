```python
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import threading
import time
import os

app = Flask(__name__)
CORS(app)

# ============================================================
# LATEST JPEG FRAME
# ============================================================

latest_frame = None
frame_lock = threading.Lock()


# ============================================================
# ADD HEADERS
# ============================================================

@app.after_request
def add_headers(response):

    # Allow your Render static website to access the stream
    response.headers["Access-Control-Allow-Origin"] = "*"

    # Prevent caching
    response.headers["Cache-Control"] = (
        "no-cache, no-store, must-revalidate"
    )

    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return jsonify({
        "service": "Sentry Stream",
        "status": "online",
        "stream": "/stream",
        "upload": "/frame"
    })


# ============================================================
# RECEIVE JPEG FROM YOLO
# ============================================================

@app.route("/frame", methods=["POST"])
def receive_frame():

    global latest_frame

    # Your YOLO program sends raw JPEG bytes:
    #
    # data=encoded.tobytes()
    #
    # Content-Type: image/jpeg

    frame = request.get_data(
        cache=False,
        as_text=False
    )

    if not frame:

        return jsonify({
            "error": "No JPEG received"
        }), 400

    # Store newest JPEG
    with frame_lock:

        latest_frame = frame

    return jsonify({
        "status": "received",
        "bytes": len(frame)
    })


# ============================================================
# VIDEO STREAM
# ============================================================

@app.route("/stream")
def stream():

    def generate():

        while True:

            # Get newest JPEG
            with frame_lock:

                frame = latest_frame

            # Wait until YOLO sends a frame
            if frame is None:

                time.sleep(0.02)

                continue

            # ------------------------------------------------
            # MJPEG FRAME
            # ------------------------------------------------

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: "
                + str(len(frame)).encode()
                + b"\r\n\r\n"
                + frame
                + b"\r\n"
            )

            # Prevent excessive CPU usage
            time.sleep(0.03)


    return Response(
        generate(),
        mimetype=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        )
    )


# ============================================================
# HEALTH
# ============================================================

@app.route("/health")
def health():

    with frame_lock:

        online = latest_frame is not None

    return jsonify({
        "status": "online",
        "frame_available": online
    })


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    print("=" * 50)
    print("SENTRY STREAM SERVER")
    print("=" * 50)

    print()
    print(f"Running on port {port}")

    print()
    print("Stream:")
    print("/stream")

    print()
    print("JPEG upload:")
    print("/frame")

    print("=" * 50)

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True,
        debug=False
    )
```
