import os
import time
import uuid
import shutil
import werkzeug.utils
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS

from converter import get_video_info, convert_video_to_gif, convert_with_target_size, COMPRESSION_PROFILES

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "outputs")
SAMPLE_VIDEO_PATH = os.path.join(os.path.dirname(__file__), "sample_test.mp4")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv', 'm4v'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_old_files(max_age_seconds=3600):
    now = time.time()
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        if not os.path.exists(folder):
            continue
        for fname in os.listdir(folder):
            fpath = os.path.join(folder, fname)
            if os.path.isfile(fpath):
                if now - os.path.getmtime(fpath) > max_age_seconds:
                    try:
                        os.remove(fpath)
                    except Exception:
                        pass

@app.before_request
def auto_cleanup():
    cleanup_old_files()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/g/<gif_filename>")
def share_page(gif_filename):
    gif_path = os.path.join(OUTPUT_FOLDER, gif_filename)
    if not os.path.exists(gif_path):
        return redirect(url_for('index'))
    return render_template("share.html", gif_filename=gif_filename)

@app.route("/api/sample", methods=["POST", "GET"])
def load_sample_video():
    if not os.path.exists(SAMPLE_VIDEO_PATH):
        from test_converter import create_sample_video
        create_sample_video(SAMPLE_VIDEO_PATH, duration=5, fps=30)
        
    video_id = f"sample_{uuid.uuid4().hex[:8]}.mp4"
    target_path = os.path.join(UPLOAD_FOLDER, video_id)
    shutil.copyfile(SAMPLE_VIDEO_PATH, target_path)
    
    info = get_video_info(target_path)
    return jsonify({
        "video_id": video_id,
        "filename": "sample_video.mp4",
        "duration": info["duration"],
        "width": info["width"],
        "height": info["height"],
        "fps": info["fps"],
        "total_frames": info["total_frames"]
    })

@app.route("/api/upload", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400
        
    file = request.files["video"]
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported video format. Allowed: MP4, MOV, AVI, MKV, WEBM"}), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    video_id = f"{uuid.uuid4().hex}.{ext}"
    saved_path = os.path.join(UPLOAD_FOLDER, video_id)
    file.save(saved_path)

    try:
        info = get_video_info(saved_path)
    except Exception as e:
        if os.path.exists(saved_path):
            os.remove(saved_path)
        return jsonify({"error": f"Failed to inspect video: {str(e)}"}), 500

    return jsonify({
        "video_id": video_id,
        "filename": werkzeug.utils.secure_filename(file.filename),
        "duration": info["duration"],
        "width": info["width"],
        "height": info["height"],
        "fps": info["fps"],
        "total_frames": info["total_frames"]
    })

@app.route("/api/video/<video_id>")
def stream_video(video_id):
    return send_from_directory(UPLOAD_FOLDER, video_id)

@app.route("/api/convert", methods=["POST"])
def convert_video():
    data = request.json or {}
    video_id = data.get("video_id")
    if not video_id:
        return jsonify({"error": "Missing video_id"}), 400

    input_path = os.path.join(UPLOAD_FOLDER, video_id)
    if not os.path.exists(input_path):
        return jsonify({"error": "Video file expired or not found"}), 404

    start_time = float(data.get("start_time", 0.0))
    end_time = float(data.get("end_time", 0.0))
    speed = float(data.get("speed", 1.0))
    target_fps = int(data.get("target_fps", 15))
    target_width = int(data.get("target_width", 480))
    
    caption_top = data.get("caption_top", "")
    caption_bottom = data.get("caption_bottom", "")
    caption_top_y = float(data.get("caption_top_y", 0.08))
    caption_bottom_y = float(data.get("caption_bottom_y", 0.82))
    
    boomerang = bool(data.get("boomerang", False))
    reverse = bool(data.get("reverse", False))
    output_format = data.get("output_format", "gif").lower()
    loop_count = int(data.get("loop_count", 0))

    dither = data.get("dither", "bayer")
    max_colors = int(data.get("max_colors", 256))
    target_mb = float(data.get("target_mb", 0.0))
    profile_level = data.get("profile_level", None)
    if profile_level is not None:
        profile_level = int(profile_level)

    gif_filename = f"{uuid.uuid4().hex[:10]}.{output_format}"
    output_path = os.path.join(OUTPUT_FOLDER, gif_filename)

    try:
        if target_mb > 0.0:
            convert_with_target_size(
                input_path=input_path,
                output_path=output_path,
                target_mb=target_mb,
                start_time=start_time,
                end_time=end_time,
                speed=speed,
                initial_width=target_width,
                initial_fps=target_fps,
                caption_top=caption_top,
                caption_bottom=caption_bottom,
                caption_top_y=caption_top_y,
                caption_bottom_y=caption_bottom_y,
                boomerang=boomerang,
                reverse=reverse,
                output_format=output_format,
                loop_count=loop_count
            )
        else:
            convert_video_to_gif(
                input_path=input_path,
                output_path=output_path,
                start_time=start_time,
                end_time=end_time,
                speed=speed,
                target_fps=target_fps,
                target_width=target_width,
                quality="Ultra",
                dither=dither,
                max_colors=max_colors,
                caption_top=caption_top,
                caption_bottom=caption_bottom,
                caption_top_y=caption_top_y,
                caption_bottom_y=caption_bottom_y,
                boomerang=boomerang,
                reverse=reverse,
                output_format=output_format,
                loop_count=loop_count,
                profile_level=profile_level
            )
        
        file_size = os.path.getsize(output_path)
        file_size_mb = file_size / (1024 * 1024)

        prof_name = COMPRESSION_PROFILES.get(profile_level, {}).get("name", "Custom") if profile_level else "Custom"

        return jsonify({
            "success": True,
            "gif_url": f"/api/download/{gif_filename}",
            "share_url": f"/g/{gif_filename}",
            "filename": gif_filename,
            "size_mb": round(file_size_mb, 2),
            "profile_name": prof_name
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/download/<filename>")
def download_gif(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=False)

if __name__ == "__main__":
    print("Starting Video to GIF Web Server on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
