from flask import Flask, Response, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# ============================================================
# PYCHARM / YOLO HTTP STREAM EXPOSED THROUGH NGROK
# ============================================================

SOURCE_STREAM_URL = (
    "https://breath-eatery-sequester.ngrok-free.dev/stream"
)


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "service": "Sentry Stream Proxy",
        "stream": "/stream"
    })


# ============================================================
# STREAM PROXY
# ============================================================

@app.route("/stream")
def stream():

    def generate():

        try:

            print("Connecting to YOLO stream...")

            with requests.get(
                SOURCE_STREAM_URL,
                headers={
                    # This header is sent TO NGROK
                    "ngrok-skip-browser-warning": "true",

                    # Request MJPEG
                    "Accept": "multipart/x-mixed-replace"
                },
                stream=True,
                timeout=(10, None)
            ) as response:

                print(
                    "YOLO stream status:",
                    response.status_code
                )

                response.raise_for_status()

                # Forward the stream without modifying
                # the JPEG frames.

                for chunk in response.iter_content(
                    chunk_size=16384
                ):

                    if chunk:
                        yield chunk

        except requests.RequestException as e:

            print(
                "Stream connection error:",
                e
            )

    return Response(
        generate(),
        content_type=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        ),
        headers={
            "Cache-Control": (
                "no-cache, "
                "no-store, "
                "must-revalidate"
            ),
            "Pragma": "no-cache",
            "Expires": "0",

            "Access-Control-Allow-Origin": "*",

            # Disable proxy buffering
            "X-Accel-Buffering": "no"
        }
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    try:

        response = requests.get(
            SOURCE_STREAM_URL,
            headers={
                "ngrok-skip-browser-warning": "true"
            },
            stream=True,
            timeout=5
        )

        response.close()

        return jsonify({
            "status": "online",
            "source_status": response.status_code,
            "source": SOURCE_STREAM_URL
        })

    except Exception as e:

        return jsonify({
            "status": "offline",
            "error": str(e)
        }), 503


# ============================================================
# RENDER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    print("=" * 50)
    print("SENTRY STREAM PROXY")
    print("=" * 50)

    print()
    print("Source:")
    print(SOURCE_STREAM_URL)

    print()
    print("Local endpoint:")
    print("/stream")

    print()
    print("Port:")
    print(port)

    print("=" * 50)

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True,
        debug=False
    )
