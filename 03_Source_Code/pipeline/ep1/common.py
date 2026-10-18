"""Shared look for the ຮູ້ບໍ່? series: background, fonts, text, badge, footer, encoder.
Every episode uses the same canvas, colours and text positions as EP.1."""
import math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FONTS = "/root/fonts/"
BG = (7, 11, 26)
CREAM = (255, 244, 222)
AMBER = (255, 181, 71)
CYAN = (90, 209, 255)
MUTED = (150, 160, 190)
RED = (255, 92, 92)
GOLD = (214, 168, 74)

HOOK_Y, HOOK_SIZE = 380, 74        # hook text block, same on every episode
BOTTOM_Y = 1560                    # lower caption line
CTA_START = None

_fc = {}
def font(kind, size, w=700):
    key = (kind, size, w)
    if key not in _fc:
        path = f"{FONTS}lao{700 if w >= 700 else 400}.ttf" if kind == "lao" else f"{FONTS}lat{w}.ttf"
        _fc[key] = ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    return _fc[key]

def is_lao(ch): return 0x0E80 <= ord(ch) <= 0x0EFF

def runs(text):
    out, cur, kind = [], "", None
    for ch in text:
        k = "lao" if is_lao(ch) else ("same" if ch == " " else "lat")
        if k == "same":
            k = kind or "lat"
        if kind is None or k == kind:
            cur += ch; kind = k
        else:
            out.append((kind, cur)); cur, kind = ch, k
    if cur:
        out.append((kind, cur))
    return out

def line_width(text, size, w=700):
    return sum(font(k, size, w).getlength(t) for k, t in runs(text))

def draw_line(d, cx, base_y, text, size, fill, w=700, align="center", stroke=0, stroke_fill=(0, 0, 0)):
    tw = line_width(text, size, w)
    x = cx - tw / 2 if align == "center" else (cx - tw if align == "right" else cx)
    for k, t in runs(text):
        f = font(k, size, w)
        d.text((x, base_y), t, font=f, fill=fill, anchor="ls", stroke_width=stroke, stroke_fill=stroke_fill)
        x += f.getlength(t)
    return tw

def with_alpha(layer, a):
    if a < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
    return layer

def draw_block(img, cx, top, lines, size, fill=CREAM, w=700, gap=1.45, alpha=1.0, shadow=True):
    if alpha <= 0:
        return top
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = top + size
    for ln in lines:
        txt, col = (ln, fill) if isinstance(ln, str) else ln
        if shadow:
            draw_line(d, cx, y, txt, size, (0, 0, 0, 160), w, stroke=max(2, size // 14), stroke_fill=(0, 0, 0, 160))
        draw_line(d, cx, y, txt, size, col, w)
        y += int(size * gap)
    img.alpha_composite(with_alpha(layer, alpha))
    return y

def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def prog(t, a, b): return clamp((t - a) / (b - a))
def ease(x): return 1 - (1 - x) ** 3
def ease_io(x): return x * x * (3 - 2 * x)
def fade(t, a, b, fin=0.35, fout=0.35): return clamp(min((t - a) / fin, (b - t) / fout))
def lerp(a, b, x): return a + (b - a) * x

# ---------- background ----------
_rng = np.random.default_rng(7)
STARS = [(_rng.uniform(0, W), _rng.uniform(0, H), _rng.uniform(0.6, 2.4), _rng.uniform(0, 6.28), _rng.uniform(0.5, 2))
         for _ in range(320)]
def _starfield(t):
    img = Image.new("RGBA", (W, H), BG + (255,))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-300, 1100, 900, 2300), fill=(60, 30, 90, 70))
    gd.ellipse((500, -200, 1500, 800), fill=(20, 60, 110, 60))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(160)))
    d = ImageDraw.Draw(img)
    for x, y, r, ph, sp in STARS:
        a = int(140 + 110 * math.sin(t * sp + ph))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, a))
    return img
_cache = {}
def bg(t):
    k = int(t * 10)
    if k not in _cache:
        _cache.clear(); _cache[k] = _starfield(k / 10)
    return _cache[k].copy()

def glow_spot(img, cx, cy, r, color, alpha=90, blur=None):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse((cx - r, cy - r, cx + r, cy + r), fill=color + (alpha,))
    img.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur or r * 0.35)))

def arrow(d, p0, p1, color, width=8, head=26):
    d.line([p0, p1], fill=color, width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    tip = (p1[0] + math.cos(ang) * head * 0.5, p1[1] + math.sin(ang) * head * 0.5)
    l = (p1[0] + math.cos(ang + 2.5) * head, p1[1] + math.sin(ang + 2.5) * head)
    r = (p1[0] + math.cos(ang - 2.5) * head, p1[1] + math.sin(ang - 2.5) * head)
    d.polygon([tip, l, r], fill=color)

def arrow_arc(d, cx, cy, r, a0, a1, color, width=10, head=34):
    pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in np.linspace(a0, a1, 40)]
    d.line(pts, fill=color, width=width, joint="curve")
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    tip = (x2 + math.cos(ang) * head * 0.6, y2 + math.sin(ang) * head * 0.6)
    l = (x2 + math.cos(ang + 2.5) * head, y2 + math.sin(ang + 2.5) * head)
    rr = (x2 + math.cos(ang - 2.5) * head, y2 + math.sin(ang - 2.5) * head)
    d.polygon([tip, l, rr], fill=color)

# ---------- chrome shared by every episode ----------
def badge(img, ep, cat):
    d = ImageDraw.Draw(img)
    x, y = 70, 120
    d.rounded_rectangle((x, y, x + 300, y + 74), 37, fill=AMBER + (255,))
    draw_line(d, x + 150, y + 51, f"ຮູ້ບໍ່? EP.{ep}", 38, BG, 700)
    draw_line(d, x + 320, y + 50, cat, 32, CAT_COLORS.get(cat, MUTED), 700, align="left")

def footer(img, credit):
    d = ImageDraw.Draw(img)
    draw_line(d, W / 2, 1745, f"ຂໍ້ມູນ: {credit}  •  ພາບປະກອບ, ບໍ່ແມ່ນມາດຕາສ່ວນຈິງ", 28, MUTED, 400)

def run(ep, cat, credit, dur, scene, hook_lines, out=None):
    """scene(img, t) draws the episode; hook text and chrome are added here.
    The hook is shown 0–3.4 s and fades back in over the last 1.4 s so the loop is seamless."""
    args = sys.argv[1:]
    out = args[0] if args else out

    def frame(t):
        img = bg(t)
        scene(img, t)
        if t < 3.6:
            draw_block(img, W / 2, HOOK_Y, hook_lines, HOOK_SIZE, alpha=fade(t, -1, 3.6, 0.1, 0.4))
        if t > dur - 1.4:
            draw_block(img, W / 2, HOOK_Y, hook_lines, HOOK_SIZE, alpha=prog(t, dur - 1.4, dur - 0.4))
        badge(img, ep, cat)
        brand_mark(img, cat)
        footer(img, credit)
        return img.convert("RGB")

    if len(args) > 1:  # stills: comma separated seconds
        for s in args[1].split(","):
            frame(float(s)).save(f"still_ep{ep}_{s}.png")
        return
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    n = int(dur * FPS)
    for i in range(n):
        ff.stdin.write(frame(i / FPS).tobytes())
    ff.stdin.close(); ff.wait()
    print("done", out)

# ---------- brand: ບອກຕໍ່ຄວາມຮູ້ ----------
CHANNEL = "ບອກຕໍ່ຄວາມຮູ້"
SHARE_CTA = "ຖ້າຮູ້ແລ້ວ ຢ່າລືມ ບອກຕໍ່ ໃຫ້ໝູ່ເດີ້!"
CAT_COLORS = {"ອາວະກາດ": (176, 132, 255), "ສິລະປະ": (255, 122, 182), "ເຕັກໂນໂລຢີ": CYAN,
              "ວິສະວະກຳ": (255, 160, 70), "ຟີຊິກ": (110, 225, 150)}
CAT_ORDER = ["ອາວະກາດ", "ສິລະປະ", "ເຕັກໂນໂລຢີ", "ວິສະວະກຳ", "ຟີຊິກ"]

def icon(d, kind, cx, cy, s, col):
    """Simple line/flat icons, s = half-size in px."""
    c = col + (255,) if len(col) == 3 else col
    lw = max(2, int(s * 0.14))
    if kind == "ອາວະກາດ":      # star
        pts = []
        for k in range(10):
            r = s if k % 2 == 0 else s * 0.42
            a = -math.pi / 2 + k * math.pi / 5
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(pts, fill=c)
    elif kind == "ສິລະປະ":     # brush
        d.line((cx + s * 0.85, cy - s * 0.85, cx + s * 0.05, cy - s * 0.05), fill=c, width=lw + 3)
        d.polygon([(cx - s * 0.05, cy - s * 0.25), (cx + s * 0.25, cy + s * 0.05), (cx - s * 0.2, cy + s * 0.55),
                   (cx - s * 0.95, cy + s * 0.95), (cx - s * 0.55, cy + s * 0.2)], fill=c)
    elif kind == "ເຕັກໂນໂລຢີ":  # chip
        b = s * 0.6
        d.rounded_rectangle((cx - b, cy - b, cx + b, cy + b), s * 0.12, outline=c, width=lw)
        d.rectangle((cx - b * 0.45, cy - b * 0.45, cx + b * 0.45, cy + b * 0.45), fill=c)
        for k in (-0.5, 0, 0.5):
            o = k * b * 1.2
            d.line((cx + o, cy - b, cx + o, cy - s), fill=c, width=lw)
            d.line((cx + o, cy + b, cx + o, cy + s), fill=c, width=lw)
            d.line((cx - b, cy + o, cx - s, cy + o), fill=c, width=lw)
            d.line((cx + b, cy + o, cx + s, cy + o), fill=c, width=lw)
    elif kind == "ວິສະວະກຳ":    # bridge
        d.line((cx - s, cy + s * 0.25, cx + s, cy + s * 0.25), fill=c, width=lw + 2)
        d.arc((cx - s * 0.95, cy - s * 0.75, cx + s * 0.95, cy + s * 1.2), 180, 360, fill=c, width=lw)
        for k in (-0.6, -0.2, 0.2, 0.6):
            x = cx + k * s
            ytop = cy + s * 0.22 - math.sqrt(max(0, 1 - (k / 0.95) ** 2)) * s * 0.97
            d.line((x, ytop, x, cy + s * 0.25), fill=c, width=max(2, lw // 2))
        d.line((cx - s * 0.8, cy + s * 0.25, cx - s * 0.8, cy + s * 0.9), fill=c, width=lw)
        d.line((cx + s * 0.8, cy + s * 0.25, cx + s * 0.8, cy + s * 0.9), fill=c, width=lw)
    elif kind == "ຟີຊິກ":      # lightning bolt
        d.polygon([(cx + s * 0.15, cy - s), (cx - s * 0.6, cy + s * 0.15), (cx - s * 0.05, cy + s * 0.15),
                   (cx - s * 0.2, cy + s), (cx + s * 0.6, cy - s * 0.15), (cx + s * 0.05, cy - s * 0.15)], fill=c)

def brand_mark(img, ep_cat):
    """Top-right channel tag shown on every episode."""
    d = ImageDraw.Draw(img)
    tw = line_width(CHANNEL, 34, 700)
    x1 = W - 70
    draw_line(d, x1, 170, CHANNEL, 34, CREAM, 700, align="right")
    icon(d, ep_cat, x1 - tw - 30, 158, 15, CAT_COLORS.get(ep_cat, AMBER))

def share_cta(img, t, t0, t1, y=None):
    draw_block(img, W / 2, y or BOTTOM_Y, [(SHARE_CTA, CYAN)], 52, alpha=fade(t, t0, t1, 0.4, 0.5))
