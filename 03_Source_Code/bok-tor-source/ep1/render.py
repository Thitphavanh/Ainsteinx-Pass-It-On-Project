"""Render EP.1 (Venus) of the ຮູ້ບໍ່? series as a 1080x1920 silent MP4.
Voice-over is recorded by the creator; timings match captions.srt."""
import math, subprocess, sys
import numpy as np
import common as C
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
DUR = 40.0
FONTS = "/root/fonts/"
OUT = sys.argv[1] if len(sys.argv) > 1 else "ep1.mp4"
STILL = sys.argv[2] if len(sys.argv) > 2 else None   # e.g. "12.5" -> save png only

BG = (7, 11, 26)
CREAM = (255, 244, 222)
AMBER = (255, 181, 71)
CYAN = (90, 209, 255)
MUTED = (150, 160, 190)

_fc = {}
def font(kind, size, w=700):
    key = (kind, size, w)
    if key not in _fc:
        path = f"{FONTS}lao{700 if w >= 700 else 400}.ttf" if kind == "lao" else f"{FONTS}lat{w}.ttf"
        _fc[key] = ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    return _fc[key]

def is_lao(ch):
    return 0x0E80 <= ord(ch) <= 0x0EFF

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

def line_width(text, size, w):
    return sum(font(k, size, w).getlength(t) for k, t in runs(text))

def draw_line(d, cx, base_y, text, size, fill, w=700, align="center", stroke=0, stroke_fill=(0, 0, 0)):
    tw = line_width(text, size, w)
    x = cx - tw / 2 if align == "center" else cx
    for k, t in runs(text):
        f = font(k, size, w)
        d.text((x, base_y), t, font=f, fill=fill, anchor="ls",
               stroke_width=stroke, stroke_fill=stroke_fill)
        x += f.getlength(t)
    return tw

def draw_block(img, cx, top, lines, size, fill, w=700, gap=1.45, alpha=1.0, shadow=True):
    """lines: list of str or (str, color). Returns bottom y."""
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
    if alpha < 1:
        a = layer.getchannel("A").point(lambda v: int(v * alpha))
        layer.putalpha(a)
    img.alpha_composite(layer)
    return y

# ---------- easing ----------
def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def prog(t, a, b): return clamp((t - a) / (b - a))
def ease(x): return 1 - (1 - x) ** 3
def ease_io(x): return x * x * (3 - 2 * x)
def fade(t, a, b, fin=0.35, fout=0.35):
    return clamp(min((t - a) / fin, (b - t) / fout))

# ---------- stars ----------
rng = np.random.default_rng(7)
STARS = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.6, 2.4), rng.uniform(0, 6.28), rng.uniform(0.5, 2))
         for _ in range(320)]
def starfield(t):
    img = Image.new("RGBA", (W, H), BG + (255,))
    # soft nebula glow
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
STAR_CACHE = {}
def bg(t):
    k = int(t * 10)  # twinkle at 10 Hz is plenty
    if k not in STAR_CACHE:
        STAR_CACHE.clear(); STAR_CACHE[k] = starfield(k / 10)
    return STAR_CACHE[k].copy()

# ---------- planet rendering ----------
def smooth_noise(h, w, scale, seed):
    r = np.random.default_rng(seed)
    small = r.random((h // scale + 2, w // scale + 2))
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((w + scale, h + scale), Image.BICUBIC)
    a = np.asarray(im, dtype=np.float32)[:h, :w] / 255.0
    return np.concatenate([a[:, : w // 2], a[:, : w // 2][:, ::-1]], axis=1)  # mirror -> seamless wrap

def make_texture(kind):
    th, tw = 512, 1024
    lat = np.linspace(-1, 1, th)[:, None]
    n = 0.55 * smooth_noise(th, tw, 64, 1) + 0.3 * smooth_noise(th, tw, 16, 2) + 0.15 * smooth_noise(th, tw, 6, 3)
    if kind == "venus":
        band = 0.5 + 0.5 * np.sin(lat * 9 + n * 5)
        c1 = np.array([238, 205, 145]); c2 = np.array([206, 150, 80])
        tex = c1 * band[..., None] + c2 * (1 - band[..., None])
        tex = tex * (0.85 + 0.25 * n[..., None])
    else:  # earth-ish
        land = (smooth_noise(th, tw, 48, 9) > 0.55)
        tex = np.where(land[..., None], np.array([70, 150, 80]), np.array([40, 90, 190])).astype(np.float32)
        cloud = smooth_noise(th, tw, 20, 11) > 0.62
        tex = np.where(cloud[..., None], np.array([235, 240, 250]), tex)
    return np.clip(tex, 0, 255).astype(np.float32)

TEX = {"venus": make_texture("venus"), "earth": make_texture("earth")}
SPH = {}
def sphere(kind, D, rot):
    if D not in SPH:
        yy, xx = np.mgrid[-1:1:D * 1j, -1:1:D * 1j]
        rr = xx ** 2 + yy ** 2
        mask = rr <= 1
        z = np.sqrt(np.clip(1 - rr, 0, 1))
        lat = np.arcsin(np.clip(yy, -1, 1))
        lon = np.arctan2(xx, z)
        light = np.clip(xx * -0.45 + yy * -0.35 + z * 0.82, 0, 1) * 0.85 + 0.15
        SPH[D] = (mask, lat, lon, light, rr)
    mask, lat, lon, light, rr = SPH[D]
    tex = TEX[kind]; th, tw, _ = tex.shape
    u = ((lon + rot) / (2 * math.pi) % 1.0) * (tw - 1)
    v = (lat / math.pi + 0.5) * (th - 1)
    col = tex[v.astype(int), u.astype(int)] * light[..., None]
    rim = np.clip((rr - 0.82) / 0.18, 0, 1)[..., None]
    atmo = np.array([255, 215, 150]) if kind == "venus" else np.array([140, 190, 255])
    col = col * (1 - 0.35 * rim) + atmo * 0.35 * rim
    rgba = np.zeros((D, D, 4), np.uint8)
    rgba[..., :3] = np.clip(col, 0, 255)
    rgba[..., 3] = (mask * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")

def paste_planet(img, kind, cx, cy, D, rot, glow=True):
    D = max(8, int(D))
    if glow:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        c = (255, 190, 110, 90) if kind == "venus" else (110, 170, 255, 80)
        gd.ellipse((cx - D * 0.62, cy - D * 0.62, cx + D * 0.62, cy + D * 0.62), fill=c)
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(D * 0.12)))
    sp = sphere(kind, 640, rot).resize((D, D), Image.LANCZOS)
    img.alpha_composite(sp, (int(cx - D / 2), int(cy - D / 2)))

# ---------- UI pieces ----------
def badge(img, t):
    d = ImageDraw.Draw(img)
    x, y = 70, 120
    d.rounded_rectangle((x, y, x + 300, y + 74), 37, fill=AMBER + (255,))
    draw_line(d, x + 150, y + 51, "ຮູ້ບໍ່? EP.1", 38, BG, 700)
    draw_line(d, x + 320, y + 50, "ອາວະກາດ", 32, MUTED, 400, align="left")

def bar(img, x, y, w, h, frac, color, label, value_txt, done, alpha=1.0):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    draw_line(d, x, y - 22, label, 44, CREAM, 700, align="left")
    d.rounded_rectangle((x, y, x + w, y + h), h // 2, fill=(255, 255, 255, 40))
    fw = max(h, int(w * clamp(frac)))
    d.rounded_rectangle((x, y, x + fw, y + h), h // 2, fill=color + (255,))
    vw = line_width(value_txt, 50, 800)
    draw_line(d, x + w - vw, y + h + 66, value_txt, 50, color if done else CREAM, 800, align="left")
    if done:
        draw_line(d, x, y + h + 66, done, 46, color, 700, align="left")
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(layer)

def arrow_arc(d, cx, cy, r, a0, a1, color, width=10, head=34):
    pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
           for a in np.linspace(a0, a1, 40)]
    d.line(pts, fill=color, width=width, joint="curve")
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    tip = (x2 + math.cos(ang) * head * 0.6, y2 + math.sin(ang) * head * 0.6)
    l = (x2 + math.cos(ang + 2.5) * head, y2 + math.sin(ang + 2.5) * head)
    rr = (x2 + math.cos(ang - 2.5) * head, y2 + math.sin(ang - 2.5) * head)
    d.polygon([tip, l, rr], fill=color)

# ---------- scenes ----------
HOOK = ["ຮູ້ບໍ່ວ່າ ມີດາວເຄາະດວງໜຶ່ງ", ("ທີ່ 1 ມື້ ຍາວກວ່າ 1 ປີ?", AMBER)]

def frame(t):
    img = bg(t)
    rot = t * 0.18  # slow visible spin (artistic; real spin is far slower)

    # Scene A 0-6: hook + reveal
    if t < 6.6:
        a = fade(t, 0, 6.6, 0.01, 0.6)
        z = 0.75 + 0.25 * ease(prog(t, 0, 2.5))
        paste_planet(img, "venus", W / 2, 1120, 700 * z, rot)
        draw_block(img, W / 2, 380, HOOK, 74, CREAM, alpha=a)
        if t > 3.3:
            a2 = fade(t, 3.3, 6.6, 0.4, 0.6)
            draw_block(img, W / 2, 1560, [("ນັ້ນຄື ດາວພະສຸກ", AMBER)], 66, CREAM, alpha=a2)

    # Scene B 6-21: the race between one rotation and one orbit
    elif t < 21:
        a = fade(t, 6, 21, 0.5, 0.6)
        planet_y = 1120 - 560 * ease(prog(t, 6, 7.2))
        D = 700 - 360 * ease(prog(t, 6, 7.2))
        paste_planet(img, "venus", W / 2, planet_y, D, rot)
        days = 243 * ease_io(prog(t, 7.5, 17.5))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        img2 = img
        bar(img2, 120, 1010, 760, 46, days / 243, CYAN, "ໝູນຮອບຕົວເອງ 1 ຮອບ",
            f"{int(days)}/243", "ຄົບ 1 ມື້" if days >= 242.5 else None, alpha=a)
        bar(img2, 120, 1340, 760, 46, min(days, 225) / 225, AMBER, "ໂຄຈອນຮອບດວງອາທິດ 1 ຮອບ",
            f"{int(min(days, 225))}/225", "ຄົບ 1 ປີ" if days >= 224.5 else None, alpha=a)
        draw_block(img, W / 2, 1600, [f"ມື້ທີ {int(days)}"], 52, MUTED, w=400, alpha=a * fade(t, 7.5, 18, 0.4, 0.4))
        if t > 17.8:
            draw_block(img, W / 2, 1590, [("1 ມື້ ຍາວກວ່າ 1 ປີ!", AMBER)], 84, CREAM, alpha=fade(t, 17.8, 21, 0.3, 0.6))
        if t < 12:
            draw_block(img, W / 2, 760, ["ມັນໝູນຊ້າຫຼາຍ"], 56, CREAM, alpha=fade(t, 7, 12, 0.4, 0.4))

    # Scene C 21-26: spins backwards compared with Earth
    elif t < 26:
        a = fade(t, 21, 26, 0.5, 0.5)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        paste_planet(layer, "earth", 300, 1000, 300, -t * 0.9)
        paste_planet(layer, "venus", 780, 1000, 300, t * 0.9)  # opposite direction
        d = ImageDraw.Draw(layer)
        arrow_arc(d, 300, 1000, 200, 200, 340, CYAN)
        arrow_arc(d, 780, 1000, 200, 340, 200, AMBER)
        draw_line(d, 300, 1290, "ໂລກ", 54, CREAM)
        draw_line(d, 780, 1290, "ດາວພະສຸກ", 54, AMBER)
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
        img.alpha_composite(layer)
        draw_block(img, W / 2, 420, ["ມັນຍັງໝູນ", ("ກັບທິດກັບດາວເຄາະອື່ນ!", AMBER)], 72, CREAM, alpha=a)

    # Scene D 26-31: sunrise in the west
    elif t < 31:
        a = fade(t, 26, 31, 0.5, 0.5)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        # hazy Venus sky gradient
        for i in range(0, 1300, 6):
            c = tuple(int(v) for v in np.array([60, 30, 25]) + (np.array([235, 170, 90]) - np.array([60, 30, 25])) * (i / 1300))
            d.rectangle((0, 300 + i, W, 306 + i), fill=c + (255,))
        p = ease(prog(t, 26.5, 30.5))
        sx, sy = 230 + 60 * p, 1500 - 520 * p
        sun = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sun).ellipse((sx - 120, sy - 120, sx + 120, sy + 120), fill=(255, 240, 200, 255))
        layer.alpha_composite(sun.filter(ImageFilter.GaussianBlur(28)))
        # rocky ground
        ground = [(0, 1500), (180, 1460), (360, 1520), (560, 1470), (760, 1530), (930, 1480), (W, 1510), (W, H), (0, H)]
        d.polygon(ground, fill=(70, 38, 24, 255))
        draw_line(d, 200, 1640, "ທິດຕາເວັນຕົກ", 50, AMBER)
        draw_line(d, 880, 1640, "ທິດຕາເວັນອອກ", 50, MUTED, 400)
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
        img.alpha_composite(layer)
        draw_block(img, W / 2, 420, ["ດວງອາທິດ", ("ຂຶ້ນທາງທິດຕາເວັນຕົກ!", AMBER)], 80, CREAM, alpha=a)

    # Scene E 31-38: CTA, then settle back to the opening look so the loop is seamless
    else:
        a = fade(t, 31, 40.5, 0.5, 0.01)
        paste_planet(img, "venus", W / 2, 1120, 600 + 100 * ease(prog(t, 31, 40)), rot)
        draw_block(img, W / 2, 330, ["ຖ້າໄດ້ໄປຢູ່ດາວພະສຸກ", "ເຈົ້າຈະເຮັດຫຍັງ", ("ກັບ 1 ມື້ທີ່ຍາວຂະໜາດນີ້?", AMBER)],
                   64, CREAM, alpha=a * fade(t, 31, 38.6, 0.4, 0.5))
        draw_block(img, W / 2, 1560, [("ຄອມເມັ້ນບອກແດ່!", CYAN)], 66, CREAM, alpha=a * fade(t, 32, 34.6, 0.4, 0.4))
        C.share_cta(img, t, 34.7, 38.6)
        if t > 38.6:
            draw_block(img, W / 2, 380, HOOK, 74, CREAM, alpha=prog(t, 38.6, 39.6))

    C.badge(img, 1, "ອາວະກາດ")
    C.brand_mark(img, "ອາວະກາດ")
    d = ImageDraw.Draw(img)
    draw_line(d, W / 2, 1745, "ຂໍ້ມູນ: NASA Science  •  ພາບປະກອບ, ບໍ່ແມ່ນມາດຕາສ່ວນຈິງ", 28, MUTED, 400)
    return img.convert("RGB")

if STILL:
    for s in STILL.split(","):
        frame(float(s)).save(f"still_{s}.png")
    sys.exit()

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                       "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                       "-c:a", "aac", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
n = int(DUR * FPS)
for i in range(n):
    ff.stdin.write(frame(i / FPS).tobytes())
    if i % 150 == 0:
        print(f"{i}/{n}", flush=True)
ff.stdin.close(); ff.wait()
print("done", OUT)
