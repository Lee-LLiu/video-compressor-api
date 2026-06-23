from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import subprocess

app = Flask(__name__)
CORS(app)

# Render临时目录
UPLOAD_FOLDER = "/tmp"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/")
def home():
    return "FFmpeg Video Compressor API Running"


# =========================
# 🎬 核心接口：上传 + 压缩
# =========================
@app.route("/upload", methods=["POST"])
def upload():

    if "video" not in request.files:
        return jsonify({
            "success": False,
            "message": "没有收到视频"
        })

    file = request.files["video"]

    # 唯一文件名
    uid = str(uuid.uuid4())

    input_path = os.path.join(UPLOAD_FOLDER, uid + "_input.mp4")
    output_path = os.path.join(UPLOAD_FOLDER, uid + "_output.mp4")

    # 保存上传文件
    file.save(input_path)

    # =========================
    # 🎬 FFmpeg压缩核心命令
    # =========================
    try:
        command = [
            "ffmpeg",
            "-i", input_path,
            "-vcodec", "libx264",
            "-crf", "28",
            "-preset", "fast",
            output_path
        ]

        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    except subprocess.CalledProcessError as e:
        return jsonify({
            "success": False,
            "message": "压缩失败",
            "error": str(e)
        })

    # 文件大小
    size = os.path.getsize(output_path)

    return jsonify({
        "success": True,
        "message": "压缩完成",
        "filename": file.filename,
        "output_size_bytes": size,
        "download_url": f"/download/{uid}"
    })


# =========================
# 📥 下载接口
# =========================
@app.route("/download/<file_id>")
def download(file_id):

    path = os.path.join(UPLOAD_FOLDER, file_id + "_output.mp4")

    if not os.path.exists(path):
        return jsonify({
            "success": False,
            "message": "文件不存在"
        })

    return send_file(path, as_attachment=True, download_name="compressed.mp4")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
