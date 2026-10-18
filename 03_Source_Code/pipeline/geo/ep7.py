"""EP.7 ສິລະປະ — ດາວິດ ຂອງ ມີເກລັນເຈໂລ (3D, ~60 s, beat-driven)."""
import math
import numpy as np, cv2
import eng3d as E
from eng3d import M, C, W, H, prog, ease_io, lerp, clamp, unit
import v60 as V

E.setup(7, "ສິລະປະ")
rng = np.random.default_rng(7)
MARBLE = np.array([236, 232, 222.0])
STONE = np.array([176, 156, 124.0])
TERRA = np.array([196, 98, 58.0])


# ---------------- mesh helpers ----------------
def fix_winding(V, faces, center):
    out = []
    for f in faces:
        P = V[f]
        n = np.cross(P[1] - P[0], P[2] - P[0])
        if (P.mean(0) - center) @ n < 0:
            f = f[::-1]
        out.append(list(f))
    return out


def cyl(p0, p1, r0, r1, n=10, caps=True):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    ax = p1 - p0; L = np.linalg.norm(ax); ax /= L
    a = np.cross(ax, [0, 0, 1.0]) if abs(ax[2]) < 0.9 else np.cross(ax, [1.0, 0, 0])
    a /= np.linalg.norm(a); b = np.cross(ax, a)
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring0 = [p0 + r0 * (math.cos(t) * a + math.sin(t) * b) for t in th]
    ring1 = [p1 + r1 * (math.cos(t) * a + math.sin(t) * b) for t in th]
    V = np.array(ring0 + ring1)
    F = [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    if caps:
        F += [list(range(n)), list(range(n, 2 * n))]
    return V, fix_winding(V, F, (p0 + p1) / 2)


def sph(c, r, n=10, m=6, sz=1.0):
    c = np.asarray(c, float)
    V, F = [], []
    for i in range(m + 1):
        ph = -math.pi / 2 + math.pi * i / m
        for j in range(n):
            th = 2 * math.pi * j / n
            V.append(c + r * np.array([math.cos(ph) * math.cos(th), math.cos(ph) * math.sin(th), math.sin(ph) * sz]))
    V = np.array(V)
    for i in range(m):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            c1, d = (i + 1) * n + (j + 1) % n, (i + 1) * n + j
            if i == 0:
                F.append([a, c1, d])
            elif i == m - 1:
                F.append([a, b, d])
            else:
                F.append([a, b, c1, d])
    return V, fix_winding(V, F, c)


def boxm(c, s):
    V, F = E.box(c, s)
    return np.asarray(V, float), [list(f) for f in F]


class Model:
    def __init__(self):
        self.V, self.F, self.C = [], [], []

    def add(self, VF, col):
        V, F = VF
        k = sum(len(v) for v in self.V)
        self.V.append(np.asarray(V, float)); self.F += [[i + k for i in f] for f in F]; self.C += [col] * len(F)
        return self

    def build(self):
        self.Va = np.concatenate(self.V); self.Ca = np.array(self.C, float)
        return self

    def draw(self, img, cam, pos=(0, 0, 0), yaw=0.0, scale=1.0, L=None, ambient=0.38, alpha=1.0, tint=None, spec=0.0):
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
        V = (self.Va * scale) @ R.T + np.asarray(pos, float)
        cols = self.Ca if tint is None else self.Ca * 0 + np.asarray(tint, float)
        E.mesh(img, cam, V, self.F, cols, unit(-125, 48) if L is None else L, ambient, alpha=alpha, spec=spec)


def david(col=MARBLE):
    m = Model()
    J = dict(rhip=(-0.28, 0, 2.65), rknee=(-0.26, 0, 1.45), rank=(-0.25, 0.02, 0.22),
             lhip=(0.28, 0, 2.55), lknee=(0.42, -0.2, 1.45), lank=(0.5, 0.06, 0.22),
             rsho=(-0.62, 0, 4.12), relb=(-0.74, 0.03, 3.35), rwri=(-0.72, 0.0, 2.62),
             lsho=(0.62, 0, 4.25), lelb=(0.8, -0.28, 3.68), lwri=(0.46, -0.36, 4.22))
    add = lambda vf: m.add(vf, col)
    add(cyl(J["rhip"], J["rknee"], 0.25, 0.17)); add(cyl(J["rknee"], J["rank"], 0.17, 0.09))
    add(cyl(J["lhip"], J["lknee"], 0.25, 0.17)); add(cyl(J["lknee"], J["lank"], 0.17, 0.09))
    for k in ("rknee", "lknee"):
        add(sph(J[k], 0.17, 8, 4))
    add(boxm((-0.25, -0.16, 0.09), (0.26, 0.6, 0.18))); add(boxm((0.52, -0.06, 0.09), (0.26, 0.6, 0.18)))
    add(cyl((0, 0.02, 2.4), (0.0, 0.0, 3.05), 0.44, 0.38, 12))           # pelvis
    add(cyl((0, 0.0, 3.0), (0.0, 0.02, 4.18), 0.38, 0.56, 12))           # torso
    add(sph((0, -0.05, 3.75), 0.5, 12, 6, 0.9))                          # chest
    add(cyl((0, 0, 4.15), (0.02, -0.02, 4.5), 0.17, 0.15, 8))            # neck
    add(sph((0.05, -0.03, 4.8), 0.33, 12, 7, 1.12))                      # head (proportionally large)
    add(sph((0.05, 0.05, 4.92), 0.31, 10, 5, 0.9))                       # hair mass
    add(sph(J["rsho"], 0.18, 8, 4)); add(sph(J["lsho"], 0.18, 8, 4))
    add(cyl(J["rsho"], J["relb"], 0.15, 0.11)); add(cyl(J["relb"], J["rwri"], 0.11, 0.08))
    add(cyl(J["lsho"], J["lelb"], 0.15, 0.11)); add(cyl(J["lelb"], J["lwri"], 0.11, 0.08))
    add(sph(J["relb"], 0.11, 8, 4)); add(sph(J["lelb"], 0.11, 8, 4))
    add(sph((-0.72, -0.02, 2.46), 0.16, 8, 5, 1.3))                      # large right hand
    add(sph((0.42, -0.36, 4.3), 0.13, 8, 5))                             # left hand at the shoulder (sling)
    add(cyl((-0.48, 0.28, 0.0), (-0.46, 0.26, 1.3), 0.19, 0.15, 9))       # tree-stump support
    return m.build()


DAVID = david()
PERSON = Model()
for vf in (cyl((0.0, 0, 0), (0, 0, 0.85), 0.11, 0.13), cyl((0, 0, 0.85), (0, 0, 1.45), 0.17, 0.2), sph((0, 0, 1.6), 0.12, 8, 5),
           cyl((-0.22, 0, 1.4), (-0.24, 0, 0.85), 0.05, 0.04), cyl((0.22, 0, 1.4), (0.24, 0, 0.85), 0.05, 0.04)):
    PERSON.add(vf, (70, 86, 120))
PERSON.build()


def sky(top=(8, 13, 32), bot=(34, 42, 74)):
    return E.gradient(top, bot)


def block(img, cam, top, col=MARBLE, L=None, alpha=1.0, w=2.1, d=1.4):
    if top <= 0.02:
        return
    V, F = E.box((0, 0, top / 2 + 0.6), (w, d, top))
    E.mesh(img, cam, V, F, col * 0.97, unit(-125, 48) if L is None else L, 0.45, alpha=alpha)


def pedestal(img, cam, pos=(0, 0, 0), h=0.6, col=(150, 140, 128)):
    V, F = E.box((pos[0], pos[1], pos[2] + h / 2), (2.6, 1.9, h))
    E.mesh(img, cam, V, F, col, unit(-125, 48), 0.4)


# ---------------- scenes ----------------
def s_block(u, T):
    img = sky(); g = E.Glow()
    cam = E.Cam((0, 0, 3.0), 13, -70 + T * 6, 12)
    E.grid(img, cam, 30, 2.0, 0, (246, 140, 38), 0.2)
    pedestal(img, cam)
    block(img, cam, 5.6)
    g.apply(img)
    x, y, _ = cam.proj([0, 0, 6.4])
    return img, {"top": (x[0], y[0])}


CHIPS = rng.uniform(-1, 1, (60, 3))


def chips(img, g, cam, center, t, amount=1.0, spread=0.9):
    for k, (a, b, c) in enumerate(CHIPS):
        ph = (t * 1.7 + k * 0.137) % 1.0
        p = np.array(center) + np.array([a * spread, -0.7 - 0.6 * ph, c * 0.3 + 0.8 * ph - 1.6 * ph * ph])
        x, y, z = cam.proj(p)
        if z[0] > 0:
            cv2.circle(img, E._pt(x[0], y[0]), int((2 + 2 * (1 - ph)) * 16), (240, 236, 228), -1, cv2.LINE_AA, shift=4)
            g.dot(x[0], y[0], 8, (255, 200, 120), amount * (1 - ph))


def s_abandon(u, T, year=1464):
    img = sky(); g = E.Glow()
    cam = E.Cam((0, 0, 2.6), 11, -60 + T * 5, 10)
    E.grid(img, cam, 30, 2.0, 0, (246, 140, 38), 0.2)
    pedestal(img, cam)
    block(img, cam, 5.6, MARBLE * (0.96 if year == 1464 else 0.9))
    if u < 0.55:
        chips(img, g, cam, (0.3, 0, 1.6), T, 1.2 * (1 - u / 0.55))
    if year == 1476:   # a visible flaw: dark crack lines on the front face
        k = ease_io(prog(u, 0.2, 0.6))
        pts = np.array([[0.3 - 0.05 * i + 0.08 * math.sin(i * 1.7), -0.71, 5.6 - i * 0.55 * k] for i in range(9)])
        E.polyline(img, cam, pts, (60, 60, 70), 4)
    g.apply(img)
    x, y, _ = cam.proj([0, -0.7, 3.0])
    return img, {"block": (x[0], y[0])}


s_1464 = lambda u, T: s_abandon(u, T, 1464)
s_1476 = lambda u, T: s_abandon(u, T, 1476)
RAIN = rng.uniform(0, 1, (300, 3))


def s_years(u, T):
    day = 0.5 + 0.5 * math.sin(u * 2 * math.pi * 6)
    top = np.array([8, 13, 32]) * (1 - day) + np.array([60, 110, 170]) * day
    bot = np.array([34, 42, 74]) * (1 - day) + np.array([150, 170, 200]) * day
    img = sky(top, bot); g = E.Glow()
    cam = E.Cam((0, 0, 2.8), 12, -70 + u * 70, 12)
    E.grid(img, cam, 30, 2.0, 0, (246, 140, 38), 0.18)
    sd = unit(-90 + 180 * ((u * 6) % 1), 25 + 30 * math.sin(math.pi * ((u * 6) % 1)))
    x, y, z = cam.proj(cam.pos + sd * 500)
    if z[0] > 0:
        g.dot(x[0], y[0], 60, (255, 200, 110), 1.2 * day)
    pedestal(img, cam)
    block(img, cam, 5.6, MARBLE * (0.95 - 0.18 * u), L=sd)
    rain = max(0.0, math.sin(u * 2 * math.pi * 3))
    if rain > 0.2:
        for a, b, c in RAIN:
            xx = a * W; yy = (b * H + T * 1600) % H
            cv2.line(img, E._pt(xx, yy), E._pt(xx - 8, yy + 34), (170, 190, 220), 2, cv2.LINE_AA, shift=4)
    g.apply(img)
    return img, {"year": int(round(1476 + 25 * u))}


def s_carve(u, T):
    img = sky(); g = E.Glow()
    k = ease_io(prog(u, 0.05, 0.95))
    cam = E.Cam((0, 0, 3.2), lerp(11, 12.5, k), -80 + T * 7, 10)
    E.grid(img, cam, 30, 2.0, 0, (246, 140, 38), 0.2)
    pedestal(img, cam)
    DAVID.draw(img, cam, (0, 0, 0.6), spec=0.15)
    top = 5.6 * (1 - k)
    block(img, cam, top, alpha=0.96)
    if 0.02 < k < 0.98:
        chips(img, g, cam, (0, 0, 0.6 + top), T * 1.6, 1.4)
    g.apply(img)
    return img, {}


def s_compare(u, T):
    img = sky(); g = E.Glow()
    cam = E.Cam((0.8, 0, 3.0), 13.5, -105 + 25 * u, 6)
    E.grid(img, cam, 30, 1.0, 0, (246, 140, 38), 0.2)
    pedestal(img, cam, h=0.0001)
    DAVID.draw(img, cam, (0, 0, 0), spec=0.15)
    k = ease_io(prog(u, 0.1, 0.5))
    PERSON.draw(img, cam, (2.1, -0.3, 0), alpha=k)
    # height bar
    if u > 0.3:
        h = 5.17 * ease_io(prog(u, 0.3, 0.7))
        x0, y0, _ = cam.proj([[-1.4, -0.4, 0], [-1.4, -0.4, h]])
        cv2.line(img, E._pt(x0[0], y0[0]), E._pt(x0[1], y0[1]), (246, 140, 38), 5, cv2.LINE_AA, shift=4)
        for yy in (y0[0], y0[1]):
            cv2.line(img, E._pt(x0[0] - 18, yy), E._pt(x0[0] + 18, yy), (246, 140, 38), 5, cv2.LINE_AA, shift=4)
    xa, ya, _ = cam.proj([-1.4, -0.4, 5.3]); xp, yp, _ = cam.proj([2.1, -0.3, 1.8])
    g.apply(img)
    return img, {"bar": (xa[0], ya[0]), "person": (xp[0], yp[0])}


def cathedral():
    m = Model()
    m.add(boxm((0, 40, 15), (40, 70, 30)), STONE)                        # nave
    m.add(cyl((0, 0, 0), (0, 0, 38), 22, 22, 8), STONE * 1.03)          # octagonal drum
    for i in range(5):                                                   # dome
        z0, z1 = 38 + 26 * math.sin(math.pi / 2 * i / 5), 38 + 26 * math.sin(math.pi / 2 * (i + 1) / 5)
        r0, r1 = 22 * math.cos(math.pi / 2 * i / 5), 22 * math.cos(math.pi / 2 * (i + 1) / 5) + 0.01
        m.add(cyl((0, 0, z0), (0, 0, z1), r0, r1, 8, caps=False), TERRA * (1 - 0.03 * i))
    m.add(cyl((0, 0, 63), (0, 0, 72), 3, 2, 8), (235, 230, 220))         # lantern
    return m.build()


CATH = cathedral()


def s_roof(u, T):
    img = sky((10, 16, 40), (60, 70, 110)); g = E.Glow()
    cam = E.Cam((0, -18, 32), 78, -105 + 12 * u, 10)
    E.grid(img, cam, 160, 10.0, 0, (246, 140, 38), 0.16)
    CATH.draw(img, cam, (0, 0, 0), ambient=0.42)
    # statue hoisted toward the drum edge, then sways and sinks back
    up = ease_io(prog(u, 0.05, 0.5)); down = ease_io(prog(u, 0.62, 0.95))
    z = 34 * up * (1 - down)
    sway = math.sin(T * 9) * 1.2 * prog(u, 0.4, 0.6) * (1 - down)
    pos = np.array([sway, -26, z])
    DAVID.draw(img, cam, pos, yaw=0, scale=1.0)
    rope_top = cam.proj([0, -26, 70]); rope_bot = cam.proj(pos + [0, 0, 5.3])
    cv2.line(img, E._pt(rope_top[0][0], rope_top[1][0]), E._pt(rope_bot[0][0], rope_bot[1][0]), (220, 220, 230), 2, cv2.LINE_AA, shift=4)
    x, y, _ = cam.proj(pos + [0, 0, 2.6])
    heavy = prog(u, 0.45, 0.6) * (1 - prog(u, 0.9, 1.0))
    g.dot(x[0], y[0], 40, (255, 60, 30), 1.4 * heavy * (0.7 + 0.3 * math.sin(T * 10)))
    g.apply(img)
    return img, {"statue": (x[0], y[0]), "heavy": heavy}


def palazzo():
    m = Model()
    m.add(boxm((0, 30, 16), (44, 34, 32)), STONE)
    for i in range(-10, 11, 2):
        m.add(boxm((i * 2.0, 13, 33), (1.6, 1.2, 2.0)), STONE * 0.95)
    m.add(boxm((0, 22, 55), (8, 8, 46)), STONE * 1.04)                 # tower
    m.add(boxm((0, 22, 80), (10, 10, 6)), STONE * 0.97)
    m.add(cyl((0, 22, 83), (0, 22, 92), 2.6, 1.0, 8), STONE * 1.05)
    return m.build()


PAL = palazzo()


def s_piazza(u, T):
    img = sky((12, 18, 44), (90, 90, 120)); g = E.Glow()
    k = ease_io(u)
    cam = E.Cam((0, 2, lerp(20, 4.2, k)), lerp(95, 21, k), lerp(-100, -112, k), lerp(10, 5, k))
    E.grid(img, cam, 80, 5.0, 0, (246, 140, 38), 0.18)
    PAL.draw(img, cam, ambient=0.42)
    pedestal(img, cam, (0, 0, 0), h=1.6)
    DAVID.draw(img, cam, (0, 0, 1.6), spec=0.15)
    x, y, _ = cam.proj([0, 0, 7.4])
    g.apply(img)
    return img, {"statue": (x[0], y[0])}


def s_museum(u, T):
    img = E.gradient((24, 22, 30), (60, 52, 50)); g = E.Glow()
    cam = E.Cam((0, 0, 3.5), lerp(26, 15, ease_io(u)), -90 + 10 * math.sin(T * 0.4), 6)
    wall = np.array([205, 196, 182.0])
    m = Model()
    m.add(boxm((0, 8, -0.05), (14, 40, 0.1)), (120, 100, 85))
    m.add(boxm((-7, 8, 6), (0.4, 40, 12)), wall); m.add(boxm((7, 8, 6), (0.4, 40, 12)), wall)
    m.add(boxm((0, 11, 6), (14, 0.4, 12)), wall * 0.95)
    for zz in (-12, -4, 4):
        m.add(boxm((-6.6, zz, 4), (0.6, 0.8, 8)), wall * 0.9); m.add(boxm((6.6, zz, 4), (0.6, 0.8, 8)), wall * 0.9)
    m.build().draw(img, cam, ambient=0.5)
    pedestal(img, cam, (0, 4, 0), h=1.5)
    DAVID.draw(img, cam, (0, 4, 1.5), spec=0.2)
    x, y, _ = cam.proj([0, 4, 12])
    g.dot(x[0], y[0] + 120, 110, (255, 240, 210), 0.3)                       # skylight
    g.apply(img)
    xs, ys, _ = cam.proj([0, 4, 7.4])
    return img, {"statue": (xs[0], ys[0])}


def s_hero(u, T):
    img = sky(); g = E.Glow()
    cam = E.Cam((0, 0, 3.6), 11.5, -90 + T * 12, 4)
    E.grid(img, cam, 30, 1.0, 0, (246, 140, 38), 0.2)
    pedestal(img, cam, h=0.6)
    DAVID.draw(img, cam, (0, 0, 0.6), spec=0.2)
    g.apply(img)
    return img, {}


ORANGE = M.ORANGE
BEATS = [
    dict(vo="[excited] ຮູບປັ້ນທີ່ດັງທີ່ສຸດໃນໂລກ ເກີດຈາກກ້ອນຫີນອ່ອນ ທີ່ບໍ່ມີໃຜເອົາ!", src=("new", s_block), pill="ເປີດເລື່ອງ",
         head=("ຮູບປັ້ນດັງທີ່ສຸດໃນໂລກ", "ເກີດຈາກຫີນທີ່ບໍ່ມີໃຜເອົາ!"), hs1=74, hs2=60, captions=False),
    dict(vo="ປີ 1464 ຊ່າງປັ້ນ ອາໂກສຕີໂນ ດີ ດູຊໂຊ ເລີ່ມແກະສະຫຼັກ ແຕ່ເຮັດໄດ້ໜ້ອຍດຽວ ກໍປະຖິ້ມ.", src=("new", s_1464), pill="ກ້ອນຫີນ",
         cards=[("ປີ 1464", "ຊ່າງຄົນທີ 1 ປະຖິ້ມ", "flag", 0.15)]),
    dict(vo="ປີ 1476 ມີຊ່າງອີກຄົນມາຮັບຕໍ່ ແຕ່ຖອນຕົວ ເພາະຫີນອ່ອນຄຸນນະພາບບໍ່ດີ.", src=("new", s_1476), pill="ກ້ອນຫີນ",
         cards=[("ປີ 1476", "ຊ່າງຄົນທີ 2 ຖອນຕົວ", "flag", 0.15)],
         tags=[V.tag_at("block", "ຫີນຄຸນນະພາບບໍ່ດີ", dy=-260, size=42, col=(255, 160, 120), t0f=0.45)]),
    dict(vo="ກ້ອນຫີນຖືກປະໄວ້ກາງແຈ້ງ ປະມານ 25 ປີ.", src=("new", s_years), pill="ກ້ອນຫີນ",
         cards=[("ຖືກປະໄວ້ກາງແຈ້ງ", lambda i, T: f"ປີ {i.get('year', 1501)}", "clock", 0.0)]),
    dict(vo="ປີ 1501 ມີເກລັນເຈໂລ ອາຍຸພຽງ 26 ປີ ຮັບວຽກນີ້ ແລະແກະສະຫຼັກຈົນສຳເລັດໃນປີ 1504.", src=("new", s_carve), pill="ມີເກລັນເຈໂລ",
         cards=[("ມີເກລັນເຈໂລ", "ອາຍຸ 26 ປີ", "people", 0.1), ("ແກະສະຫຼັກ", "1501 – 1504", "clock", 0.45)]),
    dict(vo="ຜົນງານຄື ດາວິດ ສູງ 5.17 ແມັດ ໜັກກວ່າ 5 ໂຕນ.", src=("new", s_compare), pill="ດາວິດ",
         cards=[("ຄວາມສູງ", "5.17 ແມັດ", "ruler", 0.15), ("ນ້ຳໜັກ", "ກວ່າ 5 ໂຕນ", "rank", 0.45)],
         tags=[V.tag_at("bar", "5.17 ມ.", dy=-20, size=46, col=ORANGE, t0f=0.5), V.tag_at("person", "ຄົນ 1.7 ມ.", dy=-30, size=36, t0f=0.35)]),
    dict(vo="ເດີມຈະເອົາໄປຕັ້ງເທິງຫຼັງຄາມະຫາວິຫານ ແຕ່ໜັກເກີນໄປ ຍົກບໍ່ຂຶ້ນ.", src=("new", s_roof), pill="ຈະຕັ້ງໄວ້ໃສ?",
         tags=[V.tag_at("statue", "ໜັກເກີນ!", dy=-110, size=50, col=(255, 120, 90), t0f=0.5)]),
    dict(vo="ຄະນະກຳມະການ ທີ່ມີ ເລໂອນາໂດ ດາວິນຊີ ແລະ ບອດຕິເຊລລີ ຈຶ່ງເລືອກຕັ້ງໄວ້ໜ້າສາລາວ່າການເມືອງ ຟລໍເຣນ.", src=("new", s_piazza), pill="ຈະຕັ້ງໄວ້ໃສ?",
         cards=[("ຄະນະກຳມະການ", "ມີ ເລໂອນາໂດ ດາວິນຊີ", "people", 0.1), ("ເປີດຕົວ", "8 ກັນຍາ 1504", "flag", 0.5)]),
    dict(vo="ປີ 1873 ຍ້າຍເຂົ້າພິພິທະພັນ ສ່ວນບ່ອນເດີມ ປັດຈຸບັນແມ່ນຮູບປັ້ນຈຳລອງ.", src=("new", s_museum), pill="ປັດຈຸບັນ",
         cards=[("ປີ 1873", "ຍ້າຍເຂົ້າພິພິທະພັນ", "mountain", 0.1), ("ບ່ອນເດີມ", "ຕົວຈຳລອງ", "star", 0.5)]),
    dict(vo="[curious] ຖ້າໄດ້ໄປ ຟລໍເຣນ ເຈົ້າຢາກເບິ່ງຕົວຈິງ ຫຼື ຕົວຈຳລອງ? ຄອມເມັ້ນບອກແດ່!", src=("new", s_hero), pill="ບອກຕໍ່",
         head=("ຕົວຈິງ ຫຼື ຕົວຈຳລອງ?", "ຄອມເມັ້ນບອກແດ່!"), hs1=74, hs2=62),
    dict(vo="[happy] ຖ້າຮູ້ແລ້ວ ຢ່າລືມ ບອກຕໍ່ ໃຫ້ໝູ່ເດີ້!", src=("new", s_hero), pill="ບອກຕໍ່",
         head=("ຕົວຈິງ ຫຼື ຕົວຈຳລອງ?", "ຄອມເມັ້ນບອກແດ່!"), hs1=74, hs2=62, captions=False, share=True),
]

SHOW = V.Show(BEATS, None, timing_path="out60/EP07_timing.json", min_total=58)

if __name__ == "__main__":
    V.main(SHOW, "ຂໍ້ມູນ: Britannica, Smarthistory  |  ພາບປະກອບ 3D ແບບງ່າຍ", "g7")
