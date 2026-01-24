import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# ================== PATHS ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "images", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Fonts
FONT_REGULAR_PATH = os.path.join(BASE_DIR, "fonts", "arial.ttf")
FONT_BOLD_PATH = os.path.join(BASE_DIR, "fonts", "arialbd.ttf")

def get_font(font_size: int, bold: bool = False):
    path = FONT_BOLD_PATH if bold else FONT_REGULAR_PATH
    try:
        return ImageFont.truetype(path, font_size)
    except:
        return ImageFont.load_default()

def generate_news_image(headline, info_text, image_url, output_name):
    W, H = 1080, 1080
    
    # 1. Base Canvas
    img = Image.new("RGB", (W, H), (15, 17, 26))
    draw = ImageDraw.Draw(img)

    # 2. Image Download & Safety Box
    image_loaded = False
    if image_url and "http" in image_url:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(image_url, headers=headers, timeout=10)
            if r.status_code == 200:
                photo = Image.open(BytesIO(r.content)).convert("RGB")
                photo = photo.resize((W, 620), Image.Resampling.LANCZOS)
                img.paste(photo, (0, 0))
                image_loaded = True
        except Exception as e:
            print(f"⚠️ Image Error: {e}")

    # Safety Box if image failed
    if not image_loaded:
        draw.rectangle([0, 0, W, 620], fill=(30, 35, 50))
        draw.rectangle([20, 20, W-20, 600], outline=(0, 200, 255), width=4)
        fallback_font = get_font(60, True)
        draw.text((360, 280), "NEWS UPDATE", fill=(150, 200, 220), font=fallback_font)

    # 3. Text Overlay
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rectangle([0, 600, W, H], fill=(13, 17, 23, 255))
    img.paste(overlay, (0, 0), overlay)

    # 4. Helper: Wrap Text
    def wrap_text(text, font, max_width):
        lines = []
        words = text.split()
        current = []
        for word in words:
            test = " ".join(current + [word])
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] <= max_width:
                current.append(word)
            else:
                lines.append(" ".join(current))
                current = [word]
        if current: lines.append(" ".join(current))
        return lines

    # ======================================================
    # 🔥 STEP 5: PASTE YOUR CLEANING LOGIC HERE 🔥
    # ======================================================
    
    # Clean the Info Text (Remove JSON artifacts if any slipped through)
    if isinstance(info_text, list):
        info_text = "\n".join(info_text) # Convert list to string
    
    # Remove quotes, brackets that might break the look
    info_text = (info_text or "").replace('"', '').replace('{', '').replace('}', '').strip()
    
    # Clean Headline
    headline = (headline or "BREAKING NEWS").replace('"', '').strip().upper()

    # ======================================================
    # END CLEANING LOGIC - DRAWING STARTS BELOW
    # ======================================================

    # 6. Draw Headline
    y_text = 630
    font_size = 65
    
    while True:
        font = get_font(font_size, True)
        lines = wrap_text(headline, font, 980)
        if len(lines) <= 2 or font_size < 35:
            break
        font_size -= 5

    for line in lines[:3]:
        draw.text((50, y_text), line, fill=(255, 215, 0), font=font)
        y_text += font_size + 15

    # 7. Draw Info Text
    y_text += 20
    font_body = get_font(35, False)
    body_lines = wrap_text(info_text, font_body, 980)

    for line in body_lines[:5]:
        draw.text((50, y_text), line, fill=(230, 230, 230), font=font_body)
        y_text += 45

    # 8. Footer
    draw.text((50, 1020), "TRENDSCOPE • LIVE", fill=(0, 200, 255), font=get_font(24, True))

    # 9. Save
    save_path = os.path.join(OUTPUT_DIR, output_name)
    img.save(save_path)
    return save_path