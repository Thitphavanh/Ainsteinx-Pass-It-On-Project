"""EP.4 (3D) ວິສະວະກຳ — ຍອດຫໍໄອເຟລ ເຄື່ອນຕາມດວງອາທິດ. 41 s."""
import math
import numpy as np, cv2
from PIL import Image
import eng3d as E
from eng3d import M, C, W, H, prog, ease_io, lerp, clamp, unit

DUR = 41.0
E.setup(4, "ວິສະວະກຳ")
IRON = np.array([170, 116, 68.0])
LIT = np.array([255, 196, 120.0])
HOT = np.array([255, 120, 40.0])

ZS = [0, 57, 116, 190, 276, 300, 312]
WS = [62.5, 36, 20, 10, 4.5, 3, 0.6]


def wz(z): return float(np.interp(z, ZS, WS))
def legw(z): return float(np.interp(z, [0, 57, 116], [17, 10, 0]))


def tower_segments(grow=0.0, lean=np.zeros(2), sun_h=None, heat=0.0):
    """Return A, B, colours, widths for the lattice tower."""
    A, B, N = [], [], []

    def P(sx, sy, z, inset=0.0):
        w = wz(z) - inset
        off = lean * (z / 312) ** 2
        return np.array([sx * w + off[0], sy * w + off[1], z * (1 + grow)])

    levels = np.concatenate([np.linspace(0, 57, 6), np.linspace(57, 116, 6)[1:], np.linspace(116, 300, 13)[1:]])
    corners = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    faces = [((1, 1), (1, -1), (1, 0)), ((-1, 1), (-1, -1), (-1, 0)), ((1, 1), (-1, 1), (0, 1)), ((1, -1), (-1, -1), (0, -1))]
    W_ = []
    for i in range(len(levels) - 1):
        z0, z1 = levels[i], levels[i + 1]
        for sx, sy in corners:   # main legs
            A.append(P(sx, sy, z0)); B.append(P(sx, sy, z1)); N.append((sx * .7, sy * .7)); W_.append(3.2)
            if z1 <= 116:            # inner edges of the four separate legs
                lw0, lw1 = legw(z0), legw(z1)
                for ix, iy in ((lw0, 0), (0, lw0), (lw0, lw0)):
                    pass
                a = P(sx, sy, z0, 0); b = P(sx, sy, z1, 0)
                ai = a - np.array([sx * lw0, sy * lw0, 0]); bi = b - np.array([sx * lw1, sy * lw1, 0])
                ax = a - np.array([sx * lw0, 0, 0]); bx = b - np.array([sx * lw1, 0, 0])
                ay = a - np.array([0, sy * lw0, 0]); by = b - np.array([0, sy * lw1, 0])
                for p, q in ((ai, bi), (ax, bx), (ay, by)):
                    A.append(p); B.append(q); N.append((sx * .7, sy * .7)); W_.append(1.8)
                for p, q in ((a, bx), (ax, b), (a, by), (ay, b)):
                    A.append(p); B.append(q); N.append((sx * .7, sy * .7)); W_.append(0.9)
        if z0 >= 57 or True:
            for c0, c1, n in faces:
                if z1 <= 57:
                    continue
                a0, b0 = P(*c0, z0), P(*c1, z0)
                a1, b1 = P(*c0, z1), P(*c1, z1)
                A += [a0, b0]; B += [b1, a1]; N += [n, n]; W_ += [1.1, 1.1]
                A.append(a1); B.append(b1); N.append(n); W_.append(0.8)
    # arches on each face under the first platform
    for c0, c1, n in faces:
        a, b = P(*c0, 0), P(*c1, 0)
        s = np.linspace(0.12, 0.88, 22)
        pts = [a + (b - a) * u + np.array([0, 0, 39 * math.sin(math.pi * (u - 0.12) / 0.76) + 4]) for u in s]
        for p, q in zip(pts, pts[1:]):
            A.append(p); B.append(q); N.append(n); W_.append(1.6)
    # antenna
    top = P(0, 0, 300) * np.array([1, 1, 1]); top[:2] = lean
    A.append(np.array([lean[0], lean[1], 300 * (1 + grow)])); B.append(np.array([lean[0] * 1.08, lean[1] * 1.08, 330 * (1 + grow)])); N.append((0, 0)); W_.append(1.6)
    A, B = np.array(A), np.array(B)
    N = np.array(N, float)
    cols = np.tile(IRON, (len(A), 1))
    if sun_h is not None:
        f = np.clip(N @ sun_h, 0, 1)[:, None]
        cols = IRON + (LIT - IRON) * f * 0.8
        cols = cols + (HOT - cols) * f * heat * 0.6
    return A, B, cols, np.array(W_), N


def platforms(grow, lean):
    out = []
    for z, w, t in ((57, 36, 6), (116, 20, 5), (276, 4.5, 4)):
        off = lean * (z / 312) ** 2
        out.append(E.box((off[0], off[1], z * (1 + grow)), (2 * w + 10, 2 * w + 10, t)))
    return out


def sky():
    img = E.gradient((7, 12, 30), (30, 40, 72))
    return img


def sun_dir(az, el):
    return unit(az, el)


def draw_tower(img, cam, grow=0.0, lean=np.zeros(2), sun=None, heat=0.0, glow=None, alpha=1.0):
    sun_h = None if sun is None else sun[:2] / (np.linalg.norm(sun[:2]) + 1e-9)
    A, B, cols, Wd, N = tower_segments(grow, lean, sun_h, heat)
    L = sun if sun is not None else unit(-130, 45)
    for V, Fc in platforms(grow, lean):
        E.mesh(img, cam, V, Fc, (200, 140, 80), L, 0.45)
    # draw lines with per-segment width
    xa, ya, za = cam.proj(A); xb, yb, zb = cam.proj(B)
    order = np.argsort(-(za + zb))
    for i in order:
        if za[i] <= 1 or zb[i] <= 1:
            continue
        w = clamp(cam.f * Wd[i] / ((za[i] + zb[i]) / 2), 1, 9)
        cv2.line(img, E._pt(xa[i], ya[i]), E._pt(xb[i], yb[i]), tuple(float(c) for c in cols[i]), max(1, int(round(w))), cv2.LINE_AA, shift=4)
    if glow is not None and sun_h is not None and heat > 0:
        f = np.clip(N @ sun_h, 0, 1)
        for i in np.nonzero(f > 0.5)[0][::2]:
            glow.line((xa[i], ya[i]), (xb[i], yb[i]), 10, (255, 110, 30), 0.35 * heat * f[i])
    tip = np.array([lean[0] * 1.08, lean[1] * 1.08, 330 * (1 + grow)])
    return tip


def ground(img, cam, alpha=0.22):
    E.grid(img, cam, 420, 30, 0, (246, 140, 38), alpha)


def draw_sun(img, glow, cam, sdir):
    p = cam.pos + sdir * 5000
    x, y, z = cam.proj(p)
    if z[0] > 0:
        glow.dot(x[0], y[0], 140, (255, 140, 40), 1.2)
        glow.dot(x[0], y[0], 60, (255, 210, 120), 1.6)
        E.sphere(img, x[0], y[0], 30, (255, 230, 170), np.array([0, 0, 1.0]), 1.0, 0.0)
    return x[0], y[0], z[0]


# ---------------- scenes ----------------
def s_tower_intro(t):
    img = sky(); g = E.Glow()
    yaw = 20 + t * 9
    dist = 600 if t < 3.0 else lerp(600, 120, ease_io(prog(t, 3.0, 3.8)))
    cam = E.Cam((0, 0, 150 if t < 3 else lerp(150, 120, prog(t, 3, 3.8))), dist, yaw, 8)
    sd = sun_dir(yaw - 140, 28)
    draw_sun(img, g, cam, sd)
    ground(img, cam)
    draw_tower(img, cam, sun=sd, heat=0.2, glow=g)
    g.apply(img)
    return img, {}


rng = np.random.default_rng(3)
LAT = np.array([[i, j, k] for i in range(-3, 3) for j in range(-3, 3) for k in range(-3, 3)], float) + 0.5
PH = rng.uniform(0, 2 * np.pi, (len(LAT), 3))


def s_lattice(t):
    img = E.gradient((10, 12, 26), (26, 20, 30)); g = E.Glow()
    heat = ease_io(prog(t, 5.8, 7.6))
    a = 1.0 + 0.10 * heat
    amp = 0.04 + 0.10 * heat
    w = 9 + 10 * heat
    P = LAT * a + amp * np.sin(t * w + PH)
    cam = E.Cam((0, 0, 0), lerp(9, 13.5, ease_io(prog(t, 3.4, 6.0))), 35 + t * 7, 22)
    x, y, z = cam.proj(P)
    order = np.argsort(-z)
    col = np.array([150, 160, 182.0]) + (np.array([255, 150, 70.0]) - np.array([150, 160, 182.0])) * heat
    Lv = cam.view(unit(-120, 50))
    # bonds
    A, B = [], []
    idx = {tuple(v): n for n, v in enumerate(LAT)}
    for n, v in enumerate(LAT):
        for d in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            m = idx.get(tuple(v + d))
            if m is not None:
                A.append(P[n]); B.append(P[m])
    E.lines(img, cam, np.array(A), np.array(B), col * 0.55, width_px=3)
    for i in order:
        R = cam.f * 0.28 / z[i]
        E.sphere(img, x[i], y[i], R, col, Lv, 0.3, 0.5)
        if heat > 0.05:
            g.dot(x[i], y[i], R * 1.6, (255, 100, 30), 0.25 * heat)
    g.apply(img)
    return img, {"heat": heat}


def s_grow(t):
    img = sky(); g = E.Glow()
    cam = E.Cam((0, 0, 165), 600, -90 + (t - 9) * 2, 8)
    sd = unit(-60, 50)
    draw_sun(img, g, cam, sd)
    ground(img, cam)
    grow = 0.07 * ease_io(prog(t, 9.8, 11.6))
    tip = draw_tower(img, cam, grow=grow, sun=sd, heat=0.5 * prog(t, 9.8, 11.6), glow=g)
    info = {}
    if grow > 0.002:   # ghost of the old top + dimension
        x0, y0, _ = cam.proj([[-40, 0, 330], [40, 0, 330]])
        cv2.line(img, E._pt(x0[0], y0[0]), E._pt(x0[1], y0[1]), (220, 230, 255), 2, cv2.LINE_AA, shift=4)
        xt, yt, _ = cam.proj(tip)
        ax = x0[1] + 40
        cv2.arrowedLine(img, E._pt(ax, y0[0]), E._pt(ax, yt[0]), (120, 210, 255), 4, cv2.LINE_AA, shift=4, tipLength=0.25)
        info["dim"] = (ax + 20, (y0[0] + yt[0]) / 2)
    g.apply(img)
    return img, info


def s_lean(t):
    img = sky(); g = E.Glow()
    cam = E.Cam((0, 0, 170), 640, -90, 8)
    sd = unit(62, 22)                            # sun on +x  (screen right)
    sx, sy, _ = draw_sun(img, g, cam, sd)
    ground(img, cam)
    heat = ease_io(prog(t, 13.5, 15.5))
    lean = -26.0 * np.array([math.cos(math.radians(62)), math.sin(math.radians(62))]) * ease_io(prog(t, 15.0, 18.5))
    tip = draw_tower(img, cam, lean=lean, sun=sd, heat=heat, glow=g)
    # sun rays
    if heat > 0:
        for k in range(7):
            yy = 560 + k * 110
            g.line((sx, sy), (W * 0.7, yy), 6, (255, 170, 60), 0.25 * heat)
    xt, yt, _ = cam.proj(tip)
    info = {"tip": (xt[0], yt[0]), "lean": lean[0] * 2}
    if lean[0] < -2:
        cv2.arrowedLine(img, E._pt(xt[0] + 90, yt[0] + 40), E._pt(xt[0] - 60, yt[0] + 40), (120, 210, 255), 5, cv2.LINE_AA, shift=4, tipLength=0.3)
    g.apply(img)
    return img, info


SUN_AZ0, SUN_AZ1 = 0.0, -180.0


def s_trace(t):
    img = sky(); g = E.Glow()
    u = ease_io(prog(t, 21.0, 22.8))
    cam = E.Cam((0, 0, lerp(170, 300, u)), lerp(640, 560, u), lerp(-90, -120, u) + (t - 21) * 2, lerp(8, 38, u))
    ground(img, cam, 0.18)
    k = prog(t, 22.4, 26.4)
    az = lerp(SUN_AZ0, SUN_AZ1, k)
    el = 20 + 45 * math.sin(math.pi * k)
    sd = unit(az, el)
    draw_sun(img, g, cam, sd)
    LEAN = 26.0
    lean = -LEAN * np.array([math.cos(math.radians(az)), math.sin(math.radians(az))])
    tip = draw_tower(img, cam, lean=lean, sun=sd, heat=1.0, glow=g)
    # trace of the tip so far
    ks = np.linspace(0, k, max(2, int(60 * k) + 2))
    pts = [[-LEAN * 1.08 * math.cos(math.radians(lerp(SUN_AZ0, SUN_AZ1, q))), -LEAN * 1.08 * math.sin(math.radians(lerp(SUN_AZ0, SUN_AZ1, q))), 330] for q in ks]
    if k > 0:
        E.polyline(img, cam, np.array(pts), (60, 150, 255), 6)
        x, y, _ = cam.proj(np.array(pts))
        for a, b in zip(zip(x, y), list(zip(x, y))[1:]):
            g.line(a, b, 16, (40, 120, 255), 0.6)
    xt, yt, _ = cam.proj(tip)
    g.dot(xt[0], yt[0], 26, (150, 220, 255), 1.6)
    g.apply(img)
    return img, {"tip": (xt[0], yt[0])}


def bridge_geom(gap):
    parts = []
    L = 40.0
    for s in (-1, 1):
        cx = s * (L / 2 + gap / 2)
        parts.append((E.box((cx, 0, 8), (L, 12, 1.6)), (120, 128, 140)))          # deck
        parts.append((E.box((cx, 0, 9.0), (L, 11, 0.25)), (60, 64, 72)))           # asphalt
        parts.append((E.box((s * (L + gap / 2) - s * 3, 0, 3.6), (3, 8, 7.2)), (90, 96, 110)))  # pier
    # finger plates of the joint
    for i in range(-5, 6):
        y = i * 1.0
        parts.append((E.box((-gap / 2 - 0.4 + (0.6 if i % 2 else 0), y, 9.2), (0.8 + (1.2 if i % 2 else 0), 0.45, 0.12)), (150, 156, 168)))
        parts.append((E.box((gap / 2 + 0.4 - (0.6 if not i % 2 else 0), y, 9.2), (0.8 + (1.2 if not i % 2 else 0), 0.45, 0.12)), (150, 156, 168)))
    return parts


def s_bridge(t):
    img = E.gradient((12, 18, 40), (40, 46, 74)); g = E.Glow()
    close = ease_io(prog(t, 31.0, 33.0))
    cam = E.Cam((0, 0, lerp(7, 9, close)), lerp(52, 13, close), lerp(-62, -40, close) + (t - 27) * 1.5, lerp(16, 34, close))
    sd = unit(-30, 40)
    draw_sun(img, g, cam, sd)
    ground(img, cam, 0.15)
    heat = 0.5 + 0.5 * math.sin((t - 27.5) * 1.3)
    gap = lerp(1.6, 0.35, heat)
    for (V, Fc), col in bridge_geom(gap):
        E.mesh(img, cam, V, Fc, col, sd, 0.4)
    # lane dashes
    A = np.array([[x, 0, 9.14] for x in np.arange(-38, 38, 4.0) if abs(x) > 2])
    E.lines(img, cam, A, A + np.array([2.0, 0, 0]), (230, 220, 180), width_world=0.18, wmax=8)
    x, y, _ = cam.proj([0, -6.5, 9.3])
    g.apply(img)
    return img, {"gap": (x[0], y[0]), "heat": heat}


def s_outro(t):
    img = sky(); g = E.Glow()
    yaw = 60 + (t - 36) * 10
    cam = E.Cam((0, 0, 165), lerp(900, 620, ease_io(prog(t, 36.3, 38))), yaw, 10)
    sd = sun_dir(yaw - 150, 30)
    draw_sun(img, g, cam, sd)
    ground(img, cam)
    draw_tower(img, cam, sun=sd, heat=0.3, glow=g)
    g.apply(img)
    return img, {}


SCENES = [(0, 3.6, s_tower_intro), (3.6, 9.0, s_lattice), (9.0, 13.0, s_grow), (13.0, 21.0, s_lean),
          (21.0, 27.0, s_trace), (27.0, 36.4, s_bridge), (36.4, 41.1, s_outro)]
XF = 0.35


def world(t):
    for i, (a, b, fn) in enumerate(SCENES):
        if a <= t < b:
            img, info = fn(t)
            if i + 1 < len(SCENES) and t > b - XF:
                img2, _ = SCENES[i + 1][2](t)
                img = E.blend(img, img2, (t - (b - XF)) / XF)
            return img, info, fn.__name__
    return SCENES[-1][2](t) + (SCENES[-1][2].__name__,)


def frame(t):
    img, info, sc = world(t)
    base = Image.fromarray(img).convert("RGBA")
    M.brand(base)
    for txt, a, b in [("ເປີດເລື່ອງ", 0.2, 3.4), ("ເຫຼັກ", 3.7, 8.9), ("ສູງຂຶ້ນ", 9.1, 12.9), ("ອ່ຽງໜີແດດ", 13.1, 20.9),
                      ("ຕາມດວງອາທິດ", 21.1, 26.9), ("ວິສະວະກຳ", 27.1, 36.3), ("ບອກຕໍ່", 36.6, 41.5)]:
        M.pill(base, txt, t, a, b)
    E.headline(base, t, 0.2, 3.4, "ຍອດຫໍໄອເຟລ", "ເຄື່ອນທີ່ທຸກມື້ ຕາມດວງອາທິດ!", y=430, s1=84, s2=62)
    M.caption(base, "ຫໍໄອເຟລເຮັດຈາກເຫຼັກ", t, 3.7, 6.3)
    M.caption(base, "ເຫຼັກ ຈະຂະຫຍາຍຕົວ ເມື່ອຖືກຄວາມຮ້ອນ", t, 6.3, 8.9)
    M.card(base, t, 4.2, 8.9, 285, 480, "ໂຄງສ້າງເຫຼັກ", "7,300 ໂຕນ", "mountain")
    M.card(base, t, 6.5, 8.9, 795, 480, "ຮ້ອນຂຶ້ນ", "ຂະຫຍາຍຕົວ", "ruler")
    if sc == "s_lattice" and 6.0 < t < 8.9:
        E.tag(base, W / 2, 330, "ອາຕອມເຫຼັກ ສັ່ນແຮງຂຶ້ນ ແລະ ຫ່າງກັນອອກ", t, 6.0, 8.8, size=40, col=(255, 200, 140))
    M.caption(base, "ໃນມື້ຮ້ອນ ຫໍຈະສູງຂຶ້ນຫຼາຍມິນລີແມັດ", t, 9.1, 12.9)
    if "dim" in info:
        E.tag(base, info["dim"][0] + 120, info["dim"][1] + 14, "+ ຫຼາຍ ມມ.", t, 10.0, 12.9, size=44, col=(140, 215, 255))
    M.card(base, t, 9.6, 12.9, W / 2, 600, "ມື້ຮ້ອນ ຫໍສູງຂຶ້ນ", "+ ຫຼາຍ ມິນລີແມັດ", "ruler")
    M.caption(base, "ແດດສ່ອງພຽງດ້ານດຽວ ດ້ານນັ້ນຈຶ່ງຂະຫຍາຍຫຼາຍກວ່າ", t, 13.1, 17.0)
    M.caption(base, "ເຮັດໃຫ້ຍອດຫໍ ອ່ຽງໜີແດດ", t, 17.0, 20.9)
    if sc == "s_lean" and info.get("lean", 0) < -3:
        x, y = info["tip"]
        E.tag(base, x, y - 40, "ອ່ຽງໜີແດດ", t, 16.0, 20.8, size=46, col=(140, 215, 255))
    M.card(base, t, 13.6, 20.9, 285, 480, "ດ້ານຖືກແດດ", "ຮ້ອນ ຂະຫຍາຍ", "sun")
    M.card(base, t, 15.2, 20.9, 795, 480, "ດ້ານຮົ່ມ", "ເຢັນ ຂະຫຍາຍໜ້ອຍ", "flag")
    M.caption(base, "ໃນມື້ແດດອອກ ຍອດຫໍເຄື່ອນເປັນວົງ", t, 21.1, 24.0)
    M.caption(base, "ກວ້າງປະມານ 15 ຊັງຕີແມັດ ຕາມດວງອາທິດ", t, 24.0, 26.9)
    M.card(base, t, 23.0, 26.9, W / 2, 600, "ເສັ້ນທາງຂອງຍອດຫໍ", "ວົງກວ້າງ 15 ຊມ.", "ruler")
    M.caption(base, "ຂົວ ແລະທາງລົດໄຟ ຈຶ່ງຕ້ອງມີຮ່ອງຂະຫຍາຍຕົວ", t, 27.1, 30.9)
    if sc == "s_bridge" and t < 36.3:
        x, y = info["gap"]
        E.tag(base, x, y + 70, "ຮ່ອງຂະຫຍາຍຕົວ", t, 28.0, 36.2, size=46, col=M.ORANGE)
    M.caption(base, "ລອງສັງເກດຂົວໃກ້ບ້ານ ເຈົ້າຈະເຫັນຮ່ອງນ້ອຍໆ", t, 31.1, 34.0)
    M.caption(base, "ກົດຕິດຕາມໄວ້ ມື້ອື່ນມີເລື່ອງໃໝ່", t, 34.0, 36.3, col=(140, 215, 255))
    E.headline(base, t, 36.8, 42, "ຮ້ອນຂະຫຍາຍ ເຢັນຫົດ", "ວິສະວະກອນຕ້ອງຄິດໄວ້ກ່ອນ!", y=430, s1=72, s2=60)
    M.caption(base, C.SHARE_CTA, t, 37.2, 42, y=1640, size=50, col=(120, 210, 255))
    if 13 < t < 27:
        d = Image.new("RGBA", (W, H)); from PIL import ImageDraw
        E.draw_line(ImageDraw.Draw(base), W / 2, 1640, "(ຂະຫຍາຍເກີນຈິງ ເພື່ອໃຫ້ເຫັນ)", 32, (170, 178, 200, 255), 400)
    E.footer(base, "ຂໍ້ມູນ: La Tour Eiffel (ທາງການ)  |  ພາບປະກອບ 3D")
    return np.asarray(base.convert("RGB"))


if __name__ == "__main__":
    E.main(frame, DUR, "e4")
