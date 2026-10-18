"""EP.6 — 1 ປີແສງ (one light-year). 3D space flight, same look as the map-story clip. 1080x1920 @30.
usage: python3 lightyear.py out.mp4 [f0 f1] | --still t1,t2
"""
import sys, math, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw
import mekong as M
import common as C
from common import W, H, FPS, prog, ease_io, lerp, clamp, draw_line

DUR = 51.0
M.EP, M.CAT, M.CAT_COL = 6, "ອາວະກາດ", (176, 132, 255)
F, Y0 = 1500.0, 880.0
AU = 1.495978707e8
LY = 9.4607304725808e12
LD = LY / 365.25
RE, RM, RS = 6371.0, 1737.4, 695700.0
C_KMS = 299792.458

def unit(lon, lat):
    a, b = math.radians(lon), math.radians(lat)
    return np.array([math.cos(b) * math.cos(a), math.cos(b) * math.sin(a), math.sin(b)])

SUN = np.zeros(3)
EARTH = np.array([AU, 0, 0])
MOON = EARTH + 384400 * unit(118, 4)
VOY = LD * unit(258, 35)
PROX = 4.24 * LY * unit(239, -44)

# ---------------- camera ----------------
#        t     target                       D        yaw   pitch
KEYS = [(0.0,  EARTH,                      23900,    150,  14),
        (5.0,  EARTH,                      23900,    160,  14),
        (6.0,  EARTH,                      28500,    163,  16),
        (11.2, EARTH,                      28500,    172,  16),
        (13.0, (EARTH + MOON) / 2,         8.6e5,    200,  20),
        (18.0, (EARTH + MOON) / 2,         8.6e5,    206,  20),
        (20.0, EARTH * 0.5,                3.1e8,    262,  22),
        (25.0, EARTH * 0.5,                3.1e8,    268,  22),
        (27.2, VOY * 0.5,                  5.6e10,   280,  12),
        (32.0, VOY * 0.5,                  5.6e10,   286,  12),
        (34.2, SUN,                        3.4e13,   296,  32),
        (41.0, SUN,                        3.4e13,   306,  32),
        (43.0, PROX * 0.45,                9.0e13,   318,  14),
        (46.5, PROX * 0.45,                9.0e13,   324,  14),
        (48.4, EARTH,                      26000,    510,  14),
        (51.0, EARTH,                      24500,    516,  14)]


def camera(t):
    for (t0, T0, D0, y0, p0), (t1, T1, D1, y1, p1) in zip(KEYS, KEYS[1:]):
        if t <= t1:
            u = ease_io(prog(t, t0, t1))
            # target moves in step with the log-zoom so the subject never leaves the frame
            D = math.exp(lerp(math.log(D0), math.log(D1), u))
            w = u if abs(D1 - D0) < 1e-6 * D0 else (D - D0) / (D1 - D0)
            T = np.asarray(T0) + (np.asarray(T1) - np.asarray(T0)) * w
            return T, math.exp(lerp(math.log(D0), math.log(D1), u)), lerp(y0, y1, u), lerp(p0, p1, u)
    t0, T0, D0, y0, p0 = KEYS[-1]
    return np.asarray(T0), D0, y0, p0


class Cam:
    def __init__(self, t):
        T, D, yaw, pitch = camera(t)
        self.D = D
        o = unit(yaw, pitch)
        self.pos = T + D * o
        self.fwd = -o
        r = np.cross(self.fwd, [0, 0, 1.0]); self.right = r / np.linalg.norm(r)
        self.up = np.cross(self.right, self.fwd)

    def proj(self, p):
        p = np.atleast_2d(p)
        v = p - self.pos
        z = v @ self.fwd
        zz = np.where(z > 1e-9, z, 1e-9)
        return W / 2 + F * (v @ self.right) / zz, Y0 - F * (v @ self.up) / zz, z

    def dirproj(self, d):  # directions at infinity (stars)
        z = d @ self.fwd
        zz = np.where(z > 1e-6, z, 1e-6)
        return W / 2 + F * (d @ self.right) / zz, Y0 - F * (d @ self.up) / zz, z

    def light(self, body):
        l = SUN - body
        n = np.linalg.norm(l)
        l = l / n if n > 0 else np.array([0, 0, 1.0])
        return np.array([l @ self.right, l @ self.up, -(l @ self.fwd)])


# ---------------- textures ----------------
def make_moon():
    rng = np.random.default_rng(7)
    w, h = 1024, 512
    base = np.zeros((h, w), np.float32)
    for k, s in [(4, 0.5), (16, 0.25), (64, 0.12), (256, 0.06)]:
        n = rng.standard_normal((max(2, k // 2), k)).astype(np.float32)
        base += cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC) * s
    img = 0.62 + base * 0.12
    yy, xx = np.mgrid[0:h, 0:w]
    for _ in range(9):   # maria
        cx, cy, r = rng.uniform(0, w), rng.uniform(h * 0.25, h * 0.75), rng.uniform(40, 110)
        img -= 0.16 * np.exp(-(((xx - cx) ** 2) + ((yy - cy) * 1.4) ** 2) / (2 * r * r))
    for _ in range(260):  # craters
        cx, cy, r = rng.uniform(0, w), rng.uniform(0, h), rng.exponential(5) + 2
        d = np.hypot(xx - cx, yy - cy) / r
        img += 0.10 * np.exp(-((d - 1) ** 2) * 18) - 0.07 * (d < 0.9)
    g = np.clip(img, 0, 1)
    return (np.stack([g * 215, g * 210, g * 205], -1)).astype(np.uint8)


MOONTEX = make_moon()


def moon_sample(lon, lat):
    u = (((lon + 180) % 360) / 360 * MOONTEX.shape[1]).astype(np.float32)
    v = ((90 - lat) / 180 * MOONTEX.shape[0]).astype(np.float32)
    return cv2.remap(MOONTEX, u, v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP).astype(np.float32)


rng = np.random.default_rng(11)
SD = rng.standard_normal((3200, 3)); SD /= np.linalg.norm(SD, axis=1, keepdims=True)
SB = rng.uniform(0.15, 1.0, 3200) ** 2.4
STC = np.array([[255, 255, 255], [200, 220, 255], [255, 230, 200], [180, 200, 255]], np.float32)[rng.integers(0, 4, 3200)]


def background(cam):
    g = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    img = (np.array([5, 8, 20], np.float32) * (1 - g) + np.array([10, 16, 36], np.float32) * g) * np.ones((1, W, 1), np.float32)
    x, y, z = cam.dirproj(SD)
    ok = (z > 0.05) & (x >= 0) & (x < W - 1) & (y >= 0) & (y < H - 1)
    star = np.zeros((H, W, 3), np.float32)
    xi, yi = x[ok].astype(int), y[ok].astype(int)
    np.add.at(star, (yi, xi), (SB[ok, None] * STC[ok]) * 1.6)
    star = cv2.GaussianBlur(star, (3, 3), 0.7)
    return img + star


# ---------------- drawing ----------------
def sphere(img, cx, cy, R, sampler, clon, clat, L, ambient=0.1, atmos=None):
    pad = int(R * 0.12 + 6)
    x0, x1 = max(0, int(cx - R - pad)), min(W, int(cx + R + pad) + 1)
    y0, y1 = max(0, int(cy - R - pad)), min(H, int(cy + R + pad) + 1)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx = (xx + 0.5 - cx) / R; dy = (cy - yy - 0.5) / R
    r2 = dx * dx + dy * dy
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    p0 = math.radians(clat)
    lat = np.degrees(np.arcsin(np.clip(z * math.sin(p0) + dy * math.cos(p0), -1, 1)))
    lon = clon + np.degrees(np.arctan2(dx, z * math.cos(p0) - dy * math.sin(p0)))
    col = sampler(lon, lat)
    nl = dx * L[0] + dy * L[1] + z * L[2]
    lit = np.clip((nl + 0.08) / 0.3, 0, 1)
    lit = lit * lit * (3 - 2 * lit) * np.clip(0.55 + 0.45 * nl, 0, 1) ** 0.5
    shade = ambient + (1 - ambient) * lit
    col = col * (shade * (0.6 + 0.4 * z ** 0.4))[..., None]
    edge = np.clip((1 - np.sqrt(r2)) * R + 0.5, 0, 1)[..., None]
    reg = img[y0:y1, x0:x1]
    reg[:] = reg * (1 - edge) + col * edge
    if atmos is not None:
        rr = np.sqrt(r2)
        halo = np.exp(-np.abs(rr - 1) * R / max(2.5, R * 0.035)) * np.clip(0.25 + nl * 0.9 + 0.3, 0, 1.2)
        reg += halo[..., None] * np.array(atmos, np.float32)


class Glow:
    def __init__(self):
        self.s = 4
        self.l = np.zeros((H // 4, W // 4, 3), np.float32)

    def dot(self, x, y, r, col, a=1.0):
        if not (abs(x) < 2e4 and abs(y) < 2e4 and r < 2e4):
            return
        cv2.circle(self.l, (int(x / 4 * 16), int(y / 4 * 16)), max(1, int(r / 4 * 16)), tuple(float(c) * a for c in col), -1, cv2.LINE_AA, shift=4)

    def line(self, p, q, w, col, a=1.0):
        if not all(abs(v) < 2e4 for v in (*p, *q)):
            return
        cv2.line(self.l, (int(p[0] / 4 * 16), int(p[1] / 4 * 16)), (int(q[0] / 4 * 16), int(q[1] / 4 * 16)), tuple(float(c) * a for c in col), max(1, int(w / 4)), cv2.LINE_AA, shift=4)

    def apply(self, img, sigma=4.0):
        g = cv2.GaussianBlur(self.l, (0, 0), sigma)
        img += cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)


def circ(img, x, y, r, col):
    if abs(x) < 2e4 and abs(y) < 2e4:
        cv2.circle(img, (int(x * 16), int(y * 16)), int(r * 16), col, -1, cv2.LINE_AA, shift=4)


def poly3d(img, cam, pts, col, alpha, width=2, closed=True, dash=False):
    x, y, z = cam.proj(pts)
    ok = z > 0
    layer = np.zeros((H, W), np.uint8)
    seg = []
    for i in range(len(pts)):
        if ok[i] and abs(x[i]) < 20000 and abs(y[i]) < 20000:
            seg.append((x[i], y[i]))
        else:
            if len(seg) > 1:
                cv2.polylines(layer, [np.round(np.array(seg) * 16).astype(np.int32)], False, 255, width, cv2.LINE_AA, shift=4)
            seg = []
    if len(seg) > 1:
        cv2.polylines(layer, [np.round(np.array(seg) * 16).astype(np.int32)], closed and ok.all(), 255, width, cv2.LINE_AA, shift=4)
    if dash:
        mask = ((np.arange(W)[None, :] // 14 + np.arange(H)[:, None] // 14) % 2).astype(np.uint8)
        layer = layer * mask
    m = layer.astype(np.float32)[..., None] / 255 * alpha
    img[:] = img * (1 - m) + np.array(col, np.float32) * m


def circle3d(center, r, n=360, tilt=0.0):
    a = np.linspace(0, 2 * np.pi, n, endpoint=True)
    return center + r * np.stack([np.cos(a), np.sin(a) * math.cos(tilt), np.sin(a) * math.sin(tilt)], 1)


def disp_r(cam, body, r, rmin):
    _, _, z = cam.proj(body)
    return max(F * r / max(z[0], 1), rmin), z[0]


def lerpv(a, b, u):
    return np.asarray(a) + (np.asarray(b) - np.asarray(a)) * u


BEAM = (150, 225, 255)


def pulse(img, glow, cam, A, B, u, width=5):
    """Light pulse travelling from A to B (u = 0..1)."""
    if u <= 0:
        return
    P = lerpv(A, B, u)
    xa, ya, za = cam.proj(A); xp, yp, zp = cam.proj(P)
    if za[0] <= 0 or zp[0] <= 0:
        return
    pa, pp = (xa[0], ya[0]), (xp[0], yp[0])
    core = np.zeros((H, W), np.uint8)
    cv2.line(core, (int(pa[0] * 16), int(pa[1] * 16)), (int(pp[0] * 16), int(pp[1] * 16)), 255, width, cv2.LINE_AA, shift=4)
    m = core.astype(np.float32)[..., None] / 255 * 0.85
    img[:] = img * (1 - m) + np.array(BEAM, np.float32) * m
    glow.line(pa, pp, width * 4, (40, 120, 255), 0.8)
    if u < 1:
        glow.dot(pp[0], pp[1], 26, (180, 230, 255), 2.2)
        circ(img, pp[0], pp[1], 9, (255, 255, 255))


def scene(t):
    cam = Cam(t)
    img = background(cam)
    glow = Glow()
    info = {}
    D = cam.D
    # ---- orbits ----
    a_moon = clamp((math.log10(D) - 4.9) * 2) * (1 - clamp((math.log10(D) - 7.2) * 2))
    if a_moon > 0:
        poly3d(img, cam, circle3d(EARTH, 384400, 360, math.radians(5)), (200, 210, 230), 0.35 * a_moon, 2)
    a_pl = clamp((math.log10(D) - 7.8) * 2) * (1 - clamp((math.log10(D) - 12.0) * 1.5))
    if a_pl > 0:
        for au, a in [(0.387, .25), (0.723, .25), (1.0, .55), (1.524, .25), (5.2, .25), (9.58, .25), (19.2, .25), (30.1, .3)]:
            fz = clamp((0.6 * D - au * AU) / (0.25 * D))
            if fz > 0:
                poly3d(img, cam, circle3d(SUN, au * AU, 240), (246, 160, 70) if au == 1.0 else (200, 200, 220), a * a_pl * fz, 2)
    a_ly = clamp((math.log10(D) - 12.6) * 2)
    if a_ly > 0 and t < 48:
        poly3d(img, cam, circle3d(SUN, LY, 360), (246, 140, 38), 0.85 * a_ly, 3, dash=True)
        info["ly_ring"] = cam.proj(SUN + LY * unit(296 + 90, 0))
    # Voyager trajectory + probe
    a_v = clamp((math.log10(D) - 9.6) * 2) * (1 - clamp((math.log10(D) - 12.4) * 2)) * (t < 41)
    if a_v > 0 and cam.proj(VOY)[2][0] > 0:
        tr = np.array([lerpv(SUN, VOY, s) for s in np.linspace(0, 1, 80)])
        poly3d(img, cam, tr, (200, 225, 255), 0.55 * a_v, 2, closed=False, dash=True)
        vx, vy, vz = cam.proj(VOY)
        glow.dot(vx[0], vy[0], 14, (200, 230, 255), 1.4 * a_v)
        circ(img, vx[0], vy[0], 6, (255, 255, 255))
        info["voy"] = (vx[0], vy[0], a_v)
    # ---- Proxima ----
    px, py, pz = cam.proj(PROX)
    a_p = clamp((math.log10(D) - 13.3) * 3) * (t < 48)
    if a_p > 0 and pz[0] > 0:
        glow.dot(px[0], py[0], 40, (255, 110, 70), 2.2 * a_p)
        circ(img, px[0], py[0], 8, (255, 190, 160))
        info["prox"] = (px[0], py[0], a_p)
    # ---- Sun ----
    sx, sy, sz = cam.proj(SUN)
    if sz[0] > 0:
        rmin = clamp(34 - 6 * max(0, math.log10(D / 3e8)), 8, 34)
        R, _ = disp_r(cam, SUN, RS, rmin)
        if -400 < sx[0] < W + 400 and -400 < sy[0] < H + 400:
            glow.dot(sx[0], sy[0], R * 3.2, (255, 150, 40), 1.4)
            glow.dot(sx[0], sy[0], R * 1.6, (255, 200, 110), 1.2)
            yy, xx = np.ogrid[0:H, 0:W]
            x0, x1 = max(0, int(sx[0] - R - 2)), min(W, int(sx[0] + R + 3))
            y0, y1 = max(0, int(sy[0] - R - 2)), min(H, int(sy[0] + R + 3))
            if x0 < x1 and y0 < y1:
                yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
                rr = np.hypot(xx - sx[0], yy - sy[0]) / R
                mu = np.sqrt(np.clip(1 - rr * rr, 0, 1))
                col = np.array([255, 160, 60], np.float32) + np.array([0, 85, 150], np.float32) * (mu ** 0.7)[..., None]
                e = np.clip((1 - rr) * R + 0.5, 0, 1)[..., None]
                reg = img[y0:y1, x0:x1]
                reg[:] = reg * (1 - e) + col * e
        info["sun"] = (sx[0], sy[0], R)
    # ---- Earth & Moon (draw far one first) ----
    sep = math.hypot(*(np.array(cam.proj(EARTH)[:2]).ravel() - np.array([sx[0], sy[0]])))
    a_e = clamp((sep - 14) / 25) if t < 48 else 1.0
    bodies = []
    for name, pos, r, rmin in [("earth", EARTH, RE, 30), ("moon", MOON, RM, 17)]:
        R, z = disp_r(cam, pos, r, rmin)
        x, y, _ = cam.proj(pos)
        bodies.append((z, name, pos, R, x[0], y[0]))
    for z, name, pos, R, x, y in sorted(bodies, key=lambda b: -b[0]):
        if z <= 0 or a_e <= 0:
            continue
        if name == "moon" and not (11.2 < t < 22):
            continue
        L = cam.light(pos)
        if name == "earth":
            if R > 2600:
                continue
            spin = 80 + t * 3.2 if t < 30 else 92 + (t - 46) * 3
            sphere(img, x, y, R, M.sample, spin, 12, L, 0.13, atmos=(60, 130, 255))
            if R < 40:
                glow.dot(x, y, R * 1.8, (60, 130, 255), 0.5 * a_e)
        else:
            sphere(img, x, y, R, moon_sample, 0, 0, L, 0.06)
        info[name] = (x, y, R)
    # ---- light ----
    if 6.2 < t < 11.4:   # 7.5 laps around Earth in "1 second" (slowed down)
        u = prog(t, 6.6, 10.6)
        laps = 7.5 * u
        ring = circle3d(EARTH, RE * 1.16, 400, math.radians(20))
        ex, ey, ez = cam.proj(EARTH)
        Rr = info["earth"][2]
        ang = laps * 2 * np.pi
        x, y, z = cam.proj(ring)
        hid = (z > ez[0]) & (np.hypot(x - ex[0], y - ey[0]) < Rr)
        a_r = M.C.fade(t, 6.3, 11.3, 0.3, 0.3)
        lay = np.zeros((H, W), np.uint8)
        for i in range(len(ring) - 1):
            if not hid[i] and not hid[i + 1]:
                cv2.line(lay, (int(x[i] * 16), int(y[i] * 16)), (int(x[i + 1] * 16), int(y[i + 1] * 16)), 90, 2, cv2.LINE_AA, shift=4)
        trail = np.linspace(ang - 1.4, ang, 40)
        tp = EARTH + RE * 1.16 * np.stack([np.cos(trail), np.sin(trail) * math.cos(math.radians(20)), np.sin(trail) * math.sin(math.radians(20))], 1)
        tx, ty, tz = cam.proj(tp)
        th = (tz > ez[0]) & (np.hypot(tx - ex[0], ty - ey[0]) < Rr)
        for i in range(39):
            if not th[i] and not th[i + 1]:
                k = i / 39
                cv2.line(lay, (int(tx[i] * 16), int(ty[i] * 16)), (int(tx[i + 1] * 16), int(ty[i + 1] * 16)), int(90 + 165 * k), int(2 + 6 * k), cv2.LINE_AA, shift=4)
                glow.line((tx[i], ty[i]), (tx[i + 1], ty[i + 1]), 12 * k + 4, (60, 150, 255), 0.9 * k * a_r)
        if not th[-1] and u < 1:
            glow.dot(tx[-1], ty[-1], 30, (190, 235, 255), 2.4 * a_r)
        m = lay.astype(np.float32)[..., None] / 255 * a_r
        img[:] = img * (1 - m) + np.array(BEAM, np.float32) * m
        info["laps"] = laps
    if 13.0 < t < 18.2:
        u = prog(t, 13.6, 16.2)
        pulse(img, glow, cam, EARTH + (MOON - EARTH) / np.linalg.norm(MOON - EARTH) * RE, MOON, u)
        info["moon_t"] = 1.282 * u
    if 20.0 < t < 25.2:
        u = prog(t, 20.4, 23.6)
        dirv = EARTH / np.linalg.norm(EARTH)
        pulse(img, glow, cam, dirv * RS, EARTH, u)
        info["sun_t"] = 499.0 * u
    if 33.6 < t < 41.2:
        u = prog(t, 34.4, 37.6)
        pulse(img, glow, cam, SUN, SUN + LY * unit(296 + 90, 0), u, 6)
        info["days"] = 365.25 * u
    glow.apply(img)
    return np.clip(img, 0, 255), info


# ---------------- UI ----------------
_orig_icon = M.icon


def icon(d, kind, cx, cy, s, col):
    c = col + (255,)
    if kind == "bolt":
        d.polygon([(cx + s * 0.2, cy - s), (cx - s * 0.6, cy + s * 0.15), (cx - s * 0.05, cy + s * 0.15), (cx - s * 0.25, cy + s),
                   (cx + s * 0.6, cy - s * 0.2), (cx + s * 0.05, cy - s * 0.2)], fill=c)
    elif kind == "globe":
        d.ellipse((cx - s, cy - s, cx + s, cy + s), outline=c, width=max(3, int(s / 6)))
        d.ellipse((cx - s * 0.45, cy - s, cx + s * 0.45, cy + s), outline=c, width=max(2, int(s / 8)))
        d.line([(cx - s, cy), (cx + s, cy)], fill=c, width=max(2, int(s / 8)))
    elif kind == "moon":
        d.ellipse((cx - s, cy - s, cx + s, cy + s), fill=c)
        d.ellipse((cx - s * 0.45, cy - s * 1.1, cx + s * 1.3, cy + s * 0.7), fill=(12, 18, 34, 255))
    elif kind == "sun":
        d.ellipse((cx - s * 0.5, cy - s * 0.5, cx + s * 0.5, cy + s * 0.5), fill=c)
        for k in range(8):
            a = k * math.pi / 4
            d.line([(cx + math.cos(a) * s * 0.7, cy + math.sin(a) * s * 0.7), (cx + math.cos(a) * s, cy + math.sin(a) * s)], fill=c, width=max(3, int(s / 6)))
    elif kind == "probe":
        d.ellipse((cx - s * 0.35, cy - s * 0.35, cx + s * 0.35, cy + s * 0.35), fill=c)
        d.pieslice((cx - s * 1.0, cy - s * 1.2, cx + s * 0.6, cy + s * 0.2), 200, 340, fill=c)
        d.line([(cx, cy), (cx + s, cy + s * 0.8)], fill=c, width=max(3, int(s / 6)))
        d.line([(cx, cy), (cx - s, cy + s * 0.8)], fill=c, width=max(3, int(s / 6)))
    elif kind == "clock":
        d.ellipse((cx - s, cy - s, cx + s, cy + s), outline=c, width=max(3, int(s / 6)))
        d.line([(cx, cy), (cx, cy - s * 0.6)], fill=c, width=max(3, int(s / 6)))
        d.line([(cx, cy), (cx + s * 0.45, cy + s * 0.2)], fill=c, width=max(3, int(s / 6)))
    elif kind == "car":
        d.rounded_rectangle((cx - s, cy - s * 0.1, cx + s, cy + s * 0.5), int(s * 0.2), fill=c)
        d.polygon([(cx - s * 0.6, cy - s * 0.1), (cx - s * 0.35, cy - s * 0.6), (cx + s * 0.4, cy - s * 0.6), (cx + s * 0.65, cy - s * 0.1)], fill=c)
        for ox in (-0.55, 0.55):
            d.ellipse((cx + ox * s - s * 0.25, cy + s * 0.3, cx + ox * s + s * 0.25, cy + s * 0.8), fill=(12, 18, 34, 255), outline=c, width=3)
    elif kind == "star":
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            rr = s if k % 2 == 0 else s * 0.42
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        d.polygon(pts, fill=c)
    else:
        _orig_icon(d, kind, cx, cy, s, col)


M.icon = icon


def tag(base, x, y, text, t, t0, t1, size=40, dy=0, col=(255, 248, 236)):
    a = C.fade(t, t0, t1, 0.35, 0.35)
    if a <= 0:
        return
    L = M.layer(); d = ImageDraw.Draw(L)
    k = C.ease(prog(t, t0, t0 + 0.4))
    draw_line(d, x, y + dy + (1 - k) * 10, text, size, col + (255,), 700, stroke=6, stroke_fill=(6, 10, 22, 230))
    M.put(base, L, a)


def mmss(s):
    s = int(round(s))
    return f"{s // 60} ນາທີ {s % 60:02d} ວິ"


def ui(img, t, info):
    base = Image.fromarray(img.astype(np.uint8)).convert("RGBA")
    M.brand(base)
    for txt, a, b in [("ເປີດເລື່ອງ", 0.2, 4.9), ("ຄວາມໄວແສງ", 5.3, 11.3), ("ໂລກ ຫາ ດວງເດືອນ", 11.6, 18.0), ("ດວງອາທິດ ຫາ ໂລກ", 18.4, 25.0),
                      ("1 ວັນແສງ", 25.4, 32.0), ("1 ປີແສງ", 32.4, 41.0), ("ດາວທີ່ໃກ້ທີ່ສຸດ", 41.4, 46.4), ("ບອກຕໍ່", 48.4, 52)]:
        M.pill(base, txt, t, a, b)
    if t < 5.2:
        a = C.fade(t, 0.25, 4.8, 0.35, 0.4)
        L = M.layer(); d = ImageDraw.Draw(L)
        k = C.ease(prog(t, 0.25, 0.8))
        draw_line(d, W / 2, 440 + (1 - k) * 24, "1 ປີແສງ", 110, M.ORANGE + (255,), 700, stroke=7, stroke_fill=(6, 10, 22, 230))
        draw_line(d, W / 2, 550 + (1 - k) * 24, "ໄກປານໃດກັນແທ້?", 72, M.CREAMT + (255,), 700, stroke=6, stroke_fill=(6, 10, 22, 230))
        M.put(base, L, a)
    # S2 speed of light
    M.caption(base, "ແສງ ໄວທີ່ສຸດໃນຈັກກະວານ", t, 5.4, 8.2)
    M.caption(base, "1 ວິນາທີ ແສງອ້ອມໂລກໄດ້ 7.5 ຮອບ", t, 8.2, 11.3)
    M.card(base, t, 5.7, 11.3, 285, 480, "ຄວາມໄວແສງ", "300,000 ກມ./ວິ", "bolt")
    laps = info.get("laps", 7.5 if t > 10.6 else 0)
    M.card(base, t, 6.5, 11.3, 795, 480, "ແສງ 1 ວິນາທີ", f"{laps:.1f} ຮອບໂລກ", "globe")
    # S3 Earth-Moon
    if "earth" in info and 12.6 < t < 18.2:
        x, y, R = info["earth"]; tag(base, x, y + R + 52, "ໂລກ", t, 12.8, 18.0)
    if "moon" in info and 12.6 < t < 18.2:
        x, y, R = info["moon"]; tag(base, x, y + R + 52, "ດວງເດືອນ", t, 13.0, 18.0)
    M.caption(base, "ໂລກ ຫາ ດວງເດືອນ ໄກ 384,400 ກິໂລແມັດ", t, 11.7, 14.9)
    M.caption(base, "ແສງໃຊ້ເວລາ ແຄ່ 1.3 ວິນາທີ", t, 14.9, 18.0)
    mt = info.get("moon_t", 1.282 if t > 16.2 else 0)
    M.card(base, t, 12.2, 18.0, W / 2, 600, "ເວລາທີ່ແສງໃຊ້", f"{mt:.2f} ວິນາທີ", "clock")
    # S4 Sun-Earth
    if "sun" in info and 19.6 < t < 25.2:
        x, y, R = info["sun"]; tag(base, x, y + R + 60, "ດວງອາທິດ", t, 19.8, 25.0)
    if "earth" in info and 19.6 < t < 25.2:
        x, y, R = info["earth"]; tag(base, x, y + R + 52, "ໂລກ", t, 19.8, 25.0)
    M.caption(base, "ແສງຈາກດວງອາທິດ ມາຮອດໂລກ", t, 18.5, 21.6)
    M.caption(base, "ໃຊ້ເວລາ ປະມານ 8 ນາທີ 20 ວິນາທີ", t, 21.6, 25.0)
    st = info.get("sun_t", 499 if t > 23.6 else 0)
    M.card(base, t, 19.0, 25.0, W / 2, 600, "ເວລາທີ່ແສງໃຊ້", mmss(st), "sun")
    # S5 Voyager
    if "voy" in info and 26.6 < t < 32.2:
        x, y, a = info["voy"]; tag(base, x, y - 26, "Voyager 1", t, 26.8, 32.0, size=40)
    M.caption(base, "ຍານ Voyager 1 ອອກເດີນທາງ ຕັ້ງແຕ່ປີ 1977", t, 25.5, 28.7)
    M.caption(base, "ເດືອນພະຈິກ 2026 ນີ້ ຈະໄກຮອດ 1 ວັນແສງ", t, 28.7, 32.0)
    M.card(base, t, 26.0, 32.0, 285, 480, "ບິນມາແລ້ວ", "49 ປີ", "probe")
    M.card(base, t, 28.8, 32.0, 795, 480, "ແສງໃຊ້ເວລາ", "1 ວັນ", "clock")
    # S6 one light-year
    if "ly_ring" in info and 34.0 < t < 41.2:
        x, y, z = info["ly_ring"]; tag(base, x[0] - 20, y[0] + 64, "1 ປີແສງ", t, 37.6, 41.0, size=46, col=M.ORANGE)
    if "sun" in info and 33.8 < t < 46.6:
        x, y, R = info["sun"]; tag(base, x, y + 66, "ດວງອາທິດ", t, 34.0, 46.4, size=36)
    M.caption(base, "ແສງເດີນທາງ 1 ປີເຕັມ = 1 ປີແສງ", t, 32.5, 35.8)
    M.caption(base, "ໄກ 9.46 ລ້ານລ້ານ ກິໂລແມັດ", t, 35.8, 38.4)
    M.caption(base, "ຂັບລົດ 100 ກມ./ຊມ. ຕ້ອງໃຊ້ 10.8 ລ້ານປີ!", t, 38.4, 41.0)
    days = info.get("days", 365.25 if t > 37.6 else 0)
    if t < 37.7:
        M.card(base, t, 33.0, 37.7, W / 2, 600, "ແສງເດີນທາງມາແລ້ວ", f"{int(days)} ວັນ", "clock")
    M.card(base, t, 37.7, 41.0, 285, 480, "1 ປີແສງ", "9.46 ລ້ານລ້ານ ກມ.", "ruler")
    M.card(base, t, 38.5, 41.0, 795, 480, "ຂັບລົດ 100 ກມ./ຊມ.", "10.8 ລ້ານປີ", "car")
    # S7 Proxima
    if "prox" in info and 42.0 < t < 46.6:
        x, y, a = info["prox"]; tag(base, x, y + 66, "Proxima Centauri", t, 42.2, 46.4, size=38)
    M.caption(base, "ດາວທີ່ໃກ້ເຮົາທີ່ສຸດ ໄກ 4.24 ປີແສງ", t, 41.5, 44.0)
    M.caption(base, "ແສງທີ່ເຮົາເຫັນ ອອກມາຕັ້ງແຕ່ 4 ປີກ່ອນ!", t, 44.0, 46.4)
    M.card(base, t, 42.0, 46.4, W / 2, 640, "Proxima Centauri", "4.24 ປີແສງ", "star")
    # S8 ending
    if t > 48.0:
        a = C.fade(t, 48.3, 53, 0.4, 0.4)
        L = M.layer(); d = ImageDraw.Draw(L)
        k = C.ease(prog(t, 48.3, 48.8))
        draw_line(d, W / 2, 440 + (1 - k) * 20, "ປີແສງ ແມ່ນໄລຍະທາງ ບໍ່ແມ່ນເວລາ!", 60, M.ORANGE + (255,), 700, stroke=6, stroke_fill=(6, 10, 22, 230))
        draw_line(d, W / 2, 530 + (1 - k) * 20, "ເຈົ້າຢາກໄປດາວດວງໃດ? ຄອມເມັ້ນເລີຍ!", 54, M.CREAMT + (255,), 700, stroke=6, stroke_fill=(6, 10, 22, 230))
        M.put(base, L, a)
        M.caption(base, C.SHARE_CTA, t, 49.2, 53, y=1640, size=50, col=(120, 210, 255))
    d = ImageDraw.Draw(base)
    draw_line(d, W / 2, 1880, "ຂໍ້ມູນ: IAU, NASA/JPL, EarthSky  |  ພາບປະກອບ ຂະໜາດດາວບໍ່ຕາມສັດສ່ວນ", 24, (200, 200, 210, 200), 400)
    return np.asarray(base.convert("RGB"))


def frame(t):
    img, info = scene(t)
    return ui(img, t, info)


if __name__ == "__main__":
    if sys.argv[1] == "--still":
        for s in sys.argv[2].split(","):
            Image.fromarray(frame(float(s))).save(f"ly_{float(s):05.1f}.png"); print("still", s)
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
