```python
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import threading
import time
import os

app = Flask(__name__)
CORS(app)

# ============================================================
# SHARED FRAME
# ============================================================

latest_frame = None

frame_lock = threading.Lock()
frame_updated = threading.Condition(frame_lock)

frame_number = 0


# ============================================================
# HOME
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "service": "Sentry Stream Server",
        "status": "online",
        "stream": "/stream",
        "upload": "/frame",
        "health": "/health"
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health", methods=["GET"])
def health():

    with frame_lock:

        available = latest_frame is not None

        current_frame = frame_number

    return jsonify({
        "status": "online",
        "frame_available": available,
        "frame_number": current_frame
    })


# ============================================================
# RECEIVE JPEG
# ============================================================

@app.route("/frame", methods=["POST"])
def receive_frame():

    global latest_frame
    global frame_number

    # --------------------------------------------------------
    # Make sure YOLO sent JPEG
    # --------------------------------------------------------

    content_type = request.headers.get(
        "Content-Type",
        ""
    ).lower()

    if not content_type.startswith("image/jpeg"):

        return jsonify({
            "error": "Expected image/jpeg"
        }), 415


    # --------------------------------------------------------
    # Read raw JPEG bytes
    # --------------------------------------------------------

    frame = request.get_data(
        cache=False,
        as_text=False
    )


    if not frame:

        return jsonify({
            "error": "Empty JPEG"
        }), 400


    # --------------------------------------------------------
    # Basic JPEG validation
    # JPEG starts with FF D8
    # JPEG ends with FF D9
    # --------------------------------------------------------

    if not frame.startswith(b"\xff\xd8"):

        return jsonify({
            "error": "Invalid JPEG data"
        }), 400


    # --------------------------------------------------------
    # Store ONLY newest frame
    # --------------------------------------------------------

    with frame_updated:

        latest_frame = frame

        frame_number += 1

        frame_updated.notify_all()


    return jsonify({
        "status": "received",
        "frame": frame_number,
        "bytes": len(frame)
    })


# ============================================================
# MJPEG STREAM
# ============================================================

@app.route("/stream", methods=["GET"])
def stream():

    def generate():

        last_frame_number = -1

        while True:

            # ------------------------------------------------
            # Wait for a NEW frame
            # ------------------------------------------------

            with frame_updated:

                while (
                    latest_frame is None
                    or frame_number == last_frame_number
                ):

                    frame_updated.wait(
                        timeout=1.0
                    )

                    # Continue checking
                    # if no frame arrived


                frame = latest_frame

                current_number = frame_number


            # ------------------------------------------------
            # Send frame
            # ------------------------------------------------

            if frame is None:
                continue


            last_frame_number = current_number


            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Cache-Control: no-cache\r\n"
                b"Content-Length: "
                + str(len(frame)).encode()
                + b"\r\n\r\n"
                + frame
                + b"\r\n"
            )


    response = Response(

        generate(),

        mimetype=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        )
    )


    # --------------------------------------------------------
    # Streaming headers
    # --------------------------------------------------------

    response.headers["Cache-Control"] = (
        "no-cache, no-store, must-revalidate"
    )

    response.headers["Pragma"] = "no-cache"

    response.headers["Expires"] = "0"

    response.headers["Access-Control-Allow-Origin"] = "*"

    response.headers["X-Accel-Buffering"] = "no"


    return response


# ============================================================
# OPTIONAL: STOP STREAM CLIENTS CLEANLY
# ============================================================

@app.errorhandler(500)
def server_error(error):

    return jsonify({
        "error": "Internal server error"
    }), 500


# ============================================================
# LOCAL DEVELOPMENT ONLY
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    print()
    print("========================================")
    print("SENTRY STREAM SERVER")
    print("========================================")
    print()
    print(f"Port: {port}")
    print()
    print("Upload:")
    print("/frame")
    print()
    print("Stream:")
    print("/stream")
    print()
    print("Health:")
    print("/health")
    print()
    print("========================================")

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True,
        debug=False
    )
```
