"""EP.5 (3D) ຟີຊິກ — ມະນຸດທຸກຄົນ ບັນຈຸໃສ່ກ້ອນນ້ຳຕານກ້ອນດຽວ. 39 s."""
import math
import numpy as np, cv2
from PIL import Image
import eng3d as E
from eng3d import M, C, W, H, prog, ease_io, lerp, clamp, unit

DUR = 39.0
E.setup(5, "ຟີຊິກ")
rng = np.random.default_rng(21)
SUGAR = np.array([246, 244, 238.0])


def space_bg(cam):
    img = E.gradient((6, 9, 22), (16, 22, 46))
    E.stars(img, cam, 0.9)
    return img


def sugar_cube(c, s, n=5):
    """Subdivided cube (grainy crystal look). Returns V, faces, colours."""
    V, Fc, cols = [], [], []
    h = s / 2
    axes = [((1, 0, 0), (0, 1, 0), (0, 0, 1)), ((1, 0, 0), (0, 0, 1), (0, 1, 0)), ((0, 1, 0), (0, 0, 1), (1, 0, 0))]
    r = np.random.default_rng(4)
    for u, v, w in axes:
        u, v, w = map(np.array, (u, v, w))
        for sgn in (-1, 1):
            for i in range(n):
                for j in range(n):
                    a0, a1 = -h + s * i / n, -h + s * (i + 1) / n
                    b0, b1 = -h + s * j / n, -h + s * (j + 1) / n
                    q = [c + u * a0 + v * b0 + w * h * sgn, c + u * a1 + v * b0 + w * h * sgn,
                         c + u * a1 + v * b1 + w * h * sgn, c + u * a0 + v * b1 + w * h * sgn]
                    nrm = np.cross(q[1] - q[0], q[2] - q[0])
                    if nrm @ (w * sgn) < 0:
                        q = q[::-1]
                    k = len(V)
                    V += q; Fc.append([k, k + 1, k + 2, k + 3])
                    cols.append(SUGAR * r.uniform(0.86, 1.0))
    return np.array(V), Fc, np.array(cols)


SPARK = rng.uniform(-0.5, 0.5, (40, 3))


def draw_cube(img, cam, g, c, s, t, alpha=1.0, L=None):
    V, Fc, cols = sugar_cube(np.asarray(c, float), s)
    L = unit(-140, 50) if L is None else L
    E.mesh(img, cam, V, Fc, cols, L, 0.42, alpha=alpha, spec=0.25)
    x, y, z = cam.proj(np.asarray(c) + SPARK * s)
    for i in range(len(SPARK)):
        tw = max(0.0, math.sin(t * 3 + i * 1.7)) ** 8
        if tw > 0.05 and z[i] > 0:
            g.dot(x[i], y[i], 10, (220, 240, 255), 1.5 * tw * alpha)
    xc, yc, _ = cam.proj(c)
    g.dot(xc[0], yc[0], cam.f * s / cam.dist * 1.1, (120, 170, 255), 0.25 * alpha)


# ---------------- scenes ----------------
def s_cube(t):
    cam = E.Cam((0, 0, 0), 4.2, 30 + t * 22, 24, y0=900)
    img = space_bg(cam); g = E.Glow()
    draw_cube(img, cam, g, (0, 0, 0), 1.2, t)
    g.apply(img)
    return img, {}


CLOUD = rng.standard_normal((5200, 3)); CLOUD /= np.linalg.norm(CLOUD, axis=1, keepdims=True)
CLOUD *= rng.normal(1.0, 0.18, (5200, 1))
NUC = rng.standard_normal((14, 3)) * 0.018
NUCC = np.where(rng.random(14) < 0.5, 0, 1)
ORB = [(0, 0), (60, 60), (-60, 60)]


def s_atom(t):
    cam = E.Cam((0, 0, 0), lerp(3.6, 2.7, ease_io(prog(t, 4.0, 9.0))), 20 + t * 8, 18, y0=900)
    img = space_bg(cam); g = E.Glow()
    # electron cloud (additive dots)
    x, y, z = cam.proj(CLOUD)
    ok = (z > 0) & (x > 0) & (x < W - 1) & (y > 0) & (y < H - 1)
    lay = np.zeros((H, W), np.float32)
    np.add.at(lay, (y[ok].astype(int), x[ok].astype(int)), 900.0)
    lay = cv2.GaussianBlur(lay, (0, 0), 1.5)
    img[:] = np.clip(img + lay[..., None] * np.array([0.35, 0.7, 1.0], np.float32), 0, 255).astype(np.uint8)
    # orbits + electrons
    for k, (yaw, tilt) in enumerate(ORB):
        a = np.linspace(0, 2 * np.pi, 160)
        ring = np.stack([np.cos(a), np.sin(a), 0 * a], 1)
        Rz = np.array([[math.cos(math.radians(yaw)), -math.sin(math.radians(yaw)), 0], [math.sin(math.radians(yaw)), math.cos(math.radians(yaw)), 0], [0, 0, 1]])
        Rx = np.array([[1, 0, 0], [0, math.cos(math.radians(tilt)), -math.sin(math.radians(tilt))], [0, math.sin(math.radians(tilt)), math.cos(math.radians(tilt))]])
        ring = ring @ (Rz @ Rx).T * 1.05
        E.polyline(img, cam, ring, (90, 150, 230), 2, alpha=0.6, closed=True)
        ang = t * (2.2 + k * 0.4) + k * 2
        e = np.array([math.cos(ang), math.sin(ang), 0]) @ (Rz @ Rx).T * 1.05
        ex, ey, ez = cam.proj(e)
        g.dot(ex[0], ey[0], 34, (90, 170, 255), 1.6)
        E.sphere(img, ex[0], ey[0], 9, (170, 220, 255), np.array([0.3, 0.5, 0.8]), 0.5, 0.6)
    # nucleus (tiny!)
    x, y, z = cam.proj(NUC)
    Lv = cam.view(unit(-130, 50))
    for i in np.argsort(-z):
        E.sphere(img, x[i], y[i], max(2.2, cam.f * 0.016 / z[i]), (255, 150, 60) if NUCC[i] else (240, 230, 210), Lv, 0.4, 0.4)
    cx, cy, _ = cam.proj([0, 0, 0])
    g.dot(cx[0], cy[0], 30, (255, 140, 50), 1.0)
    g.apply(img)
    return img, {"nuc": (cx[0], cy[0])}


def ellipse_ring(a, b, z, n=72):
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.stack([a * np.cos(th), b * np.sin(th), np.full(n, z)], 1)


def stadium_mesh():
    V, Fc, cols = [], [], []
    tiers = [(64, 46, 1.5, 92, 70, 14, (34, 52, 98)), (92, 70, 14, 112, 88, 26, (200, 104, 40)), (112, 88, 26, 128, 102, 38, (40, 60, 112))]
    n = 72
    for a0, b0, z0, a1, b1, z1, col in tiers:
        r0, r1 = ellipse_ring(a0, b0, z0, n), ellipse_ring(a1, b1, z1, n)
        for i in range(n):
            j = (i + 1) % n
            k = len(V)
            V += [r0[i], r0[j], r1[j], r1[i]]
            Fc.append([k, k + 1, k + 2, k + 3])
            cols.append(np.array(col) * (0.92 + 0.08 * (i % 2)))
    ro, rg = ellipse_ring(128, 102, 38, n), ellipse_ring(128, 102, 0, n)
    for i in range(n):
        j = (i + 1) % n
        k = len(V)
        V += [rg[i], rg[j], ro[j], ro[i]]
        Fc.append([k, k + 1, k + 2, k + 3]); cols.append(np.array((24, 34, 64)))
    return np.array(V), Fc, np.array(cols, float)


ST_V, ST_F, ST_C = stadium_mesh()


def pitch_lines():
    A, B = [], []
    def seg(p, q): A.append([*p, 0.25]); B.append([*q, 0.25])
    hx, hy = 52.5, 34
    for p, q in [((-hx, -hy), (hx, -hy)), ((hx, -hy), (hx, hy)), ((hx, hy), (-hx, hy)), ((-hx, hy), (-hx, -hy)), ((0, -hy), (0, hy))]:
        P, Q = np.array(p, float), np.array(q, float)
        for k in range(8):
            seg(P + (Q - P) * k / 8, P + (Q - P) * (k + 1) / 8)
    a = np.linspace(0, 2 * np.pi, 48)
    for i in range(47):
        seg((9.15 * math.cos(a[i]), 9.15 * math.sin(a[i])), (9.15 * math.cos(a[i + 1]), 9.15 * math.sin(a[i + 1])))
    for s in (-1, 1):
        box = [(s * hx, -20.15), (s * (hx - 16.5), -20.15), (s * (hx - 16.5), 20.15), (s * hx, 20.15)]
        for p, q in zip(box, box[1:]):
            seg(p, q)
    return np.array(A), np.array(B)


PL_A, PL_B = pitch_lines()


def pitch_tiles():
    V, Fc, cols = [], [], []
    xs = np.linspace(-63, 63, 13); ys = np.linspace(-45, 45, 10)
    for i in range(12):
        for j in range(9):
            k = len(V)
            V += [[xs[i], ys[j], 0.2], [xs[i + 1], ys[j], 0.2], [xs[i + 1], ys[j + 1], 0.2], [xs[i], ys[j + 1], 0.2]]
            Fc.append([k, k + 1, k + 2, k + 3]); cols.append((44, 128, 66) if i % 2 else (34, 110, 56))
    return np.array(V, float), Fc, np.array(cols, float)


PITCH = pitch_tiles()


def s_stadium(t):
    dive = ease_io(prog(t, 12.6, 16.2))
    D = math.exp(lerp(math.log(330), math.log(30), dive))
    cam = E.Cam((0, 0, 0), D, -70 + (t - 9) * 4, lerp(38, 26, dive), y0=900)
    img = E.gradient((8, 12, 30), (26, 34, 62)); E.stars(img, cam, 0.5); g = E.Glow()
    Lw = unit(-120, 55)
    TV, TF, TC = PITCH
    E.mesh(img, cam, TV, TF, TC, Lw, 0.5)
    E.mesh(img, cam, ST_V, ST_F, ST_C, Lw, 0.45, two_sided=True)
    E.lines(img, cam, PL_A, PL_B, (235, 240, 235), width_world=0.14, wmin=1, wmax=10)
    # the "nucleus" pea at the centre spot
    px, py, pz = cam.proj([0, 0, 0.6])
    R = max(cam.f * 0.0035 / pz[0], 5 + 6 * dive)
    pulse = 0.5 + 0.5 * math.sin(t * 5)
    g.dot(px[0], py[0], R * 2.6 + 8 * pulse, (255, 140, 40), 0.9)
    E.sphere(img, px[0], py[0], R, (110, 200, 70), cam.view(Lw), 0.35, 0.6)
    g.apply(img)
    return img, {"pea": (px[0], py[0], R)}


# people on Earth -> sugar cube
LM = np.load("landmask.npy")
cand_lon = rng.uniform(-180, 180, 60000); cand_lat = np.degrees(np.arcsin(rng.uniform(-0.85, 0.95, 60000)))
li = ((90 - cand_lat) / 180 * (LM.shape[0] - 1)).astype(int); lj = ((cand_lon + 180) / 360 * (LM.shape[1] - 1)).astype(int)
land = LM[li, lj] > 128
P_LON, P_LAT = cand_lon[land][:7000], cand_lat[land][:7000]
P_DEL = rng.uniform(0, 1.6, len(P_LON))
P_TGT = rng.uniform(-0.5, 0.5, (len(P_LON), 3))
P_COL = np.array([[255, 196, 120], [255, 150, 70], [255, 230, 180]], np.float32)[rng.integers(0, 3, len(P_LON))]
G_CLON, G_CLAT = 100.0, 15.0


def globe(img, cx, cy, R, clon, clat, Lv, alpha=1.0):
    pad = 8
    x0, x1 = max(0, int(cx - R - pad)), min(W, int(cx + R + pad))
    y0, y1 = max(0, int(cy - R - pad)), min(H, int(cy + R + pad))
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx = (xx - cx) / R; dy = (cy - yy) / R
    r2 = dx * dx + dy * dy
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    p0 = math.radians(clat)
    lat = np.degrees(np.arcsin(np.clip(z * math.sin(p0) + dy * math.cos(p0), -1, 1)))
    lon = clon + np.degrees(np.arctan2(dx, z * math.cos(p0) - dy * math.sin(p0)))
    col = M.sample(lon, lat)
    nl = dx * Lv[0] + dy * Lv[1] + z * Lv[2]
    col = col * (0.2 + 0.8 * np.clip(nl * 1.2 + 0.2, 0, 1))[..., None]
    rr = np.sqrt(r2)
    e = np.clip((1 - rr) * R + 0.5, 0, 1)[..., None] * alpha
    reg = img[y0:y1, x0:x1].astype(np.float32)
    halo = (np.exp(-np.abs(rr - 1) * R / 10) * alpha)[..., None] * np.array([50, 110, 230], np.float32)
    img[y0:y1, x0:x1] = np.clip(reg * (1 - e) + col * e + halo, 0, 255).astype(np.uint8)


def s_squeeze(t):
    cam = E.Cam((0, 0, 0), 8, -90 + (t - 17) * 3, 14, y0=1090)
    img = space_bg(cam); g = E.Glow()
    clon = G_CLON + 4 * min(t - 17, 2.5)
    gx, gy, GR = W / 2, 680, 330
    Lv = np.array([-0.45, 0.4, 0.8]); Lv /= np.linalg.norm(Lv)
    k_all = prog(t, 19.0, 23.6)
    globe(img, gx, gy, GR, clon, G_CLAT, Lv, 1.0 - 0.45 * k_all)
    # people positions on the globe (screen)
    l0, p0 = math.radians(clon), math.radians(G_CLAT)
    lam, phi = np.radians(P_LON), np.radians(P_LAT)
    vis = math.sin(p0) * np.sin(phi) + math.cos(p0) * np.cos(phi) * np.cos(lam - l0)
    sx = gx + GR * np.cos(phi) * np.sin(lam - l0)
    sy = gy - GR * (math.cos(p0) * np.sin(phi) - math.sin(p0) * np.cos(phi) * np.cos(lam - l0))
    s_cube = 0.6
    tx, ty, tz = cam.proj(P_TGT * s_cube)
    u = np.array([ease_io(prog(t, 19.5 + d, 21.6 + d)) for d in P_DEL])
    show = (vis > 0.05) | (u > 0)
    a_light = clamp((t - 17.6) / 0.8)
    # arc: lift outwards from the globe, then fall into the cube
    mx, my = (sx + tx) / 2 + (sx - gx) * 0.5, (sy + ty) / 2 - 160
    X = (1 - u) ** 2 * sx + 2 * (1 - u) * u * mx + u * u * tx
    Y = (1 - u) ** 2 * sy + 2 * (1 - u) * u * my + u * u * ty
    form = ease_io(prog(t, 23.0, 24.2))
    a_p = a_light * (1 - form)
    ok = show & (X > 0) & (X < W - 1) & (Y > 0) & (Y < H - 1)
    if a_p > 0:
        lay = np.zeros((H, W, 3), np.float32)
        np.add.at(lay, (Y[ok].astype(int), X[ok].astype(int)), P_COL[ok] * (0.9 * a_p))
        lay = cv2.GaussianBlur(lay, (0, 0), 1.1) * 2.2
        img[:] = np.clip(img + lay, 0, 255).astype(np.uint8)
        for i in np.nonzero(ok & (u > 0) & (u < 1))[0][::40]:
            g.dot(X[i], Y[i], 8, (255, 160, 70), 0.6 * a_p)
    if form > 0:
        draw_cube(img, cam, g, (0, 0, 0), s_cube, t, alpha=form)
    elif t > 21:
        cx, cy, _ = cam.proj([0, 0, 0])
        g.dot(cx[0], cy[0], 70, (255, 160, 70), 0.6 * prog(t, 21, 23))
    g.apply(img)
    cx, cy, _ = cam.proj([0, 0, 0])
    return img, {"cube": (cx[0], cy[0])}


CRACKS = []
for k in range(11):
    a = rng.uniform(0, 2 * np.pi); pts = [np.array([0.0, 0.0])]
    for s in range(7):
        a += rng.normal(0, 0.35)
        pts.append(pts[-1] + 0.45 * np.array([math.cos(a), math.sin(a)]))
    CRACKS.append(np.array(pts))


def s_weight(t):
    t_hit = 26.9
    fall = prog(t, 26.0, t_hit)
    zc = lerp(5.0, 0.5, fall ** 2)
    shake = 0.0 if t < t_hit else 22 * math.exp(-(t - t_hit) * 5) * math.sin((t - t_hit) * 70)
    cam = E.Cam((0, 0, 0.6), 7.5, -60 + (t - 26) * 4, 20, y0=980 + shake)
    img = E.gradient((8, 12, 30), (30, 34, 58)); g = E.Glow()
    E.grid(img, cam, 12, 1.0, 0, (246, 140, 38), 0.2)
    if t >= t_hit:
        k = t - t_hit
        for r0 in (0.0, 0.35):
            rr = 0.8 + (k - r0) * 9
            if k > r0 and rr < 14:
                a = np.linspace(0, 2 * np.pi, 120)
                E.polyline(img, cam, np.stack([rr * np.cos(a), rr * np.sin(a), np.full(120, 0.02)], 1), (255, 170, 80), 4,
                           alpha=clamp(1 - rr / 14) * 0.9, closed=True)
        grow = clamp(k / 0.6)
        for cr in CRACKS:
            n = max(2, int(len(cr) * grow))
            P = np.concatenate([cr[:n] * 1.0 + np.sign(cr[1]) * 0.5 * 0, np.zeros((n, 1)) + 0.02], 1)
            P[:, :2] += cr[1] / np.linalg.norm(cr[1]) * 0.5
            E.polyline(img, cam, P, (255, 120, 40), 4)
            x, y, _ = cam.proj(P)
            for i in range(n - 1):
                g.line((x[i], y[i]), (x[i + 1], y[i + 1]), 14, (255, 90, 20), 0.6)
        if k < 0.5:
            cx, cy, _ = cam.proj([0, 0, 0])
            g.dot(cx[0], cy[0], 260 * (1 - k * 2), (255, 200, 120), 1.4 * (1 - k * 2))
    draw_cube(img, cam, g, (0, 0, zc), 1.0, t)
    g.apply(img)
    return img, {}


SCENES = [(0, 4.0, s_cube), (4.0, 9.0, s_atom), (9.0, 17.0, s_stadium), (17.0, 26.0, s_squeeze), (26.0, 31.0, s_weight), (31.0, 39.1, s_cube)]
XF = 0.35


def world(t):
    for i, (a, b, fn) in enumerate(SCENES):
        if a <= t < b:
            img, info = fn(t)
            if i + 1 < len(SCENES) and t > b - XF:
                img2, _ = SCENES[i + 1][2](t)
                img = E.blend(img, img2, (t - (b - XF)) / XF)
            return img, info, fn.__name__
    img, info = SCENES[-1][2](t)
    return img, info, "s_cube"


def frame(t):
    img, info, sc = world(t)
    base = Image.fromarray(img).convert("RGBA")
    M.brand(base)
    for txt, a, b in [("ເປີດເລື່ອງ", 0.2, 3.9), ("ອາຕອມ", 4.1, 8.9), ("ທຽບຂະໜາດ", 9.1, 16.9), ("ບີບອັດ", 17.1, 25.9),
                      ("ນ້ຳໜັກ", 26.1, 30.9), ("ບອກຕໍ່", 31.1, 39.5)]:
        M.pill(base, txt, t, a, b)
    E.headline(base, t, 0.2, 3.9, "ມະນຸດທຸກຄົນໃນໂລກ", "ບັນຈຸໃສ່ກ້ອນນ້ຳຕານກ້ອນດຽວໄດ້!", y=430, s1=78, s2=58)
    M.caption(base, "ອາຕອມເກືອບທັງໝົດ ແມ່ນພື້ນທີ່ຫວ່າງເປົ່າ", t, 4.1, 8.9)
    M.card(base, t, 4.8, 8.9, W / 2, 600, "ພື້ນທີ່ຫວ່າງໃນອາຕອມ", "ເກືອບ 100%", "globe")
    if sc == "s_atom" and t > 5.8:
        x, y = info["nuc"]
        E.tag(base, x + 150, y + 120, "ນິວເຄລຍ (ນ້ອຍຫຼາຍ!)", t, 6.0, 8.9, size=40, col=M.ORANGE)
    M.caption(base, "ຖ້າອາຕອມມີຂະໜາດເທົ່າເດີ່ນບານ", t, 9.1, 13.0)
    M.caption(base, "ນິວເຄລຍຢູ່ກາງ ຈະນ້ອຍພຽງເທົ່າເມັດຖົ່ວ", t, 13.0, 16.9)
    M.card(base, t, 9.8, 16.9, 285, 480, "ອາຕອມ", "= ເດີ່ນບານ", "globe")
    M.card(base, t, 13.2, 16.9, 795, 480, "ນິວເຄລຍ", "= ເມັດຖົ່ວ", "star")
    if sc == "s_stadium" and t > 13.4:
        x, y, R = info["pea"]
        E.tag(base, x, y - R - 50, "ເມັດຖົ່ວ = ນິວເຄລຍ", t, 13.6, 16.9, size=42, col=(170, 235, 120))
    M.caption(base, "ຖ້າບີບເອົາພື້ນທີ່ຫວ່າງອອກທັງໝົດ", t, 17.1, 21.4)
    M.caption(base, "ມະນຸດ 8 ພັນລ້ານຄົນ ຈະນ້ອຍເທົ່າກ້ອນນ້ຳຕານ", t, 21.4, 25.9)
    M.card(base, t, 17.6, 25.9, 285, 480, "ມະນຸດທັງໂລກ", "8 ພັນລ້ານຄົນ", "people")
    M.card(base, t, 23.4, 25.9, 795, 480, "ບີບແລ້ວ ເຫຼືອ", "1 ກ້ອນນ້ຳຕານ", "mountain")
    M.caption(base, "ແຕ່ໜັກຫຼາຍຮ້ອຍລ້ານໂຕນ!", t, 26.6, 30.9, size=58, col=M.ORANGE)
    M.card(base, t, 27.2, 30.9, W / 2, 600, "ນ້ຳໜັກ", "ຫຼາຍຮ້ອຍລ້ານໂຕນ", "rank")
    E.headline(base, t, 31.2, 40, "ແບ່ງປັນໃຫ້ໝູ່", "ທີ່ມັກວິທະຍາສາດເບິ່ງແດ່!", y=430, s1=80, s2=62)
    M.caption(base, "ກົດຕິດຕາມ ຮູ້ບໍ່? ໄວ້ເລີຍ", t, 32.0, 35.5, col=(140, 215, 255))
    M.caption(base, C.SHARE_CTA, t, 35.6, 40, y=1640, size=50, col=(120, 210, 255))
    E.footer(base, "ຂໍ້ມູນ: Astronomy.com  |  ພາບປະກອບ 3D ບໍ່ແມ່ນມາດຕາສ່ວນຈິງ")
    return np.asarray(base.convert("RGB"))


if __name__ == "__main__":
    E.main(frame, DUR, "e5")
