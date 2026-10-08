import os
import time
from converter import convert_video_to_gif, get_video_info
from PIL import Image, ImageSequence

def optimize_gif_pil(input_gif_path, output_gif_path):
    """
    Applies Pillow LZW dictionary optimization and frame disposal tuning.
    """
    img = Image.open(input_gif_path)
    frames = []
    durations = []
    
    for frame in ImageSequence.Iterator(img):
        frames.append(frame.copy())
        durations.append(frame.info.get('duration', 66))
        
    if frames:
        frames[0].save(
            output_gif_path,
            save_all=True,
            append_images=frames[1:],
            optimize=True,
            duration=durations,
            loop=0
        )
    return output_gif_path

def test_gif_optimizations():
    sample_mp4 = "sample_test.mp4"
    if not os.path.exists(sample_mp4):
        from test_converter import create_sample_video
        create_sample_video(sample_mp4, duration=5, fps=30)

    print("--- GIF OPTIMIZATION BENCHMARK ---")
    
    # Test 1: Standard GIF
    f1 = "out_standard.gif"
    convert_video_to_gif(
        input_path=sample_mp4,
        output_path=f1,
        start_time=0,
        end_time=5,
        target_fps=15,
        target_width=480,
        quality="Fast"
    )
    s1 = os.path.getsize(f1)
    print(f"1. Standard GIF Size: {s1 / 1024:.2f} KB")

    # Test 2: Ultra High Quality PaletteGen + diff_mode=rectangle + bayer dithering
    f2 = "out_ultra.gif"
    convert_video_to_gif(
        input_path=sample_mp4,
        output_path=f2,
        start_time=0,
        end_time=5,
        target_fps=15,
        target_width=480,
        quality="Ultra",
        dither="bayer",
        max_colors=192
    )
    s2 = os.path.getsize(f2)
    print(f"2. Ultra PaletteGen (Diff + Bayer + 192 Colors) Size: {s2 / 1024:.2f} KB ({(1 - s2/s1)*100:.1f}% reduction)")

    # Test 3: No-dither (Extreme LZW Compression for Memes/Text)
    f3 = "out_nodither.gif"
    convert_video_to_gif(
        input_path=sample_mp4,
        output_path=f3,
        start_time=0,
        end_time=5,
        target_fps=15,
        target_width=480,
        quality="Ultra",
        dither="none",
        max_colors=128
    )
    s3 = os.path.getsize(f3)
    print(f"3. Minimalist No-Dither (128 Colors) Size: {s3 / 1024:.2f} KB ({(1 - s3/s1)*100:.1f}% reduction)")

if __name__ == "__main__":
    test_gif_optimizations()
