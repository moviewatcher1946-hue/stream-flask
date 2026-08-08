```python
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import threading
import time

app = Flask(__name__)
CORS(app)

# ============================================================
# CONFIG
# ============================================================

MAX_FRAME_SIZE = 5 * 1024 * 1024  # 5 MB maximum JPEG


# ============================================================
# SHARED JPEG FRAME
# ============================================================

latest_frame = None
frame_lock = threading.Lock()


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return jsonify({
        "service": "Sentry Stream Server",
        "status": "online",
        "stream": "/stream",
        "frame_upload": "/frame",
        "health": "/health"
    })


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    with frame_lock:
        has_frame = latest_frame is not None

    return jsonify({
        "status": "online",
        "frame_available": has_frame
    })


# ============================================================
# RECEIVE JPEG
# ============================================================

@app.post("/frame")
def receive_frame():

    global latest_frame

    # Your YOLO program sends raw JPEG bytes:
    #
    # data=encoded.tobytes()
    #
    # Content-Type:
    # image/jpeg

    if request.content_type != "image/jpeg":

        return jsonify({
            "error": "Content-Type must be image/jpeg"
        }), 415


    # Read JPEG
    frame = request.get_data(
        cache=False,
        as_text=False
    )


    if not frame:

        return jsonify({
            "error": "Empty JPEG"
        }), 400


    # Prevent accidentally uploading huge files
    if len(frame) > MAX_FRAME_SIZE:

        return jsonify({
            "error": "JPEG too large"
        }), 413


    # Store only newest frame
    with frame_lock:

        latest_frame = frame


    return jsonify({
        "status": "received",
        "size": len(frame)
    })


# ============================================================
# MJPEG STREAM
# ============================================================

@app.get("/stream")
def stream():

    def generate():

        while True:

            # Get latest JPEG
            with frame_lock:

                frame = latest_frame


            # No frame received yet
            if frame is None:

                time.sleep(0.05)

                continue


            # ------------------------------------------------
            # MJPEG PART
            # ------------------------------------------------

            yield b"--frame\r\n"

            yield b"Content-Type: image/jpeg\r\n"

            yield (
                b"Content-Length: "
                + str(len(frame)).encode()
                + b"\r\n"
            )

            yield b"Cache-Control: no-cache\r\n"

            yield b"\r\n"

            # The actual JPEG
            yield frame

            yield b"\r\n"


            # Don't spin the CPU
            time.sleep(0.03)


    response = Response(
        generate(),
        status=200,
        mimetype=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        )
    )


    # --------------------------------------------------------
    # STREAM HEADERS
    # --------------------------------------------------------

    response.headers["Cache-Control"] = (
        "no-cache, no-store, must-revalidate"
    )

    response.headers["Pragma"] = "no-cache"

    response.headers["Expires"] = "0"

    response.headers["Access-Control-Allow-Origin"] = "*"

    # Disable proxy buffering where supported
    response.headers["X-Accel-Buffering"] = "no"


    return response


# ============================================================
# RUN LOCALLY
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )
```
