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

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================== THEME ==================
BG_COLOR = (15, 17, 26)       # Deep Dark Navy
TEXT_COLOR = (255, 255, 255)  # Pure White
ACCENT_COLOR = (0, 210, 255)  # Cyan Blue
GRAY_TEXT = (180, 185, 200)   # Soft Gray
W, H = 1080, 1080

def get_font(size, bold=False):
    path = FONT_BOLD_PATH if bold else FONT_PATH
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def generate_news_image(headline, description, image_url, output_name="post.png"):
    # 1. Create Canvas
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # 2. Header Branding
    draw.rectangle([60, 60, 65, 95], fill=ACCENT_COLOR)
    draw.text((85, 60), "TRENDSCOPE | LIVE", fill=ACCENT_COLOR, font=get_font(32, True))

    # 3. Download & Paste News Image (Fixed Size to protect text area)
    image_pasted = False
    IMG_BOX = (60, 140, 1020, 640) # Fixed area for the photo (960x500)
    
    if image_url and image_url.startswith("http"):
        try:
            # Use headers to avoid being blocked by news sites
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(image_url, headers=headers, timeout=10)
            if r.status_code == 200:
                photo = Image.open(BytesIO(r.content)).convert("RGB")
                
                # Proportional Crop & Resize to fit 960x500
                aspect_ratio = 960 / 500
                img_aspect = photo.width / photo.height
                if img_aspect > aspect_ratio:
                    # Too wide, crop sides
                    new_width = int(aspect_ratio * photo.height)
                    left = (photo.width - new_width) / 2
                    photo = photo.crop((left, 0, left + new_width, photo.height))
                else:
                    # Too tall, crop top/bottom
                    new_height = int(photo.width / aspect_ratio)
                    top = (photo.height - new_height) / 2
                    photo = photo.crop((0, top, photo.width, top + new_height))
                
                photo = photo.resize((960, 500), Image.Resampling.LANCZOS)
                
                # Mask for rounded corners
                mask = Image.new("L", (960, 500), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.rounded_rectangle([0, 0, 960, 500], 25, fill=255)
                
                img.paste(photo, (60, 140), mask)
                image_pasted = True
        except Exception as e:
            print(f"Image Load Failed: {e}")

    if not image_pasted:
        # Fallback background if image fails
        draw.rounded_rectangle([60, 140, 1020, 640], 25, fill=(30, 35, 50))
        draw.text((400, 370), "BREAKING NEWS", fill=GRAY_TEXT, font=get_font(30))

    # 4. SMART TEXT LOGIC (Optimized to prevent cutting)
    def draw_contained_text(text, start_y, max_height, initial_size, is_bold, color):
        size = initial_size
        while size > 18:  # Minimum legible size
            font = get_font(size, is_bold)
            words = text.split()
            lines, current_line = [], []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                # Max width is 960px
                if draw.textbbox((0, 0), test_line, font=font)[2] <= 960:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            lines.append(' '.join(current_line))
            
            # Check total height including spacing
            line_height = size + 12
            total_h = len(lines) * line_height
            
            if total_h <= max_height:
                y = start_y
                for line in lines:
                    draw.text((60, y), line, fill=color, font=font)
                    y += line_height
                return y # Return the final Y position after drawing
            
            size -= 2 # Shrink and retry
        return start_y

    # --- Headline Drawing ---
    # Max height: 210px (Safe zone 680 to 890)
    headline_text = headline.upper()
    next_y = draw_contained_text(headline_text, 680, 210, 68, True, TEXT_COLOR)

    # --- Description Drawing ---
    # Max height: 110px (Safe zone next_y to 1000)
    # This uses your "No Jargon/Emotional" text from AI
    draw_contained_text(description, next_y + 15, 110, 34, False, GRAY_TEXT)

    # 5. Footer (Locked at the bottom)
    draw.line([60, 1010, 1020, 1010], fill=(50, 55, 75), width=2)
    footer_text = "FOLLOW @TRENDSCOPE FOR INSTANT UPDATES"
    draw.text((60, 1025), footer_text, fill=ACCENT_COLOR, font=get_font(26, True))

    # 6. Save
    save_path = os.path.join(OUTPUT_DIR, output_name)
    img.save(save_path)
    return save_path