from flask import Flask, request, jsonify, send_file
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

@app.route("/download/<filename>")
def download(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(filepath):
        return "文件不存在", 404

    return send_file(filepath, as_attachment=True)

@app.route("/upload", methods=["POST"])
def upload():
    if "video" not in request.files:
        return jsonify({
            "success": False,
            "message": "没有收到视频"
        })

    file = request.files["video"]
    uid = str(uuid.uuid4())

    input_name = f"{uid}_input.mp4"
    output_name = f"{uid}_compressed.mp4"

    input_path = os.path.join(UPLOAD_FOLDER, input_name)
    output_path = os.path.join(UPLOAD_FOLDER, output_name)

    file.save(input_path)

    command = [
        "ffmpeg",
        "-i", input_path,
        "-vcodec", "libx264",
        "-crf", "32",
        "-preset", "fast",
        "-acodec", "aac",
        "-b:a", "96k",
        "-y",
        output_path
    ]

    # 执行 FFmpeg 命令
    subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    )

    original_size = os.path.getsize(input_path)
    compressed_size = os.path.getsize(output_path)

    return jsonify({
        "success": True,
        "filename": file.filename,
        "original_size": original_size,
        "compressed_size": compressed_size,
        "download_url": f"https://video-compressor-api-nl0b.onrender.com/download/{output_name}"
    })

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000
    )
