"""Logo + channel art for ບອກຕໍ່ຄວາມຮູ້."""
import math, random
from PIL import Image, ImageDraw, ImageFilter
from common import (font, draw_line, line_width, icon, CAT_COLORS, CAT_ORDER, CHANNEL,
                    BG, CREAM, AMBER, CYAN, MUTED)

def space_bg(w, h, seed=7, glow=True):
    img = Image.new("RGBA", (w, h), BG + (255,))
    if glow:
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        gd.ellipse((-w * 0.25, h * 0.45, w * 0.55, h * 1.4), fill=(60, 30, 90, 90))
        gd.ellipse((w * 0.5, -h * 0.4, w * 1.3, h * 0.6), fill=(20, 60, 110, 80))
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(min(w, h) * 0.12)))
    d = ImageDraw.Draw(img, "RGBA")
    r = random.Random(seed)
    for _ in range(int(w * h / 5000)):
        x, y, s = r.uniform(0, w), r.uniform(0, h), r.uniform(0.6, 2.2) * max(1, w / 1600)
        d.ellipse((x - s, y - s, x + s, y + s), fill=(255, 255, 255, r.randint(90, 230)))
    return img.convert("RGB")  # RGB base so RGBA drawing blends

def wordmark(d, cx, y_top, size):
    """Two-tone channel name: ບອກຕໍ່ (cream) + ຄວາມຮູ້ (amber), single line."""
    a, b = "ບອກຕໍ່", "ຄວາມຮູ້"
    wa, wb = line_width(a, size), line_width(b, size)
    gap = size * 0.18
    x = cx - (wa + gap + wb) / 2
    base = y_top + size
    draw_line(d, x, base, a, size, CREAM, align="left")
    draw_line(d, x + wa + gap, base, b, size, AMBER, align="left")

def icon_row(d, cx, cy, s, spacing, chips=True):
    n = len(CAT_ORDER)
    for i, k in enumerate(CAT_ORDER):
        x = cx + (i - (n - 1) / 2) * spacing
        col = CAT_COLORS[k]
        if chips:
            d.ellipse((x - s * 1.7, cy - s * 1.7, x + s * 1.7, cy + s * 1.7), fill=col + (40,), outline=col + (200,), width=max(2, int(s * 0.12)))
        icon(d, k, x, cy, s, col)

# ---------- profile logo (circle-safe, 1024) ----------
def logo(path, size=1024):
    img = space_bg(size, size, seed=3)
    d = ImageDraw.Draw(img, "RGBA")
    c = size / 2
    # ring of five category icons on the upper arc
    R = size * 0.335
    for i, k in enumerate(CAT_ORDER):
        a = math.radians(-162 + i * 36)  # -162..-18 deg
        x, y = c + R * math.cos(a), c + 30 + R * math.sin(a)
        col = CAT_COLORS[k]
        rr = size * 0.062
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=col + (48,), outline=col + (230,), width=5)
        icon(d, k, x, y, size * 0.034, col)
    # name: two lines, big enough to read at 100px
    draw_line(d, c, c + size * 0.11, "ບອກຕໍ່", int(size * 0.17), CREAM)
    draw_line(d, c, c + size * 0.31, "ຄວາມຮູ້", int(size * 0.15), AMBER)
    img.convert("RGB").save(path)
    # round preview to check circle crop
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size, size), fill=255)
    prev = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    prev.paste(img, (0, 0), m)
    return prev

# ---------- YouTube banner 2560x1440, safe area 1546x423 in the centre ----------
def yt_banner(path):
    w, h = 2560, 1440
    img = space_bg(w, h, seed=5)
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = w / 2, h / 2
    wordmark(d, cx, cy - 165, 112)
    draw_line(d, cx, cy + 22, "ອາວະກາດ • ສິລະປະ • ເຕັກໂນໂລຢີ • ວິສະວະກຳ • ຟີຊິກ", 44, MUTED, 400)
    icon_row(d, cx, cy + 92, 21, 130)
    draw_line(d, cx, cy + 186, "ເກັດຄວາມຮູ້ໃໝ່ ວັນລະ 1 ເລື່ອງ", 30, CYAN, 400)
    img.convert("RGB").save(path)
    guide = img.copy()
    gd = ImageDraw.Draw(guide)
    gd.rectangle((cx - 773, cy - 211.5, cx + 773, cy + 211.5), outline=(255, 80, 80, 255), width=4)  # all devices
    gd.rectangle(((w - 1855) / 2, cy - 211.5, (w + 1855) / 2, cy + 211.5), outline=(255, 200, 80, 255), width=2)
    return guide

# ---------- Facebook cover 1640x924, key content kept in centre 1200x460 ----------
def fb_cover(path):
    w, h = 1640, 924
    img = space_bg(w, h, seed=9)
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = w / 2, h / 2 + 10
    wordmark(d, cx, cy - 175, 112)
    draw_line(d, cx, cy + 22, "ອາວະກາດ • ສິລະປະ • ເຕັກໂນໂລຢີ • ວິສະວະກຳ • ຟີຊິກ", 40, MUTED, 400)
    icon_row(d, cx, cy + 95, 21, 120)
    draw_line(d, cx, cy + 186, "ເກັດຄວາມຮູ້ໃໝ່ ວັນລະ 1 ເລື່ອງ", 30, CYAN, 400)
    img.convert("RGB").save(path)

if __name__ == "__main__":
    import os
    os.makedirs("brand", exist_ok=True)
    prev = logo("brand/logo_1024.png")
    Image.open("brand/logo_1024.png").resize((800, 800), Image.LANCZOS).save("brand/logo_800.png")
    guide = yt_banner("brand/youtube_banner_2560x1440.png")
    fb_cover("brand/facebook_cover_1640x924.png")
    # review sheet
    sheet = Image.new("RGBA", (2560 // 2 + 520, 760), (40, 40, 40, 255))
    sheet.alpha_composite(prev.resize((480, 480)), (20, 20))
    sheet.alpha_composite(prev.resize((96, 96)), (200, 560))
    sheet.paste(guide.resize((1280, 720)).convert("RGBA"), (520, 20))
    sheet.convert("RGB").save("brand/_review.png")
    Image.open("brand/facebook_cover_1640x924.png").resize((820, 462)).save("brand/_review_fb.png")
    print("ok")
