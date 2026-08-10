
from flask import Flask, Response
import requests
import os

app = Flask(__name__)

SOURCE = "http://127.0.0.1:8080/stream"

session = requests.Session()
session.headers["ngrok-skip-browser-warning"] = "true"


@app.route("/stream")
def stream():

    r = session.get(
        SOURCE,
        stream=True,
        timeout=(10, None)
    )

    return Response(
        r.iter_content(chunk_size=280),
        content_type="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        threaded=True
    )
