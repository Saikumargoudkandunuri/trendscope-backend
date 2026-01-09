import os
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# ================== PATHS ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "images", "output")
LOGO_PATH = os.path.join(BASE_DIR, "assets", "channels4_profile (1) (1).png")
FONT_PATH = os.path.join(BASE_DIR, "fonts", "arial.ttf")
FONT_BOLD_PATH = os.path.join(BASE_DIR, "fonts", "arialbd.ttf")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================== THEME ==================
BG_COLOR = (15, 17, 26)       # Deep Dark Navy
TEXT_COLOR = (255, 255, 255)  # Pure White
ACCENT_COLOR = (0, 210, 255)  # Cyan Blue
GRAY_TEXT = (180, 185, 200)   # Soft Gray
W, H = 1080, 1080

def get_font(size, bold=False):
    """Helper to load font or fallback to default"""
    path = FONT_BOLD_PATH if bold else FONT_PATH
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def generate_news_image(headline, info_points, image_url, output_name):
    # Create Dark Canvas
    img = Image.new("RGB", (1080, 1080), (15, 17, 26))
    draw = ImageDraw.Draw(img)
    
    # 1. Main Photo (Top 60%)
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(image_url, headers=headers, timeout=10)
        photo = Image.open(BytesIO(r.content)).convert("RGB").resize((1080, 620), Image.Resampling.LANCZOS)
        img.paste(photo, (0, 0))
    except:
        draw.rectangle([0, 0, 1080, 620], fill=(30, 35, 50))

    # 2. Flexible Text Drawing Logic
    def draw_text(text, y, max_h, size, color, is_bold):
        while size > 18:
            font = get_font(size, is_bold)
            words = text.split()
            lines, current_line = [], []
            for word in words:
                test_line = ' '.join(current_line + [word])
                if draw.textbbox((0, 0), test_line, font=font)[2] <= 980:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            lines.append(' '.join(current_line))
            if len(lines) * (size + 12) <= max_h:
                for line in lines:
                    draw.text((50, y), line, fill=color, font=font)
                    y += (size + 12)
                return y
            size -= 3
        return y

    # --- Draw Hinglish headline ---
    curr_y = draw_text(headline.upper(), 650, 140, 72, (0, 210, 255), True)
    
    # --- Draw the 3-4 Fact Lines ---
    curr_y += 10
    for point in info_points:
        curr_y = draw_text(f"• {point}", curr_y, 60, 34, (255, 255, 255), False)

    save_path = os.path.join(OUTPUT_DIR, output_name)
    img.save(save_path)
    return save_path