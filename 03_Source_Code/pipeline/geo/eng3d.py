"""Tiny 3D engine shared by the 3D episodes: perspective camera, flat-shaded meshes, lines, shaded spheres, glow.
Images are uint8 RGB numpy arrays (H, W, 3)."""
import math
import numpy as np, cv2
from PIL import Image, ImageDraw
import mekong as M
import common as C
from common import W, H, FPS, prog, ease_io, lerp, clamp, draw_line

F, Y0 = 1500.0, 880.0
SH = 16  # subpixel shift


def unit(yaw, pitch):
    a, b = math.radians(yaw), math.radians(pitch)
    return np.array([math.cos(b) * math.cos(a), math.cos(b) * math.sin(a), math.sin(b)])


class Cam:
    def __init__(self, target, dist, yaw, pitch, f=F, y0=Y0, roll=0.0):
        self.target = np.asarray(target, float)
        o = unit(yaw, pitch)
        self.pos = self.target + dist * o
        self.fwd = -o
        r = np.cross(self.fwd, [0, 0, 1.0]); r /= np.linalg.norm(r)
        u = np.cross(r, self.fwd)
        if roll:
            c, s = math.cos(math.radians(roll)), math.sin(math.radians(roll))
            r, u = r * c + u * s, -r * s + u * c
        self.right, self.up, self.f, self.y0, self.dist = r, u, f, y0, dist

    def proj(self, p):
        p = np.atleast_2d(np.asarray(p, float))
        v = p - self.pos
        z = v @ self.fwd
        zz = np.where(z > 1e-6, z, 1e-6)
        return W / 2 + self.f * (v @ self.right) / zz, self.y0 - self.f * (v @ self.up) / zz, z

    def view(self, d):
        """world direction -> view space (x right, y up, z toward camera)"""
        return np.array([d @ self.right, d @ self.up, -(d @ self.fwd)])


def gradient(top, bottom, mid=None):
    g = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    top, bottom = np.array(top, np.float32), np.array(bottom, np.float32)
    img = top * (1 - g) + bottom * g
    return np.repeat(img, W, axis=1).astype(np.uint8)


_rng = np.random.default_rng(5)
_SD = _rng.standard_normal((2600, 3)); _SD /= np.linalg.norm(_SD, axis=1, keepdims=True)
_SB = _rng.uniform(0.2, 1.0, 2600) ** 2.2


def stars(img, cam, amount=1.0):
    x, y, z = cam.proj(cam.pos + _SD)
    ok = (z > 0.05) & (x >= 0) & (x < W - 1) & (y >= 0) & (y < H - 1)
    layer = np.zeros((H, W), np.float32)
    np.add.at(layer, (y[ok].astype(int), x[ok].astype(int)), _SB[ok] * 255 * amount)
    layer = cv2.GaussianBlur(layer, (3, 3), 0.7) * 1.6
    out = img.astype(np.float32) + layer[..., None] * np.array([0.9, 0.95, 1.0], np.float32)
    img[:] = np.clip(out, 0, 255).astype(np.uint8)


def _pt(x, y):
    return (int(round(x * SH)), int(round(y * SH)))


def ok2(x, y):
    return abs(x) < 2e4 and abs(y) < 2e4


def lines(img, cam, A, B, col, width_world=None, width_px=2.0, alpha=1.0, wmin=1, wmax=14):
    """Draw 3D segments A[i]-B[i]. col may be (3,) or (N,3). Width from world size if width_world given."""
    A, B = np.atleast_2d(A), np.atleast_2d(B)
    xa, ya, za = cam.proj(A); xb, yb, zb = cam.proj(B)
    cols = np.broadcast_to(np.asarray(col, float), (len(A), 3))
    order = np.argsort(-(za + zb))
    tgt = img if alpha >= 1 else img.copy()
    for i in order:
        if za[i] <= 0.5 or zb[i] <= 0.5 or not (ok2(xa[i], ya[i]) and ok2(xb[i], yb[i])):
            continue
        if width_world is not None:
            w = clamp(cam.f * width_world / ((za[i] + zb[i]) / 2), wmin, wmax)
        else:
            w = width_px
        cv2.line(tgt, _pt(xa[i], ya[i]), _pt(xb[i], yb[i]), tuple(float(c) for c in cols[i]), max(1, int(round(w))), cv2.LINE_AA, shift=4)
    if alpha < 1:
        cv2.addWeighted(tgt, alpha, img, 1 - alpha, 0, dst=img)


def polyline(img, cam, P, col, width_px=3, alpha=1.0, closed=False):
    P = np.atleast_2d(P)
    x, y, z = cam.proj(P)
    tgt = img.copy() if alpha < 1 else img
    seg = []
    for i in range(len(P)):
        if z[i] > 0.5 and ok2(x[i], y[i]):
            seg.append(_pt(x[i], y[i]))
        else:
            if len(seg) > 1:
                cv2.polylines(tgt, [np.array(seg, np.int32)], False, tuple(map(float, col)), width_px, cv2.LINE_AA, shift=4)
            seg = []
    if len(seg) > 1:
        cv2.polylines(tgt, [np.array(seg, np.int32)], closed, tuple(map(float, col)), width_px, cv2.LINE_AA, shift=4)
    if alpha < 1:
        cv2.addWeighted(tgt, alpha, img, 1 - alpha, 0, dst=img)


def mesh(img, cam, V, faces, cols, L, ambient=0.3, alpha=1.0, outline=None, spec=0.0, two_sided=False):
    """Flat-shaded polygons (painter's algorithm). faces: list of index lists; cols: (3,) or per-face (N,3).
    L: unit light direction in WORLD space (pointing toward the light)."""
    V = np.asarray(V, float)
    x, y, z = cam.proj(V)
    cols = np.broadcast_to(np.asarray(cols, float), (len(faces), 3))
    items = []
    for k, f in enumerate(faces):
        f = list(f)
        P = V[f]
        n = np.cross(P[1] - P[0], P[2] - P[0])
        nn = np.linalg.norm(n)
        if nn == 0:
            continue
        n /= nn
        cen = P.mean(0)
        facing = (cen - cam.pos) @ n
        if facing > 0:
            if not two_sided:
                continue
            n = -n
        if (z[f] <= 0.5).any():
            continue
        lam = max(0.0, float(n @ L))
        s = ambient + (1 - ambient) * lam
        c = cols[k] * s
        if spec:
            h = L - (cen - cam.pos) / np.linalg.norm(cen - cam.pos)
            h /= np.linalg.norm(h) + 1e-9
            c = c + 255 * spec * max(0.0, float(n @ h)) ** 30
        items.append((float(z[f].mean()), f, np.clip(c, 0, 255)))
    items.sort(key=lambda it: -it[0])
    tgt = img.copy() if alpha < 1 else img
    for _, f, c in items:
        pts = np.array([_pt(x[i], y[i]) for i in f], np.int32)
        if np.abs(pts).max() > 2e5:
            continue
        cv2.fillPoly(tgt, [pts], tuple(float(v) for v in c), cv2.LINE_AA, shift=4)
        if outline is not None:
            cv2.polylines(tgt, [pts], True, outline, 1, cv2.LINE_AA, shift=4)
    if alpha < 1:
        cv2.addWeighted(tgt, alpha, img, 1 - alpha, 0, dst=img)


def box(c, s):
    """Axis-aligned box: centre c, size s -> (V, faces) with outward winding."""
    cx, cy, cz = c; sx, sy, sz = np.asarray(s) / 2
    V = np.array([[cx + dx * sx, cy + dy * sy, cz + dz * sz] for dz in (-1, 1) for dy in (-1, 1) for dx in (-1, 1)])
    Fc = [[0, 2, 3, 1], [4, 5, 7, 6], [0, 1, 5, 4], [2, 6, 7, 3], [0, 4, 6, 2], [1, 3, 7, 5]]
    return V, Fc


def sphere(img, cx, cy, R, col, Lv, ambient=0.25, spec=0.35, alpha=1.0, rim=None):
    """Shaded sphere at screen position. Lv = light direction in view space."""
    if R < 1.2:
        if ok2(cx, cy):
            cv2.circle(img, _pt(cx, cy), int(max(R, 1) * SH), tuple(map(float, col)), -1, cv2.LINE_AA, shift=4)
        return
    x0, x1 = max(0, int(cx - R - 2)), min(W, int(cx + R + 3))
    y0, y1 = max(0, int(cy - R - 2)), min(H, int(cy + R + 3))
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx = (xx + 0.5 - cx) / R; dy = (cy - yy - 0.5) / R
    r2 = dx * dx + dy * dy
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    nl = dx * Lv[0] + dy * Lv[1] + z * Lv[2]
    sh = ambient + (1 - ambient) * np.clip(nl, 0, 1)
    hz = Lv + np.array([0, 0, 1.0]); hz /= np.linalg.norm(hz)
    sp = np.clip(dx * hz[0] + dy * hz[1] + z * hz[2], 0, 1) ** 40 * 255 * spec
    c = np.array(col, np.float32) * sh[..., None] + sp[..., None]
    if rim is not None:
        c += np.array(rim, np.float32) * ((1 - z) ** 3)[..., None]
    e = np.clip((1 - np.sqrt(r2)) * R + 0.5, 0, 1)[..., None] * alpha
    reg = img[y0:y1, x0:x1].astype(np.float32)
    img[y0:y1, x0:x1] = np.clip(reg * (1 - e) + c * e, 0, 255).astype(np.uint8)


class Glow:
    def __init__(self):
        self.l = np.zeros((H // 4, W // 4, 3), np.float32)

    def dot(self, x, y, r, col, a=1.0):
        if ok2(x, y) and r < 2e4:
            cv2.circle(self.l, _pt(x / 4, y / 4), max(1, int(r / 4 * SH)), tuple(float(c) * a for c in col), -1, cv2.LINE_AA, shift=4)

    def line(self, p, q, w, col, a=1.0):
        if ok2(*p) and ok2(*q):
            cv2.line(self.l, _pt(p[0] / 4, p[1] / 4), _pt(q[0] / 4, q[1] / 4), tuple(float(c) * a for c in col), max(1, int(w / 4)), cv2.LINE_AA, shift=4)

    def apply(self, img, sigma=4.0):
        g = cv2.GaussianBlur(self.l, (0, 0), sigma)
        g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
        img[:] = np.clip(img.astype(np.float32) + g, 0, 255).astype(np.uint8)


def grid(img, cam, size, step, z=0.0, col=(246, 140, 38), alpha=0.25, center=(0, 0)):
    cx, cy = center
    vals = np.arange(-size, size + step / 2, step)
    A = [[cx + v, cy - size, z] for v in vals] + [[cx - size, cy + v, z] for v in vals]
    B = [[cx + v, cy + size, z] for v in vals] + [[cx + size, cy + v, z] for v in vals]
    # split long lines so perspective clipping works
    n = 12
    AA, BB = [], []
    for a, b in zip(A, B):
        a, b = np.array(a), np.array(b)
        for k in range(n):
            AA.append(a + (b - a) * k / n); BB.append(a + (b - a) * (k + 1) / n)
    lines(img, cam, np.array(AA), np.array(BB), col, width_px=2, alpha=alpha)


def blend(a, b, u):
    return cv2.addWeighted(a, 1 - u, b, u, 0)


# ---------------- UI wrappers (same look as the map-story / EP.6) ----------------
def setup(ep, cat):
    M.EP, M.CAT, M.CAT_COL = ep, cat, C.CAT_COLORS.get(cat, (176, 132, 255))


def tag(base, x, y, text, t, t0, t1, size=40, col=(255, 248, 236)):
    a = C.fade(t, t0, t1, 0.35, 0.35)
    if a <= 0:
        return
    L = M.layer(); d = ImageDraw.Draw(L)
    k = C.ease(prog(t, t0, t0 + 0.4))
    draw_line(d, x, y + (1 - k) * 10, text, size, tuple(col) + (255,), 700, stroke=6, stroke_fill=(6, 10, 22, 230))
    M.put(base, L, a)


def headline(base, t, t0, t1, l1, l2, y=440, s1=76, s2=68):
    a = C.fade(t, t0, t1, 0.35, 0.4)
    if a <= 0:
        return
    L = M.layer(); d = ImageDraw.Draw(L)
    k = C.ease(prog(t, t0, t0 + 0.5))
    s1 = M.fit(l1, s1, W - 80); s2 = M.fit(l2, s2, W - 80)
    draw_line(d, W / 2, y + (1 - k) * 24, l1, s1, M.ORANGE + (255,), 700, stroke=7, stroke_fill=(6, 10, 22, 230))
    draw_line(d, W / 2, y + s1 * 1.35 + (1 - k) * 24, l2, s2, M.CREAMT + (255,), 700, stroke=6, stroke_fill=(6, 10, 22, 230))
    M.put(base, L, a)


def footer(base, text):
    d = ImageDraw.Draw(base)
    draw_line(d, W / 2, 1880, text, 24, (200, 200, 210, 200), 400)


def render(frame_fn, dur, out, f0=None, f1=None):
    import subprocess
    n = int(round(dur * FPS))
    f0 = 0 if f0 is None else f0
    f1 = n if f1 is None else f1
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(f0, f1):
        p.stdin.write(np.ascontiguousarray(frame_fn(i / FPS)).tobytes())
        if i % 60 == 0:
            print(out, i, flush=True)
    p.stdin.close(); p.wait()


def main(frame_fn, dur, prefix):
    import sys
    if sys.argv[1] == "--still":
        for s in sys.argv[2].split(","):
            Image.fromarray(frame_fn(float(s))).save(f"{prefix}_{float(s):05.1f}.png"); print("still", s)
        return
    f0, f1 = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (None, None)
    render(frame_fn, dur, sys.argv[1], f0, f1)
