# ================== IMPORTS ==================
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import os

# ================== PATHS ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "images", "output")
LOGO_PATH = os.path.join(BASE_DIR, "assets", "channels4_profile (1) (1).png")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================== CONSTANTS ==================
FALLBACK_IMAGE = "https://images.unsplash.com/photo-1504711434969-e33886168f5c"

W, H = 1080, 1080
BG = (245, 246, 250)
WHITE = (255, 255, 255)
BLACK = (17, 24, 39)
GRAY = (55, 65, 81)
RED = (239, 68, 68)
BLUE = (29, 78, 216)

# ================== FONT ==================
def font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()

# ================== HELPERS ==================
def rounded(draw, box, r, fill):
    draw.rounded_rectangle(box, r, fill=fill)

def draw_wrapped(draw, text, x, y, max_w, font_obj, color, gap):
    words = text.split()
    line = ""

    for word in words:
        test = f"{line} {word}" if line else word
        w = draw.textbbox((0, 0), test, font=font_obj)[2]

        if w <= max_w:
            line = test
        else:
            draw.text((x, y), line, fill=color, font=font_obj)
            y += font_obj.size + gap
            line = word

    if line:
        draw.text((x, y), line, fill=color, font=font_obj)
        y += font_obj.size + gap

    return y

# ---------- HEADLINE FITTER (MAX 4 LINES) ----------
def fit_headline_max_lines(draw, text, max_width, max_lines, start_size=72, min_size=48):
    size = start_size

    while size >= min_size:
        f = font(size)
        words = text.split()
        lines = []
        line = ""

        for word in words:
            test = f"{line} {word}" if line else word
            w = draw.textbbox((0, 0), test, font=f)[2]

            if w <= max_width:
                line = test
            else:
                lines.append(line)
                line = word

        if line:
            lines.append(line)

        if len(lines) <= max_lines:
            return f, lines

        size -= 2

    return font(min_size), lines[:max_lines]

# ================== MAIN ==================
def generate_news_image(headline, description, image_url, output_name="post.png"):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    tag_font = font(28)
    body_font = font(34)
    footer_font = font(30)

    # ---------- TAG ----------
    tag_text = "GLOBAL KNOWLEDGE"
    tw, th = draw.textbbox((0, 0), tag_text, font=tag_font)[2:]
    rounded(draw, (60, 40, 60 + tw + 40, 40 + th + 20), 14, RED)
    draw.text((80, 50), tag_text, fill=WHITE, font=tag_font)

    # ---------- LOGO ----------
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert("RGBA").resize((120, 120))
        img.paste(logo, (900, 40), logo)

    # ---------- HEADLINE (MAX 4 LINES + AUTO SHRINK) ----------
    max_width = 960
    max_lines = 4

    head_font, headline_lines = fit_headline_max_lines(
        draw,
        headline,
        max_width,
        max_lines
    )

    y = 150
    for line in headline_lines:
        draw.text((60, y), line, fill=BLACK, font=head_font)
        y += head_font.size + 10

    y += 20

    # ---------- IMAGE (AUTO POSITIONED) ----------
    IMAGE_Y = y
    IMAGE_W, IMAGE_H = 960, 420

    image_done = False
    for url in [image_url, FALLBACK_IMAGE]:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                photo = Image.open(BytesIO(r.content)).convert("RGB")
                photo = photo.resize((IMAGE_W, IMAGE_H))

                mask = Image.new("L", (IMAGE_W, IMAGE_H), 0)
                ImageDraw.Draw(mask).rounded_rectangle(
                    (0, 0, IMAGE_W, IMAGE_H), 26, fill=255
                )

                img.paste(photo, (60, IMAGE_Y), mask)
                image_done = True
                break
        except:
            continue

    if not image_done:
        draw.rectangle(
            (60, IMAGE_Y, 60 + IMAGE_W, IMAGE_Y + IMAGE_H),
            outline=GRAY,
            width=3
        )
        draw.text(
            (420, IMAGE_Y + 190),
            "IMAGE NOT AVAILABLE",
            fill=GRAY,
            font=font(28)
        )

    # ---------- DESCRIPTION ----------
    y = IMAGE_Y + IMAGE_H + 30
    description = description[:260] + "…" if len(description) > 260 else description
    y = draw_wrapped(draw, description, 60, y, 960, body_font, GRAY, 8)

    # ---------- FOOTER ----------
    footer_h = 90
    draw.rectangle((0, H - footer_h, W, H), fill=BLUE)
    draw.text(
        (60, H - 60),
        "Follow @globalknowledge  |  Instagram • YouTube",
        fill=WHITE,
        font=footer_font
    )

    # ---------- SAVE ----------
    path = os.path.join(OUTPUT_DIR, output_name)
    img.save(path)
    return path
