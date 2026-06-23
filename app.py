from flask import Flask
from flask import request
from flask import jsonify

from flask_cors import CORS

app = Flask(__name__)

CORS(app)

@app.route("/")
def home():

    return "Video Compressor API Running"


@app.route("/upload", methods=["POST"])
def upload():

    if "video" not in request.files:

        return jsonify({
            "success": False,
            "message": "没有收到视频"
        })

    file = request.files["video"]

    return jsonify({

        "success": True,

        "filename": file.filename,

        "size_bytes": len(file.read())

    })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )
