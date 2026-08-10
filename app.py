
from flask import Flask, Response, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)


# ============================================================
# CONFIGURATION
# ============================================================

SOURCE_STREAM_URL = (
    "https://breath-eatery-sequester.ngrok-free.dev/stream"
)

# Small chunks help reduce buffering/latency.
CHUNK_SIZE = 1024


# ============================================================
# HTTP SESSION
# ============================================================

session = requests.Session()

session.headers.update({

    # Prevent ngrok browser warning page
    "ngrok-skip-browser-warning": "true",

    # Tell ngrok we want MJPEG
    "Accept": "multipart/x-mixed-replace"

})


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return jsonify({

        "status": "online",

        "service": "Sentry Stream Proxy",

        "stream": "/stream",

        "health": "/health"

    })


# ============================================================
# MJPEG STREAM PROXY
# ============================================================

@app.route("/stream")
def stream():

    def generate():

        response = None

        try:

            print(
                "Connecting to YOLO stream..."
            )

            # ------------------------------------------------
            # CONNECT TO NGROK
            # ------------------------------------------------

            response = session.get(

                SOURCE_STREAM_URL,

                stream=True,

                timeout=(10, None)

            )

            print(
                "YOLO stream status:",
                response.status_code
            )

            response.raise_for_status()


            # ------------------------------------------------
            # FORWARD RAW MJPEG DATA
            #
            # Nothing is decoded.
            # Nothing is re-encoded.
            # Nothing is modified.
            # ------------------------------------------------

            for chunk in response.iter_content(

                chunk_size=CHUNK_SIZE

            ):

                if chunk:

                    yield chunk


        except requests.RequestException as e:

            print(
                "Stream connection error:",
                e
            )


        except GeneratorExit:

            # Client disconnected.
            pass


        except Exception as e:

            print(
                "Stream error:",
                e
            )


        finally:

            if response is not None:

                response.close()


            print(
                "YOLO stream disconnected."
            )


    # ========================================================
    # RESPONSE
    # ========================================================

    return Response(

        generate(),

        content_type=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        ),

        headers={

            # ------------------------------------------------
            # Disable browser caching
            # ------------------------------------------------

            "Cache-Control":
                "no-cache, no-store, must-revalidate",

            "Pragma":
                "no-cache",

            "Expires":
                "0",

            # ------------------------------------------------
            # CORS
            # ------------------------------------------------

            "Access-Control-Allow-Origin":
                "*",

            # ------------------------------------------------
            # Disable reverse-proxy buffering
            # ------------------------------------------------

            "X-Accel-Buffering":
                "no",

            # ------------------------------------------------
            # Keep connection alive
            # ------------------------------------------------

            "Connection":
                "keep-alive"

        }

    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    try:

        response = session.get(

            SOURCE_STREAM_URL,

            stream=True,

            timeout=5

        )

        status_code = response.status_code

        response.close()


        if status_code == 200:

            return jsonify({

                "status": "online",

                "source_status":
                    status_code

            })


        return jsonify({

            "status": "error",

            "source_status":
                status_code

        }), 503


    except Exception as e:

        return jsonify({

            "status": "offline",

            "error": str(e)

        }), 503


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    port = int(

        os.environ.get(

            "PORT",

            5000

        )

    )


    print()
    print("=" * 60)
    print("SENTRY STREAM PROXY")
    print("=" * 60)

    print()

    print(
        "Source:"
    )

    print(
        SOURCE_STREAM_URL
    )

    print()

    print(
        "Stream:"
    )

    print(
        f"/stream"
    )

    print()

    print(
        "Health:"
    )

    print(
        f"/health"
    )

    print()

    print(
        "Port:"
    )

    print(
        port
    )

    print()

    print("=" * 60)


    # --------------------------------------------------------
    # Flask
    # --------------------------------------------------------

    app.run(

        host="0.0.0.0",

        port=port,

        threaded=True,

        debug=False

    )
