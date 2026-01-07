import os
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "images", "output")
LOGO_PATH = os.path.join(BASE_DIR, "assets", "channels4_profile (1) (1).png")
FONT_PATH = os.path.join(BASE_DIR, "fonts", "arial.ttf")
FONT_BOLD_PATH = os.path.join(BASE_DIR, "fonts", "arialbd.ttf")

os.makedirs(OUTPUT_DIR, exist_ok=True)

BG_COLOR = (15, 17, 26)
TEXT_COLOR = (255, 255, 255)
ACCENT_COLOR = (0, 210, 255)
GRAY_TEXT = (160, 165, 180)
W, H = 1080, 1080

def get_font(size, bold=False):
    path = FONT_BOLD_PATH if bold else FONT_PATH
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def draw_wrapped_text(draw, text, x, y, max_w, font_obj, color, spacing=12):
    words = text.split()
    lines, current_line = [], []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if draw.textbbox((0, 0), test_line, font=font_obj)[2] <= max_w:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))
    for line in lines:
        draw.text((x, y), line, fill=color, font=font_obj)
        y += font_obj.size + spacing
    return y

def generate_news_image(headline, description, image_url, output_name="post.png"):
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw.rectangle([60, 60, 65, 95], fill=ACCENT_COLOR)
    draw.text((80, 60), "TRENDSCOPE | INDIA", fill=ACCENT_COLOR, font=get_font(30, True))

    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA").resize((100, 100))
            img.paste(logo, (920, 45), logo)
        except: pass

    try:
        r = requests.get(image_url, timeout=10)
        photo = Image.open(BytesIO(r.content)).convert("RGB").resize((960, 520))
        mask = Image.new("L", (960, 520), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, 960, 520], 20, fill=255)
        img.paste(photo, (60, 140), mask)
    except:
        draw.rounded_rectangle([60, 140, 1020, 660], 20, outline=GRAY_TEXT)

    y = 700
    y = draw_wrapped_text(draw, headline.upper(), 60, y, 960, get_font(60, True), TEXT_COLOR)
    draw_wrapped_text(draw, description[:180]+"...", 60, y+20, 960, get_font(34), GRAY_TEXT)

    draw.line([60, 1000, 1020, 1000], fill=(50, 50, 60), width=2)
    draw.text((60, 1020), "FOLLOW @TRENDSCOPE", fill=ACCENT_COLOR, font=get_font(28, True))

    path = os.path.join(OUTPUT_DIR, output_name)
    img.save(path)
    return path