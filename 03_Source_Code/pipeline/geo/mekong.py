"""Map-story clip: ແມ່ນ້ຳຂອງ (Mekong). 1080x1920, 30 fps.
usage: python3 mekong.py out.mp4 [f0 f1]      (frame range, for parallel parts)
       python3 mekong.py --still t1,t2,...   (preview PNGs)
"""
import sys, math, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw
sys.path.insert(0, "/home/claude/ep1")
import common as C
from common import W, H, FPS, prog, ease_io, lerp, clamp, draw_line, line_width
Image.MAX_IMAGE_PIXELS = None

DUR = 51.0
ORANGE = (246, 140, 38)
HL = np.array([255, 128, 30], np.float32)
NAVYTXT = (10, 16, 34)
CREAMT = (255, 244, 226)
RIVER = (140, 215, 255)

# ---------------- data ----------------
TEXG = np.asarray(Image.open("tex.jpg").convert("RGB"))
TEXA = np.asarray(Image.open("tex_asia.png").convert("RGB"))
A_LON0, A_LAT1, A_PPD = 60.0, 50.0, 30.0
A_LON1, A_LAT0 = 135.0, -5.0
MEK = np.load("mekong.npy")
seg = np.hypot(np.diff(MEK[:, 0]) * np.cos(np.radians(MEK[:-1, 1])), np.diff(MEK[:, 1])) * 111.2
CUM = np.concatenate([[0], np.cumsum(seg)])
LEN = CUM[-1]
_cj = json.load(open("countries50.json"))
BORDER_SET = ["China", "Myanmar", "Laos", "Thailand", "Cambodia", "Vietnam", "India", "Bangladesh", "Bhutan", "Nepal", "Malaysia"]
POLY = {k: [np.array(ring, np.float64) for poly in _cj[k] for ring in poly] for k in BORDER_SET}
SOURCE = (94.68, 33.75)

# river progress: time -> along-river km (entry points by index on the path)
def _km(i): return CUM[i]
RIV_T = [11.0, 13.6, 14.4, 15.6, 19.5, 22.5, 24.0]
RIV_K = [0, _km(224), _km(232), _km(241), _km(427), _km(481), LEN]
ENTRY = {"China": 11.3, "Myanmar": 13.6, "Laos": 14.4, "Thailand": 15.6, "Cambodia": 19.5, "Vietnam": 22.5}
LAO_NAME = {"China": "ຈີນ", "Myanmar": "ມຽນມາ", "Laos": "ລາວ", "Thailand": "ໄທ", "Cambodia": "ກຳປູເຈຍ", "Vietnam": "ຫວຽດນາມ"}
LABEL_AT = {"China": (98.4, 30.2), "Myanmar": (98.9, 21.6), "Laos": (102.9, 20.6), "Thailand": (101.6, 16.4),
            "Cambodia": (104.4, 12.9), "Vietnam": (107.0, 11.3)}


def river_km(t):
    return float(np.interp(t, RIV_T, RIV_K)) if t >= 11 else 0.0


def river_point(km):
    return float(np.interp(km, CUM, MEK[:, 0])), float(np.interp(km, CUM, MEK[:, 1]))


# ---------------- camera ----------------
def gl(a, b, u):  # geometric lerp (zoom)
    return math.exp(lerp(math.log(a), math.log(b), u))


def follow(t):
    """Camera that trails the river tip (tip sits a little above centre)."""
    span = lerp(16, 19, ease_io(prog(t, 11, 13.5)))
    pts = [river_point(river_km(t - k * 0.15)) for k in range(10)]
    lon = sum(p[0] for p in pts) / 10
    lat = sum(p[1] for p in pts) / 10
    return lon, lat - 110 * span / H, span


S2_END = (95.0, SOURCE[1] - 160 * 16 / H, 16.0)
S4 = (100.6, 22.4, 32.0)
S5 = (103.8, 16.6, 14.0)
S6 = (105.6, 11.2, 12.0)
S7 = (102.0, 18.0, 42.3)
G_R0 = 440


def flat_mix(a, b, u):
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u), gl(a[2], b[2], u))


def views(t):
    """List of (weight, view). view = ('g', lon, lat, R, cy) or ('f', lon, lat, span)."""
    if t < 6.2:
        if t < 4.5:
            u = ease_io(prog(t, 0, 4.5))
            return [(1, ("g", lerp(66, 102, u), lerp(10, 18, u), G_R0 * (1 + 0.05 * t / 4.5), 1040))]
        u = ease_io(prog(t, 4.5, 6.2))
        r0 = G_R0 * 1.05
        return [(1, ("g", lerp(102, 95, u), lerp(18, 31.5, u), gl(r0, 2600, u), lerp(1040, 960, u)))]
    if t < 11:
        u = ease_io(prog(t, 6.2, 9.0))
        f = ("f",) + flat_mix((95, 31.5, H * 57.2958 / 2600), S2_END, u)
        x = prog(t, 6.2, 6.5)
        if x < 1:
            return [(1 - x, ("g", 95, 31.5, 2600, 960)), (x, f)]
        return [(1, f)]
    if t < 25:
        u = ease_io(prog(t, 11, 12.2))
        return [(1, ("f",) + flat_mix(S2_END, follow(t), u))]
    if t < 31:
        return [(1, ("f",) + flat_mix(follow(25), S4, ease_io(prog(t, 25, 26.8))))]
    if t < 38:
        return [(1, ("f",) + flat_mix(S4, S5, ease_io(prog(t, 31, 32.8))))]
    if t < 45:
        return [(1, ("f",) + flat_mix(S5, S6, ease_io(prog(t, 38, 39.8))))]
    u = ease_io(prog(t, 45, 46.4))
    f = ("f",) + flat_mix(S6, S7, u)
    if t < 46.4:
        return [(1, f)]
    g_u = ease_io(prog(t, 46.4, 48.8))
    g = ("g", lerp(102, 100, g_u) - 4 * prog(t, 48.8, 51), 18, gl(2600, G_R0, g_u), lerp(960, 1040, g_u))
    x = prog(t, 46.4, 46.7)
    return [(1 - x, f), (x, g)] if x < 1 else [(1, g)]


# ---------------- projection ----------------
def project(v, lon, lat):
    lon = np.asarray(lon, np.float64); lat = np.asarray(lat, np.float64)
    if v[0] == "f":
        _, clon, clat, span = v
        deg = span / H
        return W / 2 + (lon - clon) * math.cos(math.radians(clat)) / deg, H / 2 - (lat - clat) / deg, np.ones(lon.shape, bool)
    _, clon, clat, R, cy = v
    p0, l0 = math.radians(clat), math.radians(clon)
    p, l = np.radians(lat), np.radians(lon)
    x = W / 2 + R * np.cos(p) * np.sin(l - l0)
    y = cy - R * (math.cos(p0) * np.sin(p) - math.sin(p0) * np.cos(p) * np.cos(l - l0))
    vis = math.sin(p0) * np.sin(p) + math.cos(p0) * np.cos(p) * np.cos(l - l0) > 0
    return x, y, vis


_YY, _XX = np.mgrid[0:H, 0:W].astype(np.float32)
_BG = None


def background():
    global _BG
    if _BG is None:
        g = np.linspace(0, 1, H)[:, None, None]
        _BG = (np.array([6, 10, 24]) * (1 - g) + np.array([12, 22, 46]) * g) * np.ones((H, W, 3))
        rng = np.random.default_rng(3)
        for _ in range(260):
            x, y = rng.integers(0, W), rng.integers(0, H)
            _BG[y, x] = np.minimum(255, _BG[y, x] + rng.uniform(40, 150))
        _BG = cv2.GaussianBlur(_BG.astype(np.float32), (3, 3), 0.6)
    return _BG.copy()


def sample(lon, lat):
    """Texture colour for lon/lat arrays (float32 HxWx3). Uses the sharp regional texture where available."""
    ug = (((lon + 180) % 360) / 360 * TEXG.shape[1]).astype(np.float32)
    vg = ((90 - lat) / 180 * TEXG.shape[0]).astype(np.float32)
    out = cv2.remap(TEXG, ug, vg, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP).astype(np.float32)
    ua = ((lon - A_LON0) * A_PPD).astype(np.float32)
    va = ((A_LAT1 - lat) * A_PPD).astype(np.float32)
    w = np.clip(np.minimum.reduce([lon - A_LON0, A_LON1 - lon, lat - A_LAT0, A_LAT1 - lat]) / 1.5, 0, 1).astype(np.float32)
    if w.max() > 0:
        a = cv2.remap(TEXA, ua, va, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
        out = out * (1 - w[..., None]) + a * w[..., None]
    return out


def render_map(v):
    if v[0] == "f":
        _, clon, clat, span = v
        deg = span / H
        lon = clon + (_XX - W / 2) * deg / math.cos(math.radians(clat))
        lat = clat - (_YY - H / 2) * deg
        img = sample(lon, lat)
        # gentle vignette
        r = np.hypot((_XX - W / 2) / W, (_YY - H / 2) / H)
        return img * (1 - 0.35 * np.clip(r - 0.25, 0, 1)[..., None])
    _, clon, clat, R, cy = v
    img = background()
    dx = (_XX - W / 2) / R
    dy = (cy - _YY) / R
    rho2 = dx * dx + dy * dy
    inside = rho2 < 1
    z = np.sqrt(np.clip(1 - rho2, 0, 1))
    p0, l0 = math.radians(clat), math.radians(clon)
    lat = np.degrees(np.arcsin(np.clip(z * math.sin(p0) + dy * math.cos(p0), -1, 1)))
    lon = clon + np.degrees(np.arctan2(dx, z * math.cos(p0) - dy * math.sin(p0)))
    col = sample(lon, lat)
    # lighting from upper-left + limb darkening
    nx, ny = dx, dy
    light = np.clip(0.55 + 0.45 * (z * 0.75 - nx * 0.35 + ny * 0.45), 0.25, 1.15)
    col = col * (light * (0.55 + 0.45 * z ** 0.5))[..., None]
    rim = np.exp(-np.abs(np.sqrt(rho2) - 1) * R / 14)
    edge = np.clip((1 - np.sqrt(rho2)) * R, 0, 1)        # AA edge
    img = img * (1 - edge[..., None]) + col * edge[..., None]
    img += (rim * (~inside | (rho2 > 0.9)))[..., None] * np.array([40, 95, 190], np.float32) * 0.9
    return img


# ---------------- overlays on the map ----------------
KEYS = {  # country highlight alpha keyframes (t, a)
    "Laos": [(0, 0), (0.8, 0.0), (1.4, 0.55), (4.3, 0.55), (5.0, 0), (14.2, 0), (14.7, 0.6), (15.8, 0.35), (25, 0.35), (31.2, 0.35),
             (32.0, 0.62), (37.8, 0.62), (38.6, 0.18), (45, 0.18), (46.5, 0.0), (48.6, 0.0), (49.2, 0.6), (51, 0.6)],
    "China": [(0, 0), (11.1, 0), (11.6, 0.45), (13.6, 0.22), (31.2, 0.22), (32.0, 0.0)],
    "Myanmar": [(0, 0), (13.4, 0), (13.9, 0.6), (15.0, 0.3), (31.2, 0.3), (32.0, 0.0)],
    "Thailand": [(0, 0), (15.4, 0), (15.9, 0.6), (17.5, 0.3), (31.2, 0.3), (32.0, 0.0)],
    "Cambodia": [(0, 0), (19.3, 0), (19.8, 0.6), (21.5, 0.3), (38.2, 0.3), (39.0, 0.45), (44.8, 0.45), (45.6, 0)],
    "Vietnam": [(0, 0), (22.3, 0), (22.8, 0.6), (24.5, 0.3), (38.2, 0.3), (39.0, 0.45), (44.8, 0.45), (45.6, 0)],
}


def keyval(keys, t):
    ts, vs = zip(*keys)
    return float(np.interp(t, ts, vs))


def fill_country(img, v, name, a, t):
    if a <= 0.01:
        return
    mask = np.zeros((H, W), np.uint8)
    for ring in POLY[name]:
        x, y, vis = project(v, ring[:, 0], ring[:, 1])
        if not vis.any():
            continue
        pts = np.stack([x, y], 1)
        if np.abs(pts).max() > 30000:
            continue
        cv2.fillPoly(mask, [np.round(pts * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
    ys, xs = np.nonzero(mask[::8, ::8])
    if len(xs) == 0 and not mask.any():
        return
    m = mask.astype(np.float32)[..., None] / 255 * a
    lum = img.mean(2, keepdims=True) / 255
    hl = HL * (0.55 + 0.75 * lum)
    img[:] = img * (1 - m) + hl * m


def borders(img, v, alpha):
    if alpha <= 0:
        return
    layer = np.zeros((H, W), np.uint8)
    for name in BORDER_SET:
        for ring in POLY[name]:
            x, y, vis = project(v, ring[:, 0], ring[:, 1])
            if vis.mean() < 0.99:
                continue
            pts = np.stack([x, y], 1)
            if np.abs(pts).max() > 30000:
                continue
            cv2.polylines(layer, [np.round(pts * 16).astype(np.int32)], True, 255, 2, cv2.LINE_AA, shift=4)
    m = layer.astype(np.float32)[..., None] / 255 * alpha
    img[:] = img * (1 - m) + np.array([255, 245, 230], np.float32) * m


def river(img, v, t, width):
    km = river_km(t) if t < 25 else LEN
    if t < 11 or km <= 1:
        return None
    n = int(np.searchsorted(CUM, km))
    tip = river_point(km)
    pts_ll = np.vstack([MEK[:n], [tip]])
    x, y, vis = project(v, pts_ll[:, 0], pts_ll[:, 1])
    pts = np.stack([x, y], 1)
    s = 4  # glow on a 1/4 layer
    glow = np.zeros((H // s, W // s), np.float32)
    cv2.polylines(glow, [np.round(pts / s * 16).astype(np.int32)], False, 1.0, max(2, int(width * 2.2 / s)), cv2.LINE_AA, shift=4)
    glow = cv2.GaussianBlur(glow, (0, 0), 3.5)
    glow = cv2.resize(glow, (W, H), interpolation=cv2.INTER_LINEAR)
    img += glow[..., None] * np.array([60, 140, 255], np.float32) * 0.9
    core = np.zeros((H, W), np.uint8)
    cv2.polylines(core, [np.round(pts * 16).astype(np.int32)], False, 255, max(2, int(width)), cv2.LINE_AA, shift=4)
    m = core.astype(np.float32)[..., None] / 255
    img[:] = img * (1 - m) + np.array(RIVER, np.float32) * m
    # flowing light dots along the river
    spacing = 160.0
    dots = (np.arange(0, LEN + spacing, spacing) + t * 90) % (LEN + spacing)
    dots = dots[dots < km - 20]
    if len(dots):
        dl = np.array([river_point(d) for d in dots])
        dx, dy, dv = project(v, dl[:, 0], dl[:, 1])
        for a, b in zip(dx, dy):
            cv2.circle(img, (int(a * 16), int(b * 16)), int(max(2, width * 0.55) * 16), (255, 255, 255), -1, cv2.LINE_AA, shift=4)
    tx, ty, _ = project(v, [tip[0]], [tip[1]])
    return float(tx[0]), float(ty[0]), km < LEN - 1


def river_width(v):
    if v[0] == "g":
        return clamp(v[3] / 260, 2.5, 7)
    return clamp(4 + (20 - v[3]) * 0.25, 3.5, 7)


def compose_view(v, t):
    img = render_map(v)
    for name, keys in KEYS.items():
        a = keyval(keys, t)
        if name == "Laos" and t < 5.5 or (name == "Laos" and t > 48.6):
            a *= 0.75 + 0.25 * math.sin(t * 5)
        fill_country(img, v, name, a, t)
    borders(img, v, 0.42 if v[0] == "f" else 0.28)
    tip = river(img, v, t, river_width(v))
    if tip and tip[2]:
        tx, ty = tip[0], tip[1]
        r = 26 + 6 * math.sin(t * 8)
        cv2.circle(img, (int(tx * 16), int(ty * 16)), int(r * 16), (200, 235, 255), 2, cv2.LINE_AA, shift=4)
        cv2.circle(img, (int(tx * 16), int(ty * 16)), int(9 * 16), (255, 255, 255), -1, cv2.LINE_AA, shift=4)
    return img


# ---------------- UI (PIL) ----------------
def layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def put(base, lay, a):
    if a <= 0.01:
        return
    if a < 1:
        lay.putalpha(lay.getchannel("A").point(lambda q: int(q * a)))
    base.alpha_composite(lay)


def fit(text, size, maxw, w=700):
    while line_width(text, size, w) > maxw and size > 24:
        size -= 2
    return size


def caption(base, text, t, t0, t1, y=1335, size=50, col=CREAMT):
    a = C.fade(t, t0, t1, 0.3, 0.3)
    if a <= 0:
        return
    L = layer(); d = ImageDraw.Draw(L)
    s = fit(text, size, W - 90)
    rise = (1 - C.ease(prog(t, t0, t0 + 0.35))) * 18
    draw_line(d, W / 2, y + rise, text, s, col + (255,), 700, stroke=6, stroke_fill=(6, 10, 22, 235))
    put(base, L, a)


def pill(base, text, t, t0, t1, y=268):
    a = C.fade(t, t0, t1, 0.3, 0.3)
    if a <= 0:
        return
    L = layer(); d = ImageDraw.Draw(L)
    s = 36
    tw = line_width(text, s)
    pw = tw + 64
    sc = 0.85 + 0.15 * C.ease(prog(t, t0, t0 + 0.3))
    pw *= sc
    d.rounded_rectangle((W / 2 - pw / 2, y - 34, W / 2 + pw / 2, y + 34), 34, fill=ORANGE + (255,))
    draw_line(d, W / 2, y + 13, text, s, NAVYTXT + (255,))
    put(base, L, a)


def icon(d, kind, cx, cy, s, col):
    c = col + (255,)
    if kind == "mountain":
        d.polygon([(cx - s, cy + s * 0.7), (cx - s * 0.2, cy - s * 0.8), (cx + s * 0.25, cy - s * 0.1), (cx + s * 0.5, cy - s * 0.45), (cx + s, cy + s * 0.7)], fill=c)
    elif kind == "flag":
        d.line([(cx - s * 0.6, cy - s), (cx - s * 0.6, cy + s)], fill=c, width=max(3, int(s / 5)))
        d.polygon([(cx - s * 0.6, cy - s), (cx + s * 0.8, cy - s * 0.55), (cx - s * 0.6, cy - s * 0.1)], fill=c)
    elif kind == "ruler":
        d.line([(cx - s, cy), (cx + s, cy)], fill=c, width=max(3, int(s / 5)))
        for k in (-1, 1):
            d.polygon([(cx + k * s, cy), (cx + k * s * 0.55, cy - s * 0.4), (cx + k * s * 0.55, cy + s * 0.4)], fill=c)
    elif kind == "rank":
        d.polygon([(cx - s * 0.7, cy - s * 0.8), (cx + s * 0.7, cy - s * 0.8), (cx + s * 0.5, cy + s * 0.1), (cx - s * 0.5, cy + s * 0.1)], fill=c)
        d.rectangle((cx - s * 0.12, cy + s * 0.1, cx + s * 0.12, cy + s * 0.6), fill=c)
        d.rectangle((cx - s * 0.5, cy + s * 0.6, cx + s * 0.5, cy + s * 0.85), fill=c)
    elif kind == "fish":
        d.ellipse((cx - s * 0.9, cy - s * 0.45, cx + s * 0.45, cy + s * 0.45), fill=c)
        d.polygon([(cx + s * 0.3, cy), (cx + s, cy - s * 0.5), (cx + s, cy + s * 0.5)], fill=c)
        d.ellipse((cx - s * 0.6, cy - s * 0.15, cx - s * 0.4, cy + s * 0.05), fill=(14, 20, 36, 255))
    elif kind == "people":
        for ox, r in ((-0.45, 0.28), (0.45, 0.28), (0, 0.34)):
            d.ellipse((cx + ox * s - r * s, cy - s * 0.75 - r * s, cx + ox * s + r * s, cy - s * 0.75 + r * s), fill=c)
            d.pieslice((cx + ox * s - r * 1.9 * s, cy - s * 0.2, cx + ox * s + r * 1.9 * s, cy + s * 1.2), 180, 360, fill=c)


def card(base, t, t0, t1, cx, w, label, value, kind, y=1405, h=180):
    a = C.fade(t, t0, t1, 0.3, 0.3)
    if a <= 0:
        return
    L = layer(); d = ImageDraw.Draw(L)
    k = C.ease(prog(t, t0, t0 + 0.35))
    yy = y + (1 - k) * 30
    d.rounded_rectangle((cx - w / 2, yy, cx + w / 2, yy + h), 26, fill=(12, 18, 34, 228), outline=ORANGE + (255,), width=4)
    ix = cx - w / 2 + 62
    icon(d, kind, ix, yy + h / 2, 30, ORANGE)
    tx = ix + 52
    ls = fit(label, 32, w - (tx - (cx - w / 2)) - 24, 400)
    draw_line(d, tx, yy + 62, label, ls, (225, 214, 196, 255), 400, align="left")
    vs = fit(value, 64, w - (tx - (cx - w / 2)) - 24)
    draw_line(d, tx, yy + 140, value, vs, (255, 176, 74, 255), 700, align="left")
    put(base, L, a)


def pin(base, v, lon, lat, name, t, t0, t1, side="right", size=40, dot=ORANGE):
    a = C.fade(t, t0, t1, 0.3, 0.4)
    if a <= 0:
        return
    x, y, vis = project(v, [lon], [lat])
    x, y = float(x[0]), float(y[0])
    L = layer(); d = ImageDraw.Draw(L)
    k = C.ease(prog(t, t0, t0 + 0.4))
    r = 13 * (0.4 + 0.6 * k)
    d.ellipse((x - r - 5, y - r - 5, x + r + 5, y + r + 5), fill=(255, 250, 240, 255))
    d.ellipse((x - r, y - r, x + r, y + r), fill=dot + (255,))
    if name:
        al = "left" if side == "right" else "right"
        tx = x + 30 if side == "right" else x - 30
        draw_line(d, tx, y + size * 0.36, name, size, (255, 250, 240, 255), 700, align=al, stroke=5, stroke_fill=(8, 12, 26, 230))
    put(base, L, a)


def label(base, v, lon, lat, text, t, t0, t1, size=46):
    a = C.fade(t, t0, t1, 0.35, 0.4)
    if a <= 0:
        return
    x, y, vis = project(v, [lon], [lat])
    L = layer(); d = ImageDraw.Draw(L)
    k = C.ease(prog(t, t0, t0 + 0.4))
    draw_line(d, float(x[0]), float(y[0]) + 16 + (1 - k) * 12, text, size, (255, 248, 236, 255), 700, stroke=6, stroke_fill=(40, 18, 4, 220))
    put(base, L, a)


LOGO = None


EP, CAT, CAT_COL = 6, "ພູມສາດ", (110, 214, 190)


def brand(base):
    """Same chrome as EP.1-5: amber 'ຮູ້ບໍ່? EP.N' pill + category top-left, channel name + logo top-right."""
    global LOGO
    if LOGO is None:
        im = Image.open("/home/claude/ep1/brand/minimal/logo_final_800.png").convert("RGB").resize((60, 60), Image.LANCZOS)
        m = Image.new("L", (240, 240), 0)
        ImageDraw.Draw(m).ellipse((0, 0, 239, 239), fill=255)
        im.putalpha(m.resize((60, 60), Image.LANCZOS))
        LOGO = im
    d = ImageDraw.Draw(base)
    x, y = 70, 120
    d.rounded_rectangle((x, y, x + 300, y + 74), 37, fill=C.AMBER + (255,))
    draw_line(d, x + 150, y + 51, f"ຮູ້ບໍ່? EP.{EP}", 38, C.BG + (255,), 700)
    draw_line(d, x + 320, y + 50, CAT, 32, CAT_COL + (255,), 700, align="left", stroke=4, stroke_fill=(6, 10, 22, 200))
    x1 = W - 70
    tw = draw_line(d, x1, 170, C.CHANNEL, 34, CREAMT + (255,), 700, align="right", stroke=4, stroke_fill=(6, 10, 22, 200))
    base.alpha_composite(LOGO, (int(x1 - tw - 74), 127))


def credit(base):
    d = ImageDraw.Draw(base)
    draw_line(d, W / 2, 1880, "ຂໍ້ມູນ: MRC, Britannica  |  ແຜນທີ່: Natural Earth, NOAA", 24, (200, 200, 210, 200), 400)


def ui(img, t, v):
    base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
    brand(base)
    # chapter pills
    for txt, a, b in [("ເປີດເລື່ອງ", 0.2, 4.8), ("ຕົ້ນນ້ຳ", 6.3, 10.9), ("ເສັ້ນທາງ", 11.2, 24.9), ("ຕົວເລກ", 25.2, 30.9),
                      ("ໃນລາວ", 31.2, 37.9), ("ຊີວິດ", 38.2, 44.9), ("ບອກຕໍ່", 46.8, 51.5)]:
        pill(base, txt, t, a, b)
    # hook
    if t < 5:
        a = C.fade(t, 0.25, 4.7, 0.35, 0.4)
        L = layer(); d = ImageDraw.Draw(L)
        k = C.ease(prog(t, 0.25, 0.8))
        draw_line(d, W / 2, 420 + (1 - k) * 24, "ແມ່ນ້ຳຂອງ ທີ່ໄຫຼຜ່ານລາວ", 76, ORANGE + (255,), 700, stroke=6, stroke_fill=(6, 10, 22, 230))
        draw_line(d, W / 2, 530 + (1 - k) * 24, "ເລີ່ມຕົ້ນມາຈາກໃສ?", 76, CREAMT + (255,), 700, stroke=6, stroke_fill=(6, 10, 22, 230))
        put(base, L, a)
    # S2 source
    if 6 < t < 13.5 and v[0] == "f":
        pin(base, v, SOURCE[0], SOURCE[1], "ຕົ້ນນ້ຳ", t, 6.7, 12.2, size=42, dot=(120, 210, 255))
    caption(base, "ຕົ້ນນ້ຳຢູ່ເທິງ ລາບສູງທິເບດ ປະເທດຈີນ", t, 6.4, 8.8)
    caption(base, "ສູງກວ່າ 5,000 ແມັດ ຈາກລະດັບນ້ຳທະເລ", t, 8.8, 10.9)
    card(base, t, 7.4, 10.9, W / 2, 640, "ຄວາມສູງຂອງຕົ້ນນ້ຳ", "ປະມານ 5,200 ມ.", "mountain")
    # S3 route
    if 11 < t < 31.2 and v[0] == "f":
        for name, t0 in ENTRY.items():
            lon, lat = LABEL_AT[name]
            label(base, v, lon, lat, LAO_NAME[name], t, t0 + 0.1, 31.0 if t0 > 12 else 25.0)
    caption(base, "ໄຫຼລົງໃຕ້ ຜ່ານຈີນ ມຽນມາ ລາວ ແລະ ໄທ", t, 11.4, 18.6)
    caption(base, "ຜ່ານກຳປູເຈຍ ແລ້ວອອກທະເລທີ່ຫວຽດນາມ", t, 18.7, 24.9)
    n = sum(1 for x in ENTRY.values() if t >= x)
    card(base, t, 11.6, 24.9, W / 2, 560, "ໄຫຼຜ່ານ", f"{max(1, n)} / 6 ປະເທດ", "flag")
    # S4 numbers
    caption(base, "ຍາວເກືອບ 5,000 ກິໂລແມັດ", t, 25.4, 28.2)
    caption(base, "ຍາວເປັນອັນດັບ 12 ຂອງໂລກ", t, 28.2, 30.9)
    card(base, t, 25.8, 30.9, 285, 480, "ຄວາມຍາວ", "ເກືອບ 5,000 ກມ.", "ruler")
    card(base, t, 28.3, 30.9, 795, 480, "ອັນດັບຄວາມຍາວ", "ທີ 12 ຂອງໂລກ", "rank")
    # S5 Laos
    if 31 < t < 38.6 and v[0] == "f":
        label(base, v, 103.4, 18.7, "ລາວ", t, 32.0, 38.2, size=62)
        pin(base, v, 102.13, 19.89, "ຫຼວງພະບາງ", t, 34.8, 38.2, side="left")
        pin(base, v, 102.60, 17.96, "ວຽງຈັນ", t, 35.5, 38.2, side="left")
        pin(base, v, 105.79, 15.12, "ປາກເຊ", t, 36.2, 38.2)
    caption(base, "ໃນລາວ ແມ່ນ້ຳຂອງເປັນທັງຊາຍແດນ ແລະ ເສັ້ນທາງຊີວິດ", t, 31.3, 34.6)
    caption(base, "ຜ່ານຫຼວງພະບາງ ວຽງຈັນ ຈົນຮອດປາກເຊ", t, 34.6, 37.9)
    # S6 lower Mekong
    if 38 < t < 45.4 and v[0] == "f":
        pin(base, v, 104.92, 11.56, "ພະນົມເປັນ", t, 39.6, 44.8, side="left")
        label(base, v, 106.3, 10.05, "ປາກແມ່ນ້ຳ", t, 40.2, 44.8, size=40)
    caption(base, "ແມ່ນ້ຳຂອງ ມີປາຫຼາຍກວ່າ 850 ຊະນິດ", t, 38.3, 41.5)
    caption(base, "ແລະ ລ້ຽງຊີວິດຜູ້ຄົນ ຫຼາຍສິບລ້ານຄົນ", t, 41.5, 44.9)
    card(base, t, 38.9, 44.9, 285, 480, "ປາໃນແມ່ນ້ຳຂອງ", "850+ ຊະນິດ", "fish")
    card(base, t, 41.7, 44.9, 795, 480, "ຄົນໃນລຸ່ມແມ່ນ້ຳຂອງ", "ປະມານ 65 ລ້ານ", "people")
    # S7 ending
    if t > 46.6:
        a = C.fade(t, 47.0, 52, 0.4, 0.4)
        L = layer(); d = ImageDraw.Draw(L)
        k = C.ease(prog(t, 47.0, 47.5))
        draw_line(d, W / 2, 420 + (1 - k) * 20, "ເຈົ້າຢູ່ໃກ້ແມ່ນ້ຳຂອງບໍ?", 70, ORANGE + (255,), 700, stroke=6, stroke_fill=(6, 10, 22, 230))
        draw_line(d, W / 2, 520 + (1 - k) * 20, "ຄອມເມັ້ນບອກແຂວງຂອງເຈົ້າ!", 62, CREAMT + (255,), 700, stroke=6, stroke_fill=(6, 10, 22, 230))
        put(base, L, a)
        caption(base, C.SHARE_CTA, t, 48.6, 52, y=1640, size=50, col=(120, 210, 255))
    credit(base)
    return np.asarray(base.convert("RGB"))


def frame(t):
    vs = views(t)
    img = None
    for w, v in vs:
        f = compose_view(v, t)
        img = f * w if img is None else img + f * w
    dom = max(vs, key=lambda x: x[0])[1]
    return ui(img, t, dom)


if __name__ == "__main__":
    if sys.argv[1] == "--still":
        for s in sys.argv[2].split(","):
            Image.fromarray(frame(float(s))).save(f"still_{float(s):05.1f}.png")
            print("still", s)
        sys.exit()
    out = sys.argv[1]
    n = int(DUR * FPS)
    f0, f1 = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, n)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(f0, f1):
        p.stdin.write(frame(i / FPS).tobytes())
        if i % 60 == 0:
            print(out, i, flush=True)
    p.stdin.close(); p.wait()
