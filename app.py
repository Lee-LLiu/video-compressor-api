from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import subprocess

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "/tmp"

# 注意：此字典存储在内存中，重启服务器后数据会丢失
tasks = {}

@app.route("/")
def home():
    return "FFmpeg Video Compressor API Running"

@app.route("/upload", methods=["POST"])
def upload():
    if "video" not in request.files:
        return jsonify({
            "success": False,
            "message": "没有收到视频"
        })

    file = request.files["video"]
    task_id = str(uuid.uuid4())

    input_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_input.mp4")
    output_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_output.mp4")

    file.save(input_path)

    tasks[task_id] = {
        "status": "processing",
        "input": input_path,
        "output": output_path
    }

    try:
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

        # 注意：此处为同步执行，如果视频很大，请求会阻塞
        subprocess.run(command, check=True)
        tasks[task_id]["status"] = "done"

    except Exception as e:
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = str(e)

    return jsonify({
        "success": True,
        "task_id": task_id
    })

@app.route("/status/<task_id>")
def status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({
            "success": False,
            "message": "task不存在"
        })

    if task["status"] == "done":
        original_size = os.path.getsize(task["input"])
        compressed_size = os.path.getsize(task["output"])
        return jsonify({
            "success": True,
            "status": "done",
            "filename": os.path.basename(task["input"]),
            "original_size": original_size,
            "compressed_size": compressed_size,
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

@app.route("/download/<task_id>")
def download(task_id):
    task = tasks.get(task_id)
    if not task or task["status"] != "done":
        return "Not Found or Not Ready", 404

    return send_file(task["output"], as_attachment=True)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000
    )
