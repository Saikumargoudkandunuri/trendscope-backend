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

def generate_news_image(headline, image_url, output_name):
    """
    Generates a high-quality RVCJ style news image.
    Features: Smart Cropping, Auto-Text Resizing, Dark Theme.
    """
    # 1. Create Base Canvas
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # 2. Top Header Branding
    draw.rectangle([60, 60, 65, 95], fill=ACCENT_COLOR) # Cyan side-bar
    draw.text((85, 60), "TRENDSCOPE | LIVE", fill=ACCENT_COLOR, font=get_font(32, True))

    # 3. Smart Image Handling (Fixed Box: 960x500)
    image_pasted = False
    if image_url and image_url.startswith("http"):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(image_url, headers=headers, timeout=10)
            if r.status_code == 200:
                photo = Image.open(BytesIO(r.content)).convert("RGB")
                
                # --- PROPORTIONAL SMART CROP ---
                target_w, target_h = 960, 500
                target_aspect = target_w / target_h
                img_aspect = photo.width / photo.height

                if img_aspect > target_aspect:
                    # Image is too wide - crop the sides
                    new_width = int(target_aspect * photo.height)
                    left = (photo.width - new_width) / 2
                    photo = photo.crop((left, 0, left + new_width, photo.height))
                else:
                    # Image is too tall - crop the top/bottom
                    new_height = int(photo.width / target_aspect)
                    top = (photo.height - new_height) / 2
                    photo = photo.crop((0, top, photo.width, top + new_height))
                
                photo = photo.resize((target_w, target_h), Image.Resampling.LANCZOS)
                
                # Rounded corners for the image card
                mask = Image.new("L", (target_w, target_h), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.rounded_rectangle([0, 0, target_w, target_h], 25, fill=255)
                
                img.paste(photo, (60, 140), mask)
                image_pasted = True
        except Exception as e:
            print(f"Image Load Error: {e}")

    # Fallback if image download fails
    if not image_pasted:
        draw.rounded_rectangle([60, 140, 1020, 640], 25, fill=(30, 35, 50))
        draw.text((400, 370), "BREAKING NEWS", fill=GRAY_TEXT, font=get_font(30))

    # 4. SMART TEXT LOGIC (Auto-shrinks to fit)
    def draw_rvcj_text(text, start_y, max_h, initial_size):
        size = initial_size
        while size > 22: # Minimum font size
            font = get_font(size, True)
            words = text.split()
            lines, current_line = [], []
            
            # Wrap text manually to calculate height
            for word in words:
                test_line = ' '.join(current_line + [word])
                if draw.textbbox((0, 0), test_line, font=font)[2] <= 960:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            lines.append(' '.join(current_line))
            
            # Check if total height fits the box
            line_spacing = 15
            total_h = len(lines) * (size + line_spacing)
            
            if total_h <= max_h:
                # Text fits! Now draw it
                y = start_y
                for line in lines:
                    draw.text((60, y), line, fill=TEXT_COLOR, font=font)
                    y += (size + line_spacing)
                return y
            
            size -= 5 # Shrink font and try again
        return start_y

    # Draw Headline (starts at 680, max height 300px)
    draw_rvcj_text(headline.upper(), 680, 300, 75)

    # 5. Bottom Branding Footer
    draw.line([60, 1010, 1020, 1010], fill=(50, 55, 75), width=2)
    footer_font = get_font(26, True)
    draw.text((60, 1025), "FOLLOW @TRENDSCOPE | INDIA", fill=ACCENT_COLOR, font=footer_font)

    # 6. Save with Unique Name
    save_path = os.path.join(OUTPUT_DIR, output_name)
    img.save(save_path)
    print(f"✅ Image Generated: {output_name}")
    return save_path