import os
import cv2
import numpy as np
from converter import get_video_info, convert_video_to_gif

def create_sample_video(output_path="sample.mp4", duration=5, fps=30, width=640, height=360):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = duration * fps
    for i in range(total_frames):
        # Create animated frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Bouncing circle
        cx = int((i * 10) % width)
        cy = int(height / 2 + 50 * np.sin(i * 0.1))
        cv2.circle(frame, (cx, cy), 30, (0, 255, 128), -1)
        
        # Frame counter text
        time_sec = i / fps
        cv2.putText(
            frame,
            f"Frame {i+1}/{total_frames} ({time_sec:.2f}s)",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2
        )
        out.write(frame)
        
    out.release()
    print(f"Created sample video: {output_path}")

def run_tests():
    sample_mp4 = "sample_test.mp4"
    output_gif = "output_test.gif"
    
    create_sample_video(sample_mp4, duration=5, fps=30)
    
    # 1. Test video info
    info = get_video_info(sample_mp4)
    print("Video Info:", info)
    assert info["duration"] == 5.0
    assert info["fps"] == 30.0
    assert info["width"] == 640
    assert info["height"] == 360
    
    # 2. Test trimming from 1.0s to 3.5s with 1.5x speed
    print("Testing conversion with trim (1.0s - 3.5s) and 1.5x speed...")
    convert_video_to_gif(
        input_path=sample_mp4,
        output_path=output_gif,
        start_time=1.0,
        end_time=3.5,
        speed=1.5,
        target_fps=15,
        target_width=320,
        quality="High"
    )
    
    assert os.path.exists(output_gif)
    file_size = os.path.getsize(output_gif)
    print(f"GIF successfully created! Size: {file_size} bytes")
    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
