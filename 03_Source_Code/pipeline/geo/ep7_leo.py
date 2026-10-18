"""EP.7 ສິລະປະ — ເລໂອນາໂດ ດາວິນຊີ: ປະຫວັດ ຄວາມເກັ່ງ ແລະ ຄວາມອັດສະລິຍະ (3D + map, ~60 s)."""
import math, json
import numpy as np, cv2
from PIL import Image, ImageDraw
import lightyear as LY            # registers the extra card icons (clock, star, bolt, ...)
import eng3d as E
from eng3d import M, C, W, H, prog, ease_io, lerp, clamp, unit
import v60 as V

E.setup(7, "ສິລະປະ")
rng = np.random.default_rng(17)

# ---------------- Europe map (same look as the Mekong map story) ----------------
M.TEXA = np.asarray(Image.open("tex_europe_green.png").convert("RGB"))
M.A_LON0, M.A_LON1, M.A_LAT0, M.A_LAT1, M.A_PPD = -12.0, 30.0, 33.0, 58.0, 30.0
_cj = json.load(open("countries50.json"))
EU = ["Italy", "France", "Switzerland", "Austria", "Germany", "Spain", "Slovenia", "Croatia", "Portugal", "Belgium",
      "Netherlands", "Luxembourg", "United Kingdom", "Tunisia", "Algeria", "Bosnia and Herz.", "Hungary", "Czechia"]
M.POLY = {k: [np.array(r, float) for poly in _cj[k] for r in poly] for k in EU}
M.BORDER_SET = EU


def map_frame(v, fills, T):
    img = M.render_map(v)
    for name, a in fills.items():
        M.fill_country(img, v, name, a, T)
    M.borders(img, v, 0.4)
    return np.clip(img, 0, 255).astype(np.uint8)


def fv(lon, lat, span):
    return ("f", lon, lat, span)


def s_birth(u, T):
    k = ease_io(prog(u, 0.0, 0.75))
    v = fv(lerp(11.5, 11.0, k), lerp(45.0, 42.9, k), math.exp(lerp(math.log(34), math.log(13), k)))
    img = map_frame(v, {"Italy": 0.55 * prog(u, 0.1, 0.4)}, T)
    return img, {"view": v, "pins": [(10.93, 43.79, "ວິນຊີ (1452)", 0.35, "right"), (11.26, 43.77, "ຟລໍເຣນ", 0.6, "left")]}


def s_works(u, T):
    k = ease_io(prog(u, 0.0, 0.5))
    v = fv(lerp(11.0, 5.6, k), lerp(42.9, 46.4, k), math.exp(lerp(math.log(13), math.log(16), k)))
    img = map_frame(v, {"Italy": 0.3, "France": 0.3 * prog(u, 0.4, 0.7)}, T)
    return img, {"view": v, "pins": [(9.19, 45.46, "ມີລານ: ອາຫານຄ່ຳມື້ສຸດທ້າຍ", 0.3, "right"), (2.35, 48.86, "ປາຣີ: ໂມນາລີຊາ", 0.6, "right")]}


def s_france(u, T):
    k = ease_io(prog(u, 0.0, 0.6))
    v = fv(lerp(6.0, 5.0, k), lerp(46.0, 46.6, k), math.exp(lerp(math.log(15), math.log(13), k)))
    img = map_frame(v, {"France": 0.45, "Italy": 0.15}, T)
    # route Milan -> Amboise (1516)
    a, b = np.array([9.19, 45.46]), np.array([0.98, 47.41])
    q = ease_io(prog(u, 0.1, 0.6))
    pts = np.array([a + (b - a) * s + np.array([0, 1.4 * math.sin(math.pi * s)]) for s in np.linspace(0, q, 40)])
    x, y, _ = M.project(v, pts[:, 0], pts[:, 1])
    if q > 0:
        cv2.polylines(img, [np.round(np.stack([x, y], 1) * 16).astype(np.int32)], False, (140, 215, 255), 5, cv2.LINE_AA, shift=4)
    return img, {"view": v, "pins": [(9.19, 45.46, "ມີລານ", 0.0, "right"), (0.98, 47.41, "ອຳບົວສ໌ (1519)", 0.55, "left")]}


def pins_tag(base, info, T, w0, w1):
    if "view" not in info:
        return
    v = info["view"]
    for lon, lat, name, f, side in info["pins"]:
        M.pin(base, v, lon, lat, name, T, w0 + f * (w1 - w0), w1 - 0.05, side=side, size=38)


# ---------------- 3D objects ----------------
WOOD = np.array([150, 102, 58.0])
CLOTH = np.array([228, 212, 176.0])
PARCH = np.array([226, 206, 160.0])
SEPIA = (92, 62, 34)


def sky3d(top=(10, 16, 38), bot=(46, 52, 84)):
    return E.gradient(top, bot)


def _sketches():
    out = []
    t = np.linspace(0, 2 * np.pi, 40)
    for k in range(40):
        cx, cy, r = rng.uniform(0.3, 0.7), rng.uniform(0.3, 0.7), rng.uniform(0.12, 0.2)
        kind = k % 4
        if kind == 0:      # gear
            rr = r * (1 + 0.15 * (np.sin(t * 6) > 0))
            out.append(np.stack([cx + rr * np.cos(t), cy + rr * np.sin(t)], 1))
        elif kind == 1:    # wing curve
            x = np.linspace(0.15, 0.85, 30)
            out.append(np.stack([x, cy + 0.18 * np.sin((x - 0.15) * 4.5) * (1 - (x - 0.5) ** 2 * 3)], 1))
        elif kind == 2:    # spiral (water study)
            tt = np.linspace(0, 5 * np.pi, 60)
            out.append(np.stack([cx + 0.02 * tt * np.cos(tt) / 1.5, cy + 0.02 * tt * np.sin(tt) / 1.5], 1))
        else:              # pyramid
            out.append(np.array([[cx - r, cy - r], [cx, cy + r], [cx + r, cy - r], [cx - r, cy - r], [cx, cy - r * 0.4], [cx, cy + r]]))
    return out


SKETCH = _sketches()


def book(img, cam, open_k, flip, pos=(0, 0, 0), scale=1.0, L=None):
    """Open notebook: covers + fanned pages with sepia sketch strokes. flip 0..1 animates a page fan."""
    L = unit(-120, 55) if L is None else L
    P = np.asarray(pos, float)
    w, h = 1.0 * scale, 1.4 * scale
    ang = math.radians(lerp(90, 8, open_k))
    def page(theta, side, col, sk=None):
        # page hinged on the spine (y axis at x=0), rotated by theta from flat
        c, s = math.cos(theta), math.sin(theta)
        V = np.array([[0, -h / 2, 0], [side * w * c, -h / 2, w * s], [side * w * c, h / 2, w * s], [0, h / 2, 0]]) + P
        E.mesh(img, cam, V, [[0, 1, 2, 3]], col, L, 0.55, two_sided=True)
        if sk is not None:
            for st in sk[:2]:
                pts = np.array([[side * w * c * a, -h / 2 + h * b, w * s * a + 0.002] for a, b in st]) + P
                E.polyline(img, cam, pts, SEPIA, 2, alpha=0.8)
    page(ang, -1, WOOD * 0.8); page(ang, 1, WOOD * 0.8)                       # covers
    for i in range(10):
        th = ang + math.radians(1.2 * i)
        page(th, -1, PARCH * (0.94 + 0.006 * i), SKETCH[4:6] if i == 9 else None)
    for i in range(10):
        page(ang + math.radians(1.2 * i), 1, PARCH * (0.94 + 0.006 * i), SKETCH[(i * 2 + 1) % 40:(i * 2 + 1) % 40 + 2] if i == 9 else None)
    f = ease_io(flip)
    page(ang + math.radians(12) + (math.pi - 2 * ang - math.radians(24)) * f, 1, PARCH * 0.99, SKETCH[int(flip * 7) * 3 % 38: int(flip * 7) * 3 % 38 + 2])


def s_notebook(u, T):
    img = sky3d((26, 20, 18), (60, 44, 34)); g = E.Glow()
    cam = E.Cam((0, 0, 0.1), 3.4, -90 + 20 * math.sin(T * 0.3), 52, y0=860)
    E.grid(img, cam, 6, 0.25, -0.02, (246, 140, 38), 0.12)
    book(img, cam, 1.0, (T * 0.9) % 1.0)
    g.apply(img)
    return img, {"pages": int(10000 * ease_io(prog(u, 0.05, 0.85)))}


def s_mirror(u, T):
    img, info = s_notebook(0.0, T)
    img = (img.astype(np.float32) * 0.55).astype(np.uint8)
    return img, {"mirror": ease_io(prog(u, 0.35, 0.75))}


def mirror_panel(base, info, T, w0, w1):
    if "mirror" not in info:
        return
    k = info["mirror"]
    a = C.fade(T, w0 + 0.1, w1 - 0.05, 0.3, 0.3)
    if a <= 0:
        return
    pw, ph = 860, 360
    card = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, pw - 1, ph - 1), 24, fill=(226, 206, 160, 255), outline=(150, 102, 58, 255), width=5)
    txt = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    dt = ImageDraw.Draw(txt)
    from common import font
    f1 = font("lat", 74, 400)
    for i, line in enumerate(["Leonardo", "da Vinci"]):
        dt.text((pw / 2, 120 + i * 110), line, font=f1, fill=(92, 62, 34, 255), anchor="mm")
    sx = math.cos(math.pi * (1 - k))           # -1 (mirrored) -> +1 (readable)
    wq = max(2, int(pw * abs(sx)))
    t2 = txt.resize((wq, ph))
    if sx < 0:
        t2 = t2.transpose(Image.FLIP_LEFT_RIGHT)
    card.alpha_composite(t2, ((pw - wq) // 2, 0))
    lay = M.layer(); lay.alpha_composite(card, ((W - pw) // 2, 520))
    M.put(base, lay, a)


HEART_PATH = None


def s_heart(u, T):
    img = E.gradient((24, 10, 14), (60, 22, 28)); g = E.Glow()
    cam = E.Cam((0, 0, 0), 5.2, -90 + 25 * math.sin(T * 0.4), 8, y0=860)
    beat = 1 + 0.07 * max(0, math.sin(T * 2 * math.pi * 1.1)) ** 4
    Lv = cam.view(unit(-120, 45))
    loops = []
    for sgn in (-1, 1):   # simplified two-circuit loop (body / lungs)
        th = np.linspace(0, 2 * np.pi, 120)
        loops.append(np.stack([sgn * (0.9 + 0.9 * (1 - np.cos(th)) / 2) * 1.1, 0.25 * np.sin(th), 1.0 * np.sin(th) * 0.9], 1) * np.array([1, 1, 1]))
    for lp, col in zip(loops, ((120, 160, 255), (255, 90, 80))):
        E.polyline(img, cam, lp, col, 6, alpha=0.6, closed=True)
        n = len(lp)
        for k in range(10):
            idx = int(((T * 0.35 + k / 10) % 1.0) * n)
            x, y, z = cam.proj(lp[idx])
            g.dot(x[0], y[0], 16, col, 1.4)
    parts = [((-0.22, 0, 0.12), 0.55, (200, 40, 50)), ((0.25, 0.05, 0.1), 0.5, (185, 35, 45)), ((0, 0, -0.32), 0.42, (175, 30, 40))]
    items = []
    for c, r, col in parts:
        x, y, z = cam.proj(np.array(c) * beat)
        items.append((z[0], x[0], y[0], cam.f * r * beat / z[0], col))
    for z, x, y, R, col in sorted(items, key=lambda a: -a[0]):
        E.sphere(img, x, y, R, col, Lv, 0.35, 0.5)
    xc, yc, _ = cam.proj([0, 0, 0])
    g.dot(xc[0], yc[0], 260 * (beat - 0.95), (255, 60, 60), 0.8)
    g.apply(img)
    return img, {"heart": (xc[0], yc[0])}


def ornithopter(img, cam, T, pos=(0, 0, 0), scale=1.0, L=None, flap_speed=1.3):
    L = unit(-120, 55) if L is None else L
    P = np.asarray(pos, float)
    s = scale
    flap = math.radians(32) * math.sin(T * 2 * math.pi * flap_speed)
    A, B = [], []
    # fuselage beam + pilot frame
    A += [P + [-1.2 * s, 0, 0]]; B += [P + [1.6 * s, 0, 0]]
    A += [P + [0, 0, 0], P + [0.4 * s, 0, 0]]; B += [P + [0.2 * s, 0, -0.6 * s], P + [0.2 * s, 0, -0.6 * s]]
    A += [P + [1.6 * s, 0, 0]]; B += [P + [2.1 * s, 0, 0.15 * s]]                         # tail
    for side in (-1, 1):
        ribs = []
        for i in range(6):
            r = (0.6 + 0.62 * i) * s
            x = (0.6 - 0.12 * i) * s
            yy = side * r * math.cos(flap * (0.4 + 0.12 * i))
            zz = r * math.sin(flap * (0.4 + 0.12 * i)) + 0.05 * s
            tip = P + np.array([x - 1.7 * s * (i / 5) ** 1.3, yy, zz])
            ribs.append(tip)
            A.append(P + [0.3 * s, side * 0.15 * s, 0.05 * s]); B.append(tip)
        root = P + np.array([0.3 * s, side * 0.15 * s, 0.05 * s])
        for i in range(5):
            E.mesh(img, cam, np.array([root, ribs[i], ribs[i + 1]]), [[0, 1, 2]], CLOTH * (0.9 + 0.02 * i), L, 0.5, two_sided=True)
        for i in range(5):
            A.append(ribs[i]); B.append(ribs[i + 1])
    E.lines(img, cam, np.array(A), np.array(B), WOOD, width_world=0.05 * s, wmin=2, wmax=8)


CLOUDS = rng.uniform(-1, 1, (26, 3))


def clouds(img, g, cam, T, speed=0.0, spread=40, base=(0, 0, 0)):
    for a, b, c in CLOUDS:
        p = np.array(base) + np.array([a * spread, b * spread * 0.5 + 10, ((c * spread + T * speed) % (2 * spread)) - spread])
        x, y, z = cam.proj(p)
        if z[0] > 1:
            g.dot(x[0], y[0], cam.f * 1.0 / z[0], (220, 228, 245), 0.3)


def s_flight(u, T):
    img = sky3d((30, 60, 120), (150, 170, 210)); g = E.Glow()
    cam = E.Cam((-0.3, 0, 0.2), 10.5, 215 + 15 * math.sin(T * 0.5), 58, y0=840)
    clouds(img, g, cam, T, speed=0)
    ornithopter(img, cam, T, (0, 0, 0.15 * math.sin(T * 2)), 1.0)
    g.apply(img)
    return img, {}


def parachute(img, cam, pos, s=1.0, sway=0.0, L=None):
    L = unit(-120, 55) if L is None else L
    P = np.asarray(pos, float)
    h, half = 3.4 * s, 1.75 * s
    apex = P + [0, 0, h]
    c = [P + [dx * half, dy * half, 0] for dx, dy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    for i in range(4):
        E.mesh(img, cam, np.array([apex, c[i], c[(i + 1) % 4]]), [[0, 1, 2]], CLOTH * (0.9 + 0.04 * i), L, 0.5, two_sided=True)
    A = [apex] * 4 + c; B = c + [c[1], c[2], c[3], c[0]]
    E.lines(img, cam, np.array(A), np.array(B), WOOD, width_world=0.06 * s, wmin=2, wmax=7)
    harness = P + [sway, 0, -2.6 * s]
    E.lines(img, cam, np.array(c), np.array([harness] * 4), (210, 200, 180), width_px=2)
    # small figure under the harness (stick figure)
    hd = harness + [0, 0, -0.2 * s]
    fig = [(hd, hd + [0, 0, -0.8 * s]), (hd + [0, 0, -0.8 * s], hd + [0.25 * s, 0, -1.5 * s]), (hd + [0, 0, -0.8 * s], hd + [-0.25 * s, 0, -1.5 * s]),
           (hd + [0, 0, -0.25 * s], harness + [0.3 * s, 0, 0.1]), (hd + [0, 0, -0.25 * s], harness + [-0.3 * s, 0, 0.1])]
    E.lines(img, cam, np.array([a for a, b in fig]), np.array([b for a, b in fig]), (40, 46, 64), width_world=0.09 * s, wmin=2, wmax=8)
    x, y, z = cam.proj(hd + [0, 0, 0.12 * s])
    if z[0] > 0:
        cv2.circle(img, E._pt(x[0], y[0]), int(cam.f * 0.16 * s / z[0] * 16), (40, 46, 64), -1, cv2.LINE_AA, shift=4)


def s_parachute(u, T):
    img = sky3d((40, 80, 150), (170, 190, 225)); g = E.Glow()
    alt = 3000 * (1 - 0.55 * u)
    cam = E.Cam((0, 0, 0.5), 11, -80 + 15 * math.sin(T * 0.5), 6, y0=820)
    for a, b, c in CLOUDS:                      # clouds stream upward = we are falling
        p = np.array([a * 18, 12 + b * 6, ((c * 30 + T * 6) % 60) - 30])
        x, y, z = cam.proj(p)
        if z[0] > 1:
            g.dot(x[0], y[0], cam.f * 1.0 / z[0], (230, 236, 248), 0.3)
    parachute(img, cam, (0, 0, 0.8 + 0.2 * math.sin(T * 1.2)), 1.0, sway=0.15 * math.sin(T * 1.4))
    g.apply(img)
    return img, {"alt": alt}


def s_hero(u, T):
    img = sky3d(); g = E.Glow()
    cam = E.Cam((0, 0, 0.8), 9.5, -90 + T * 8, 12, y0=920)
    E.grid(img, cam, 20, 1.0, -2.2, (246, 140, 38), 0.18)
    book(img, cam, 1.0, (T * 0.5) % 1.0, pos=(0, 0, -2.1), scale=1.6)
    ornithopter(img, cam, T, (-1.6, 0.8, 2.2), 0.75)
    parachute(img, cam, (2.4, -0.5, 0.6 + 0.3 * math.sin(T)), 0.55, sway=0.1 * math.sin(T))
    g.apply(img)
    return img, {}


import os
R3D = "/home/claude/statue/frames"
_need = []
_RU = [None]


def r3d(name, post=None):
    def fn(u, T):
        f = int(round(T * 30))
        p = f"{R3D}/{name}_{f:05d}.jpg"
        if _RU[0] is not None:
            p = _RU[0].path(name, float(u), T) or p
        _need.append(dict(out=p, scene=name, t=round(T, 4), u=round(float(u), 4)))
        if os.path.exists(p):
            img = np.asarray(Image.open(p).convert("RGB")).copy()
        else:
            img = np.zeros((H, W, 3), np.uint8)
        info = {}
        if post:
            img, info = post(img, u, T)
        return img, info
    fn.__name__ = "r3d_" + name
    return fn


def _mirror_post(img, u, T):
    return img, {"mirror": ease_io(prog(u, 0.35, 0.75))}


def _note_post(img, u, T):
    return img, {"pages": int(10000 * ease_io(prog(u, 0.05, 0.85)))}


ORANGE = M.ORANGE
BEATS = [
    dict(vo="[excited] ຈິດຕະກອນ ວິສະວະກອນ ແລະ ນັກວິທະຍາສາດ ໃນຄົນດຽວ: ເລໂອນາໂດ ດາວິນຊີ!", src=("new", r3d("hero")), pill="ເປີດເລື່ອງ",
         head=("ເລໂອນາໂດ ດາວິນຊີ", "ອັດສະລິຍະ ທີ່ເກັ່ງທຸກດ້ານ!"), hs1=80, hs2=60, captions=False),
    dict(vo="ເກີດປີ 1452 ທີ່ເມືອງວິນຊີ ອິຕາລີ ອາຍຸ 15 ປີ ໄປຮຽນແຕ້ມຮູບ ທີ່ຟລໍເຣນ.", src=("new", s_birth), pill="ຊີວິດ",
         tags=[pins_tag], cards=[("ເກີດ", "15 ເມສາ 1452", "star", 0.15), ("ອາຍຸ 15 ປີ", "ຮຽນແຕ້ມທີ່ ຟລໍເຣນ", "people", 0.55)]),
    dict(vo="ລາວແຕ້ມ ອາຫານຄ່ຳມື້ສຸດທ້າຍ ແລະ ໂມນາລີຊາ ທີ່ດັງກ້ອງໂລກ.", src=("new", s_works), pill="ຜົນງານ",
         tags=[pins_tag], cards=[("ອາຫານຄ່ຳມື້ສຸດທ້າຍ", "1495–1498", "flag", 0.2), ("ໂມນາລີຊາ", "ລູບ, ປາຣີ", "star", 0.6)]),
    dict(vo="ແຕ່ລາວຍັງຂຽນບັນທຶກ ແລະແບບແຕ້ມ ກວ່າ 10,000 ໜ້າ.", src=("new", r3d("notebook", _note_post)), pill="ບັນທຶກ",
         cards=[("ບັນທຶກ ແລະ ແບບແຕ້ມ", lambda i, T: f"{i.get('pages', 10000):,} ໜ້າ", "clock", 0.05)]),
    dict(vo="ຂຽນດ້ວຍມືຊ້າຍ ແບບປີ້ນກັບ ຕ້ອງສ່ອງແວ່ນຈຶ່ງອ່ານອອກ!", src=("new", r3d("mirror", _mirror_post)), pill="ບັນທຶກ",
         tags=[mirror_panel], cards=[("ຖະນັດ", "ມືຊ້າຍ", "people", 0.1), ("ຂຽນແບບ", "ສ່ອງແວ່ນ", "star", 0.5)]),
    dict(vo="ລາວຜ່າສົບສຶກສາ ປະມານ 30 ສົບ ແລະເຂົ້າໃຈວ່າ ຫົວໃຈເຮັດວຽກຄືປໍ້າ.", src=("new", r3d("heart")), pill="ກາຍວິພາກ",
         cards=[("ຜ່າສົບສຶກສາ", "ປະມານ 30 ສົບ", "people", 0.15), ("ຫົວໃຈ", "= ປໍ້າ", "bolt", 0.6)]),
    dict(vo="ຂຽນເລື່ອງການບິນ ກວ່າ 35,000 ຄຳ ແລະ 500 ຮູບ ກ່ອນມີເຮືອບິນ 400 ປີ.", src=("new", r3d("flight")), pill="ການບິນ",
         cards=[("ເລື່ອງການບິນ", "35,000+ ຄຳ", "ruler", 0.15), ("ຮູບແຕ້ມ", "500 ຮູບ", "star", 0.5)]),
    dict(vo="ຮົ່ມຊູຊີບຊົງປີຣາມິດ ຂອງລາວ ປີ 2000 ມີຄົນສ້າງແລ້ວລອງໂດດ ມັນລອຍລົງມາໄດ້ແທ້!", src=("new", r3d("parachute")), pill="ຮົ່ມຊູຊີບ",
         cards=[("ອອກແບບ", "ຮົ່ມຊູຊີບ ຊົງປີຣາມິດ", "flag", 0.1), ("ປີ 2000 ລອງໂດດ", "ລອຍລົງໄດ້ແທ້!", "rank", 0.55)]),
    dict(vo="ລາວເສຍຊີວິດປີ 1519 ທີ່ຝຣັ່ງ ແຕ່ຄວາມຄິດຂອງລາວ ຍັງຢູ່ມາຮອດທຸກວັນນີ້.", src=("new", s_france), pill="ມໍລະດົກ",
         tags=[pins_tag], cards=[("ເສຍຊີວິດ", "2 ພຶດສະພາ 1519", "flag", 0.25), ("ອາຍຸ", "67 ປີ", "clock", 0.55)]),
    dict(vo="[curious] ເຈົ້າວ່າ ດາວິນຊີ ເກັ່ງດ້ານໃດທີ່ສຸດ? ຄອມເມັ້ນບອກແດ່!", src=("new", r3d("hero")), pill="ບອກຕໍ່",
         head=("ດາວິນຊີ ເກັ່ງດ້ານໃດທີ່ສຸດ?", "ຄອມເມັ້ນບອກແດ່!"), hs1=70, hs2=62),
    dict(vo="[happy] ຖ້າຮູ້ແລ້ວ ຢ່າລືມ ບອກຕໍ່ ໃຫ້ໝູ່ເດີ້!", src=("new", r3d("hero")), pill="ບອກຕໍ່",
         head=("ດາວິນຊີ ເກັ່ງດ້ານໃດທີ່ສຸດ?", "ຄອມເມັ້ນບອກແດ່!"), hs1=70, hs2=62, captions=False, share=True),
]

SHOW = V.Show(BEATS, None, timing_path="out60/EP07_timing.json", min_total=58)
if os.environ.get('REUSE') == '1':
    import reuse3d
    _RU[0] = reuse3d.Reuse(BEATS, '/home/claude/statue/jobs7.json', 58, SHOW)

if __name__ == "__main__":
    import sys
    if sys.argv[1] == "--jobs":
        n = int(round(SHOW.total * 30))
        for fi in range(n):
            T = fi / 30
            i = SHOW.idx(T)
            w0, w1 = SHOW.w0[i], SHOW.w1[i]
            src = SHOW.beats[i]["src"]
            if src[1].__name__.startswith("r3d"):
                src[1]((T - w0) / max(1e-6, w1 - w0), T)
            if i + 1 < len(SHOW.beats) and T > w1 - V.XF:
                s2 = SHOW.beats[i + 1]["src"]
                if s2[1].__name__.startswith("r3d"):
                    s2[1](0.0, T)
        seen, jobs = set(), []
        for j in _need:
            if j["out"] not in seen:
                seen.add(j["out"]); jobs.append(j)
        json.dump(jobs, open(sys.argv[2], "w")); print("jobs", len(jobs)); sys.exit()
    V.main(SHOW, "ຂໍ້ມູນ: Britannica, Royal Collection Trust, Smithsonian NASM  |  ພາບປະກອບ 3D", "h7")
