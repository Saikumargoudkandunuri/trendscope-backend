import os
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# ================== PATHS ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "images", "output")
FONT_REGULAR_PATH = os.path.join(BASE_DIR, "fonts", "arial.ttf")
FONT_BOLD_PATH = os.path.join(BASE_DIR, "fonts", "arialbd.ttf")

os.makedirs(OUTPUT_DIR, exist_ok=True)
W, H = 1080, 1080

def get_font(font_size: int, bold: bool = False):
    """Load font or fallback to default"""
    path = FONT_BOLD_PATH if bold else FONT_REGULAR_PATH
    try:
        return ImageFont.truetype(path, font_size)
    except:
        return ImageFont.load_default()

def generate_news_image(headline, info_text, image_url, output_name):
    """
    Generates 1080x1080 news card image and returns saved image path.
    Fixes: NameError: size / is_bold not defined
    """

    import os
    import requests
    from io import BytesIO
    from PIL import Image, ImageDraw, ImageFont

    # --- CONFIG ---
    W, H = 1080, 1080
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = os.path.join(BASE_DIR, "images", "output")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # If you don’t have fonts folder, it will fallback to default font automatically
    FONT_REGULAR_PATH = os.path.join(BASE_DIR, "fonts", "arial.ttf")
    FONT_BOLD_PATH = os.path.join(BASE_DIR, "fonts", "arialbd.ttf")

    def get_font(font_size: int, bold: bool = False):
        """Load font from file or fallback to default font."""
        path = FONT_BOLD_PATH if bold else FONT_REGULAR_PATH
        try:
            return ImageFont.truetype(path, font_size)
        except Exception:
            return ImageFont.load_default()

    # ---- Create base canvas ----
    img = Image.new("RGB", (W, H), (15, 17, 26))
    draw = ImageDraw.Draw(img)

    # ---- 1) Load main image ----
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(image_url, headers=headers, timeout=12)
        r.raise_for_status()

        photo = Image.open(BytesIO(r.content)).convert("RGB")
        photo = photo.resize((W, 620), Image.Resampling.LANCZOS)
        img.paste(photo, (0, 0))
    except Exception:
        # fallback if image fails
        draw.rectangle([0, 0, W, 620], fill=(30, 35, 50))

    # ---- 2) Bottom overlay bar ----
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    bar_h = 430
    odraw.rectangle([0, H - bar_h, W, H], fill=(13, 56, 74, 245))
    img.paste(overlay, (0, 0), overlay)

    # ---- 3) Text helpers ----
    def wrap_text_to_width(text, font, max_width):
        words = text.split()
        lines = []
        current = []
        for word in words:
            test = " ".join(current + [word])
            w = draw.textbbox((0, 0), test, font=font)[2]
            if w <= max_width:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))
        return lines

    def draw_text_auto(text, x, y, max_width, max_height, start_size, bold=True, line_gap=12):
        """
        Auto-scales font down until text fits inside max_height.
        Returns final y position after drawing.
        """
        size = start_size
        while size >= 18:
            font = get_font(size, bold)
            lines = wrap_text_to_width(text, font, max_width)
            total_h = len(lines) * (size + line_gap)

            if total_h <= max_height:
                # draw
                for line in lines:
                    draw.text((x, y), line, fill=(255, 255, 255), font=font)
                    y += (size + line_gap)
                return y

            size -= 2

        # fallback draw at smallest font
        font = get_font(18, bold)
        lines = wrap_text_to_width(text, font, max_width)
        for line in lines[:6]:
            draw.text((x, y), line, fill=(255, 255, 255), font=font)
            y += 30
        return y

    # ---- 4) Draw headline and info ----
    headline = (headline or "").strip().upper()
    info_text = (info_text or "").strip().upper()

    y1 = draw_text_auto(
        headline,
        x=50,
        y=H - 400,
        max_width=980,
        max_height=140,
        start_size=68,
        bold=True
    )

    draw_text_auto(
        info_text,
        x=50,
        y=y1 + 10,
        max_width=980,
        max_height=240,
        start_size=34,
        bold=True
    )

    # ---- 5) Footer ----
    footer = "FOLLOW @GLOBALKNOWLEDGE | INDIA"
    draw.text((50, 1030), footer, fill=(0, 210, 255), font=get_font(24, True))

    # ---- Save ----
    save_path = os.path.join(OUTPUT_DIR, output_name)
    img.save(save_path)
    return save_path
