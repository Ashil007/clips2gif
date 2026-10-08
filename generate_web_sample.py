import os
import cv2
import numpy as np
import math
import subprocess
import imageio_ffmpeg

def generate_web_compliant_sample():
    temp_mp4 = "sample_temp.mp4"
    final_mp4 = "sample_test.mp4"
    
    duration = 5
    fps = 30
    width = 640
    height = 360
    total_frames = duration * fps
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_mp4, fourcc, fps, (width, height))
    
    for i in range(total_frames):
        t = i / fps
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Color gradient waves
        r_val = int(127 + 127 * math.sin(t * 2))
        g_val = int(127 + 127 * math.sin(t * 2 + 2))
        b_val = int(127 + 127 * math.sin(t * 2 + 4))
        
        for y in range(height):
            ratio = y / height
            r = int(r_val * (1 - ratio) + 30 * ratio)
            g = int(g_val * (1 - ratio) + 50 * ratio)
            b = int(b_val * (1 - ratio) + 120 * ratio)
            frame[y, :] = [b % 256, g % 256, r % 256]

        # Bouncing Starburst / Circle
        cx = int(width / 2 + (width / 3) * math.cos(t * 3))
        cy = int(height / 2 + (height / 4) * math.sin(t * 5))
        
        cv2.circle(frame, (cx, cy), 35, (255, 255, 255), -1)
        cv2.circle(frame, (cx, cy), 25, (0, 200, 255), -1)
        
        # Satellite
        sat_x = int(cx + 60 * math.cos(t * 8))
        sat_y = int(cy + 60 * math.sin(t * 8))
        cv2.circle(frame, (sat_x, sat_y), 12, (255, 100, 0), -1)

        # Centered Text
        text = "SAMPLE GIF DEMO"
        cv2.putText(frame, text, (int(width/2 - 140), int(height/2 + 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 4)
        cv2.putText(frame, text, (int(width/2 - 140), int(height/2 + 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        
        out.write(frame)
        
    out.release()
    
    # Convert to standard web-compatible H.264 (yuv420p) via FFmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe, "-y",
        "-i", temp_mp4,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        final_mp4
    ]
    
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
    subprocess.run(cmd, check=True, startupinfo=startupinfo)
    if os.path.exists(temp_mp4):
        os.remove(temp_mp4)
        
    print(f"Successfully generated H.264 Web-compliant sample video at {final_mp4}")

if __name__ == "__main__":
    generate_web_compliant_sample()
