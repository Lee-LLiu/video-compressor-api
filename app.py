from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import subprocess
import threading

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "/tmp"

tasks = {}

@app.route("/")
def home():
    return "FFmpeg Stable Compressor API Running"

# ======================
# 后台执行 FFmpeg
# ======================
def ffmpeg_worker(task_id):
    task = tasks[task_id]
    input_path = task["input"]
    output_path = task["output"]

    try:
        tasks[task_id]["status"] = "processing"

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

        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        tasks[task_id]["status"] = "done"

    except Exception as e:
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = str(e)

# ======================
# 上传接口（不做耗时操作！）
# ======================
@app.route("/upload", methods=["POST"])
def upload():
    if "video" not in request.files:
        return jsonify({
            "success": False,
            "message": "没有收到视频"
        })

    file = request.files["video"]
    task_id = str(uuid.uuid4())

    input_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_in.mp4")
    output_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_out.mp4")

    file.save(input_path)

    tasks[task_id] = {
        "status": "queued",
        "input": input_path,
        "output": output_path
    }

    # ⭐关键：异步执行（不阻塞请求）
    thread = threading.Thread(target=ffmpeg_worker, args=(task_id,))
    thread.start()

    return jsonify({
        "success": True,
        "task_id": task_id
    })

# ======================
# 状态查询
# ======================
@app.route("/status/<task_id>")
def status(task_id):
    if task_id not in tasks:
        return jsonify({
            "success": False,
            "message": "task不存在"
        })

    task = tasks[task_id]

    if task["status"] == "done":
        original = os.path.getsize(task["input"])
        compressed = os.path.getsize(task["output"])

        return jsonify({
            "success": True,
            "status": "done",
            "filename": os.path.basename(task["input"]),
            "original_size": original,
            "compressed_size": compressed,
            "download_url": f"/download/{task_id}"
        })

    if task["status"] == "error":
        return jsonify({
            "success": False,
            "status": "error",
            "message": task.get("error", "unknown error")
        })

    return jsonify({
        "success": True,
        "status": task["status"]
    })

# ======================
# 下载接口
# ======================
@app.route("/download/<task_id>")
def download(task_id):
    if task_id not in tasks:
        return "not found", 404

    return send_file(
        tasks[task_id]["output"],
        as_attachment=True
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
