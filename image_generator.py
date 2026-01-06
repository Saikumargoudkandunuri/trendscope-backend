import os
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# ================== PATHS ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "images", "output")
LOGO_PATH = os.path.join(BASE_DIR, "assets", "channels4_profile (1) (1).png")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================== THEME COLORS ==================
BG_COLOR = (15, 17, 26)       # Deep Dark Navy
CARD_COLOR = (25, 28, 41)     # Slightly lighter navy for contrast
TEXT_COLOR = (255, 255, 255)  # Pure White
ACCENT_COLOR = (0, 210, 255)  # Cyan Blue Accent
GRAY_TEXT = (160, 165, 180)   # Soft Gray for description
FALLBACK_IMAGE = "https://images.unsplash.com/photo-1504711434969-e33886168f5c"

W, H = 1080, 1080

# ================== HELPERS ==================
def get_font(size, bold=False):
    try:
        # On Windows: 'arialbd.ttf' for bold, 'arial.ttf' for regular
        # On Linux/Render: You might need to provide a .ttf file in your assets
        font_name = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(font_name, size)
    except:
        return ImageFont.load_default()

def draw_wrapped_text(draw, text, x, y, max_w, font_obj, color, spacing=12):
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        w = draw.textbbox((0, 0), test_line, font=font_obj)[2]
        if w <= max_w:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))

    for line in lines:
        draw.text((x, y), line, fill=color, font=font_obj)
        y += font_obj.size + spacing
    return y

# ================== MAIN GENERATOR ==================
def generate_news_image(headline, description, image_url, output_name="post.png"):
    # 1. Create Canvas
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # 2. Draw Top Tag (e.g., TRENDING NEWS)
    tag_text = "TRENDSCOPE | INDIA"
    tag_font = get_font(30, bold=True)
    tw = draw.textbbox((0, 0), tag_text, font=tag_font)[2]
    # Accent line next to tag
    draw.rectangle([60, 60, 65, 95], fill=ACCENT_COLOR)
    draw.text((80, 60), tag_text, fill=ACCENT_COLOR, font=tag_font)

    # 3. Logo (Top Right)
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            logo = logo.resize((100, 100))
            img.paste(logo, (920, 45), logo)
        except: pass

    # 4. Main Image Frame
    IMG_X, IMG_Y = 60, 140
    IMG_W, IMG_H = 960, 520
    
    # Try fetching news image
    main_photo = None
    for url in [image_url, FALLBACK_IMAGE]:
        try:
            resp = requests.get(url, timeout=5)
            main_photo = Image.open(BytesIO(resp.content)).convert("RGB")
            break
        except: continue

    if main_photo:
        # Resize and Crop to fit 960x520
        aspect = main_photo.width / main_photo.height
        target_aspect = IMG_W / IMG_H
        if aspect > target_aspect: # too wide
            new_width = int(target_aspect * main_photo.height)
            main_photo = main_photo.crop(((main_photo.width - new_width)//2, 0, (main_photo.width + new_width)//2, main_photo.height))
        else: # too tall
            new_height = int(main_photo.width / target_aspect)
            main_photo = main_photo.crop((0, (main_photo.height - new_height)//2, main_photo.width, (main_photo.height + new_height)//2))
        
        main_photo = main_photo.resize((IMG_W, IMG_H))
        
        # Rounded Corners mask
        mask = Image.new("L", (IMG_W, IMG_H), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, IMG_W, IMG_H], 20, fill=255)
        img.paste(main_photo, (IMG_X, IMG_Y), mask)

    # 5. Headline
    head_font = get_font(65, bold=True)
    y_cursor = IMG_Y + IMG_H + 40
    y_cursor = draw_wrapped_text(draw, headline.upper(), 60, y_cursor, 960, head_font, TEXT_COLOR, spacing=15)

    # 6. Description (Max 3-4 lines)
    y_cursor += 10
    desc_font = get_font(36)
    clean_desc = description[:200] + "..." if len(description) > 200 else description
    draw_wrapped_text(draw, clean_desc, 60, y_cursor, 960, desc_font, GRAY_TEXT, spacing=10)

    # 7. Sleek Minimalist Footer
    footer_y = H - 100
    draw.line([60, footer_y, 1020, footer_y], fill=(50, 50, 60), width=2)
    
    footer_font = get_font(28, bold=True)
    footer_text = "FOLLOW @TRENDSCOPE  |  GET THE FULL STORY"
    draw.text((60, footer_y + 35), footer_text, fill=ACCENT_COLOR, font=footer_font)

    # 8. Save
    path = os.path.join(OUTPUT_DIR, output_name)
    img.save(path)
    return path