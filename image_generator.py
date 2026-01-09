import os
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# ================== PATHS ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "images", "output")
FONT_BOLD_PATH = os.path.join(BASE_DIR, "fonts", "arialbd.ttf")

os.makedirs(OUTPUT_DIR, exist_ok=True)
W, H = 1080, 1080 

def get_font(size):
    try:
        return ImageFont.truetype(FONT_BOLD_PATH, size)
    except:
        return ImageFont.load_default()

# Change the function definition line to match the app.py call exactly
def generate_news_image(headline, info_text, image_url, output_name):
    # 1. Create Base Canvas (Dark Mode)
    img = Image.new("RGB", (1080, 1080), (15, 17, 26))
    draw = ImageDraw.Draw(img)
    
    # 2. Main Photo Handling (Top 60%)
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(image_url, headers=headers, timeout=10)
        photo = Image.open(BytesIO(r.content)).convert("RGB").resize((1080, 620), Image.Resampling.LANCZOS)
        img.paste(photo, (0, 0))
    except:
        draw.rectangle([0, 0, 1080, 620], fill=(30, 35, 50))

    # 3. Wirally Style Translucent Bar
    overlay = Image.new('RGBA', (1080, 1080), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    bar_h = 430 
    draw_ov.rectangle([0, 1080 - bar_h, 1080, 1080], fill=(13, 56, 74, 245)) 
    img.paste(overlay, (0, 0), overlay)
    
    # 4. Drawing Text Logic
    def draw_text_auto(text, y, max_h, initial_size, is_bold):
        size = initial_size
        while size > 20:
            font = get_font(size, is_bold)
            lines, current_line = [], []
            for word in text.split():
                test_line = ' '.join(current_line + [word])
                if draw.textbbox((0, 0), test_line, font=font)[2] <= 980:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            lines.append(' '.join(current_line))
            if len(lines) * (size + 12) <= max_h:
                for line in lines:
                    draw.text((50, y), line, fill=(255, 255, 255), font=font)
                    y += (size + 12)
                return y
            size -= 3
        return y

    # Draw the big Headline
    curr_y = draw_text_auto(headline.upper(), 1080 - 400, 140, 68, True)
    # Draw the 3-4 lines of info
    draw_text_auto(info_text.upper(), curr_y + 10, 240, 34, True)

    # 5. Branding & Save
    draw.text((50, 1030), "FOLLOW @TRENDSCOPE | INDIA", fill=(0, 210, 255), font=get_font(24, True))
    save_path = os.path.join(OUTPUT_DIR, output_name)
    img.save(save_path)
    return save_path