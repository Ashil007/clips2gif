import os
import sys
import subprocess
import imageio_ffmpeg
import cv2

def get_ffmpeg_path():
    return imageio_ffmpeg.get_ffmpeg_exe()

def get_system_font_path():
    if os.name == 'nt':
        font_candidates = [
            r"C:\Windows\Fonts\impact.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\arial.ttf"
        ]
        for f in font_candidates:
            if os.path.exists(f):
                return f.replace("\\", "/").replace(":", r"\:")
    elif sys.platform == 'darwin':
        mac_fonts = [
            "/System/Library/Fonts/Supplemental/Impact.ttf",
            "/Library/Fonts/Impact.ttf",
            "/System/Library/Fonts/Helvetica.ttc"
        ]
        for f in mac_fonts:
            if os.path.exists(f):
                return f
    else:
        linux_fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
        ]
        for f in linux_fonts:
            if os.path.exists(f):
                return f
    return None

def get_video_info(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 25.0
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0
    
    cap.release()
    return {
        "duration": duration,
        "width": width,
        "height": height,
        "fps": fps,
        "total_frames": total_frames
    }

COMPRESSION_PROFILES = {
    1: {"name": "Smallest File Size (Minimal MB)", "width": 320, "fps": 10, "max_colors": 64, "dither": "none"},
    2: {"name": "Compact (Low MB)", "width": 360, "fps": 12, "max_colors": 128, "dither": "bayer"},
    3: {"name": "Balanced (Medium MB)", "width": 480, "fps": 15, "max_colors": 192, "dither": "bayer"},
    4: {"name": "High Quality (Large MB)", "width": 640, "fps": 20, "max_colors": 256, "dither": "sierra2_4a"},
    5: {"name": "Maximum Quality (Highest MB)", "width": -1, "fps": 24, "max_colors": 256, "dither": "sierra2_4a"}
}

def convert_video_to_gif(
    input_path: str,
    output_path: str,
    start_time: float = 0.0,
    end_time: float = None,
    speed: float = 1.0,
    target_fps: int = 15,
    target_width: int = 480,
    quality: str = "Ultra",
    dither: str = "bayer",
    max_colors: int = 256,
    caption_top: str = "",
    caption_bottom: str = "",
    caption_top_y: float = 0.08,
    caption_bottom_y: float = 0.82,
    boomerang: bool = False,
    reverse: bool = False,
    output_format: str = "gif",
    loop_count: int = 0,
    profile_level: int = None
):
    """
    Advanced multi-stage video to GIF converter with draggable custom Y-position captions.
    """
    if profile_level in COMPRESSION_PROFILES:
        prof = COMPRESSION_PROFILES[profile_level]
        target_width = prof["width"]
        target_fps = prof["fps"]
        max_colors = prof["max_colors"]
        dither = prof["dither"]

    ffmpeg_exe = get_ffmpeg_path()
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    cmd = [ffmpeg_exe, "-y"]
    
    if start_time > 0:
        cmd.extend(["-ss", f"{start_time:.3f}"])
        
    if end_time is not None and end_time > start_time:
        cmd.extend(["-to", f"{end_time:.3f}"])
        
    cmd.extend(["-i", input_path])
    
    filters = []
    
    if reverse and not boomerang:
        filters.append("reverse")

    if abs(speed - 1.0) > 0.01:
        pts_factor = 1.0 / speed
        filters.append(f"setpts={pts_factor:.4f}*PTS")
        
    if target_fps > 0:
        filters.append(f"fps={target_fps}")
        
    if target_width > 0:
        filters.append(f"scale={target_width}:-2:flags=lanczos")
        
    font_path = get_system_font_path()
    
    # Draggable Y position mapping for Top & Bottom Captions
    if caption_top and caption_top.strip():
        txt = caption_top.strip().replace("'", "\\'").replace(":", "\\:").upper()
        draw_top = f"drawtext=text='{txt}'"
        if font_path:
            draw_top += f":fontfile='{font_path}'"
        top_y_expr = f"h*{max(0.02, min(0.90, caption_top_y)):.3f}"
        draw_top += f":fontcolor=white:bordercolor=black:borderw=3:fontsize=h/11:x=(w-text_w)/2:y={top_y_expr}"
        filters.append(draw_top)
        
    if caption_bottom and caption_bottom.strip():
        txt = caption_bottom.strip().replace("'", "\\'").replace(":", "\\:").upper()
        draw_bot = f"drawtext=text='{txt}'"
        if font_path:
            draw_bot += f":fontfile='{font_path}'"
        bot_y_expr = f"h*{max(0.02, min(0.90, caption_bottom_y)):.3f}"
        draw_bot += f":fontcolor=white:bordercolor=black:borderw=3:fontsize=h/11:x=(w-text_w)/2:y={bot_y_expr}"
        filters.append(draw_bot)

    base_filter_str = ",".join(filters) if filters else "null"
    
    if boomerang:
        vf_chain = f"[0:v]{base_filter_str}[base];[base]split[fwd][rev_in];[rev_in]reverse[rev];[fwd][rev]concat=n=2:v=1[v_final]"
        last_node = "[v_final]"
    else:
        vf_chain = f"[0:v]{base_filter_str}[v_final]"
        last_node = "[v_final]"
        
    ext = os.path.splitext(output_path)[1].lower()
    
    if ext == ".webp" or output_format == "webp":
        cmd.extend(["-filter_complex", f"{vf_chain}"])
        cmd.extend(["-map", last_node, "-c:v", "libwebp", "-loop", str(loop_count), "-preset", "default", "-lossless", "0", "-q:v", "75"])
    elif ext == ".mp4" or output_format == "mp4":
        cmd.extend(["-filter_complex", f"{vf_chain}"])
        cmd.extend(["-map", last_node, "-c:v", "libx264", "-pix_fmt", "yuv420p"])
    else:
        max_colors_val = max(16, min(256, max_colors))
        palettegen_filter = f"palettegen=max_colors={max_colors_val}:stats_mode=diff"
        
        if dither == "bayer":
            paletteuse_filter = "paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle"
        elif dither == "none":
            paletteuse_filter = "paletteuse=dither=none:diff_mode=rectangle"
        elif dither == "floyd_steinberg":
            paletteuse_filter = "paletteuse=dither=floyd_steinberg:diff_mode=rectangle"
        else:
            paletteuse_filter = "paletteuse=dither=sierra2_4a:diff_mode=rectangle"

        filter_complex = f"{vf_chain};{last_node}split[a][b];[a]{palettegen_filter}[p];[b][p]{paletteuse_filter}"
        cmd.extend(["-filter_complex", filter_complex])
        
        if loop_count >= 0:
            cmd.extend(["-loop", str(loop_count)])
            
    cmd.append(output_path)
    
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        startupinfo=startupinfo
    )
    
    _, stderr = process.communicate()
    
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg conversion failed:\n{stderr}")
        
    return output_path

def convert_with_target_size(
    input_path: str,
    output_path: str,
    target_mb: float,
    start_time: float = 0.0,
    end_time: float = None,
    speed: float = 1.0,
    initial_width: int = 480,
    initial_fps: int = 15,
    **kwargs
):
    curr_width = initial_width
    curr_fps = initial_fps
    curr_colors = 256
    dither_mode = "bayer"

    target_bytes = target_mb * 1024 * 1024

    for attempt in range(5):
        convert_video_to_gif(
            input_path=input_path,
            output_path=output_path,
            start_time=start_time,
            end_time=end_time,
            speed=speed,
            target_fps=curr_fps,
            target_width=curr_width,
            dither=dither_mode,
            max_colors=curr_colors,
            **kwargs
        )

        size = os.path.getsize(output_path)
        if size <= target_bytes:
            break

        if attempt == 0:
            dither_mode = "bayer"
            curr_colors = 192
        elif attempt == 1:
            curr_width = int(curr_width * 0.8)
        elif attempt == 2:
            curr_fps = max(10, int(curr_fps * 0.8))
        elif attempt == 3:
            curr_colors = 128
            dither_mode = "none"
        elif attempt == 4:
            curr_width = int(curr_width * 0.7)

    return output_path

if __name__ == "__main__":
    print("FFmpeg executable:", get_ffmpeg_path())
