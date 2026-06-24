from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import subprocess

app = Flask(__name__)

CORS(app)

UPLOAD_FOLDER = "/tmp"

@app.route("/")
def home():
    return "FFmpeg Video Compressor API Running"

@app.route("/ffmpeg-test")
def ffmpeg_test():
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        return jsonify({
            "success": True,
            "message": "FFmpeg 已安装",
            "output": result.stdout[:200]
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })

@app.route("/upload", methods=["POST"])
def upload():
    if "video" not in request.files:
        return jsonify({
            "success": False,
            "message": "没有收到视频"
        })

    file = request.files["video"]
    uid = str(uuid.uuid4())
    filename = uid + "_" + file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)
    filesize = os.path.getsize(filepath)

    return jsonify({
        "success": True,
        "message": "上传成功",
        "filename": file.filename,
        "saved_path": filepath,
        "size_bytes": filesize
    })

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000
    )
