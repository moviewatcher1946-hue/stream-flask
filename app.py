from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import threading
import time

app = Flask(__name__)
CORS(app)

latest_frame = None
frame_lock = threading.Lock()


@app.route("/")
def home():
    return "Sentry Stream Server Running"


@app.route("/frame", methods=["POST"])
def receive_frame():
    global latest_frame

    frame = request.get_data()

    if not frame:
        return jsonify({"error": "No frame received"}), 400

    with frame_lock:
        latest_frame = frame

    return jsonify({"status": "received"})


@app.route("/stream")
def stream():

    def generate():
        last_frame = None

        while True:

            with frame_lock:
                frame = latest_frame

            if frame is not None and frame != last_frame:
                last_frame = frame

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    b"Content-Length: "
                    + str(len(frame)).encode()
                    + b"\r\n\r\n"
                    + frame
                    + b"\r\n"
                )
            else:
                time.sleep(0.01)

    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )
