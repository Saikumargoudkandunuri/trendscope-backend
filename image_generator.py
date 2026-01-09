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

def generate_news_image(full_info_text, image_url, output_name):
    # 1. Create Base
    img = Image.new("RGB", (W, H), (0, 0, 0))
    
    # 2. Background Image (Full Screen Center Crop)
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(image_url, headers=headers, timeout=10)
        photo = Image.open(BytesIO(r.content)).convert("RGB")
        
        # Center Crop logic
        img_aspect = photo.width / photo.height
        if img_aspect > 1:
            new_width = int(photo.height)
            left = (photo.width - new_width) / 2
            photo = photo.crop((left, 0, left + new_width, photo.height))
        else:
            new_height = int(photo.width)
            top = (photo.height - new_height) / 2
            photo = photo.crop((0, top, photo.width, top + new_height))
        
        photo = photo.resize((1080, 1080), Image.Resampling.LANCZOS)
        img.paste(photo, (0, 0))
    except:
        pass

    # 3. Wirally Teal Bar (Translucent)
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    # The dark teal bar at the bottom
    bar_height = 380 
    draw_ov.rectangle([0, H - bar_height, W, H], fill=(13, 56, 74, 240)) 
    img.paste(overlay, (0, 0), overlay)
    
    # 4. Draw the Full News Info (All Caps, Bold)
    draw = ImageDraw.Draw(img)
    text = full_info_text.upper() # Wirally always uses UpperCase
    
    def draw_wirally_text(text, start_y, max_h, initial_size):
        size = initial_size
        while size > 24:
            font = get_font(size)
            lines, current_line = [], []
            for word in text.split():
                test_line = ' '.join(current_line + [word])
                if draw.textbbox((0, 0), test_line, font=font)[2] <= 1000:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            lines.append(' '.join(current_line))
            
            if len(lines) * (size + 15) <= max_h:
                y = start_y
                for line in lines:
                    # White text like reference
                    draw.text((40, y), line, fill=(255, 255, 255), font=font)
                    y += (size + 15)
                return y
            size -= 2
        return start_y

    # Draw the main info inside the teal bar
    draw_wirally_text(text, H - 340, 300, 52)

    # 5. Save
    save_path = os.path.join(OUTPUT_DIR, output_name)
    img.save(save_path)
    return save_path