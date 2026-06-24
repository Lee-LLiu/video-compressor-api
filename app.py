from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
import threading
import subprocess

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "/tmp"
OUTPUT_FOLDER = "/tmp"

tasks = {}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return "FFmpeg Async API Running"


# ========================
# 上传 + 立即返回 task_id
# ========================
@app.route("/upload", methods=["POST"])
def upload():
    if "video" not in request.files:
        return jsonify({"success": False, "message": "没有收到视频"})

    file = request.files["video"]

    task_id = str(uuid.uuid4())

    input_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_FOLDER, f"{task_id}_out.mp4")

    file.save(input_path)

    tasks[task_id] = {
        "status": "processing",
        "input_path": input_path,
        "output_path": output_path
    }

    thread = threading.Thread(
        target=compress_video,
        args=(task_id,)
    )
    thread.start()

    return jsonify({
        "success": True,
        "task_id": task_id
    })


# ========================
# FFmpeg后台任务
# ========================
def compress_video(task_id):
    task = tasks[task_id]

    input_path = task["input_path"]
    output_path = task["output_path"]

    try:
        command = [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-vcodec", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-acodec", "aac",
            output_path
        ]

        subprocess.run(command, check=True, timeout=120)

        input_size = os.path.getsize(input_path)
        output_size = os.path.getsize(output_path)

        tasks[task_id].update({
            "status": "done",
            "input_size": input_size,
            "output_size": output_size,
            "download_url": f"/download/{task_id}"
        })

    except Exception as e:
        tasks[task_id].update({
            "status": "error",
            "message": str(e)
        })


# ========================
# 查询状态
# ========================
@app.route("/status/<task_id>")
def status(task_id):
    return jsonify(tasks.get(task_id, {"status": "not_found"}))


# ========================
# 下载文件
# ========================
@app.route("/download/<task_id>")
def download(task_id):
    task = tasks.get(task_id)

    if not task or task["status"] != "done":
        return jsonify({"error": "not ready"})

    return send_from_directory(
        OUTPUT_FOLDER,
        os.path.basename(task["output_path"]),
        as_attachment=True
    )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000
    )
