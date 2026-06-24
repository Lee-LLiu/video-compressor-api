from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import subprocess
import threading

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "/tmp"

# 用来存任务状态
tasks = {}

@app.route("/")
def home():
    return "FFmpeg Async Video Compressor API Running"

# =========================
# 后台执行 FFmpeg
# =========================
def run_ffmpeg(task_id, input_path, output_path):
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

        subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

        tasks[task_id]["status"] = "done"
        tasks[task_id]["output"] = output_path

    except Exception as e:
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = str(e)

# =========================
# 上传接口（创建任务）
# =========================
@app.route("/upload", methods=["POST"])
def upload():
    if "video" not in request.files:
        return jsonify({
            "success": False,
            "message": "没有收到视频"
        })

    file = request.files["video"]
    task_id = str(uuid.uuid4())

    input_name = f"{task_id}_input.mp4"
    output_name = f"{task_id}_output.mp4"

    input_path = os.path.join(UPLOAD_FOLDER, input_name)
    output_path = os.path.join(UPLOAD_FOLDER, output_name)

    file.save(input_path)

    tasks[task_id] = {
        "status": "queued",
        "input": input_path,
        "output": output_path
    }

    # 开线程执行任务
    thread = threading.Thread(
        target=run_ffmpeg,
        args=(task_id, input_path, output_path)
    )
    thread.start()

    return jsonify({
        "success": True,
        "task_id": task_id
    })

# =========================
# 查询任务状态
# =========================
@app.route("/status/<task_id>")
def status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({
            "success": False,
            "message": "任务不存在"
        })

    if task["status"] == "done":
        size = os.path.getsize(task["output"])
        return jsonify({
            "success": True,
            "status": "done",
            "compressed_size": size,
            "download_url": f"/download/{task_id}"
        })

    return jsonify({
        "success": True,
        "status": task["status"]
    })

# =========================
# 下载接口
# =========================
@app.route("/download/<task_id>")
def download(task_id):
    task = tasks.get(task_id)
    if not task or task["status"] != "done":
        return "文件未完成或不存在", 404

    return send_file(task["output"], as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
