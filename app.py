```python
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import threading
import time

app = Flask(__name__)
CORS(app)

# ============================================================
# LATEST JPEG FRAME
# ============================================================

latest_frame = None
frame_lock = threading.Lock()


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return "Sentry Stream Server Running"


# ============================================================
# RECEIVE JPEG FROM YOLO PYTHON
# ============================================================

@app.route("/frame", methods=["POST"])
def receive_frame():

    global latest_frame

    # Your YOLO code sends:
    # data=encoded.tobytes()
    # Content-Type: image/jpeg

    frame = request.get_data()

    if not frame:
        return jsonify({
            "error": "No JPEG received"
        }), 400

    # Store ONLY the newest JPEG
    with frame_lock:
        latest_frame = frame

    return jsonify({
        "status": "received",
        "bytes": len(frame)
    })


# ============================================================
# MJPEG STREAM
# ============================================================

@app.route("/stream")
def stream():

    def generate():

        while True:

            with frame_lock:
                frame = latest_frame

            # Wait until YOLO sends the first frame
            if frame is None:

                time.sleep(0.01)

                continue

            # Send JPEG directly
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: "
                + str(len(frame)).encode()
                + b"\r\n"
                b"Cache-Control: no-cache\r\n"
                b"\r\n"
                + frame
                + b"\r\n"
            )

            # Small delay to avoid hammering the connection
            time.sleep(0.01)

    response = Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

    response.headers["Cache-Control"] = (
        "no-cache, no-store, must-revalidate"
    )

    response.headers["Pragma"] = "no-cache"

    response.headers["Expires"] = "0"

    response.headers["Access-Control-Allow-Origin"] = "*"

    # Tell reverse proxies not to buffer the stream
    response.headers["X-Accel-Buffering"] = "no"

    return response


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    with frame_lock:
        available = latest_frame is not None

    return jsonify({
        "status": "online",
        "frame_available": available
    })


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    print("=" * 50)
    print("SENTRY JPEG STREAM SERVER")
    print("=" * 50)

    print()
    print("HTTP server:")
    print("http://0.0.0.0:5000")

    print()
    print("JPEG upload:")
    print("POST /frame")

    print()
    print("MJPEG stream:")
    print("GET /stream")

    print("=" * 50)

    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True,
        debug=False
    )
```
