import os
from PIL import Image, ImageDraw, ImageFont

def generate_og_image(output_path):
    width, height = 1200, 630
    img = Image.new('RGB', (width, height), color='#000000')
    draw = ImageDraw.Draw(img)

    # Draw border grid card
    draw.rectangle([40, 40, width - 40, height - 40], outline='#222222', width=2)
    draw.rectangle([42, 42, width - 42, height - 42], fill='#0c0c0c')

    # Draw decorative accents
    draw.rectangle([80, 80, 160, 160], fill='#ffffff')
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 52)
        font_sub = ImageFont.truetype("arial.ttf", 26)
        font_badge = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font_title = font_sub = font_badge = ImageFont.load_default()

    # Draw text inside box
    draw.text((100, 95), "GIF", fill="#000000", font=font_badge)

    draw.text((80, 200), "Video to GIF Converter", fill="#ffffff", font=font_title)
    draw.text((80, 275), "Free Online MP4, MOV, WEBM to GIF, WebP & MP4 Studio", fill="#737373", font=font_sub)

    # Badges
    badges = ["⚡ High-Speed FFmpeg", "🪃 Boomerang & Reverse", "💬 Meme Captions", "💎 5 Quality Profiles", "🔒 100% Free & Secure"]
    x, y = 80, 360
    for badge in badges:
        bbox = draw.textbbox((x, y), badge, font=font_badge)
        bw = bbox[2] - bbox[0]
        if x + bw + 30 > width - 80:
            x = 80
            y += 60
        draw.rectangle([x, y, x + bw + 24, y + 40], fill='#141414', outline='#262626')
        draw.text((x + 12, y + 8), badge, fill="#ffffff", font=font_badge)
        x += bw + 40

    # Footer url
    draw.text((80, 520), "https://clips2gif.onrender.com/", fill="#ffffff", font=font_sub)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    print(f"Generated OG image at {output_path}")

if __name__ == '__main__':
    generate_og_image("static/og-image.png")
