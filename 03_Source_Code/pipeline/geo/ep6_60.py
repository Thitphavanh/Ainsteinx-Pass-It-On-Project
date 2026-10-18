"""EP.6 — 60 s version of 1 ປີແສງ (beats + new Andromeda scene)."""
import math
import numpy as np, cv2
import lightyear as LY
import eng3d as E
from eng3d import M, C, W, H, prog, ease_io, lerp, clamp, unit
import v60 as V

E.setup(6, "ອາວະກາດ")
rng = np.random.default_rng(31)


def galaxy(n, arms=2, r=1.0, tight=3.2, seed=0):
    g = np.random.default_rng(seed)
    t = g.uniform(0, 1, n) ** 0.7
    arm = g.integers(0, arms, n)
    ang = arm * 2 * np.pi / arms + tight * t * 2 * np.pi * 0.35 + g.normal(0, 0.28, n) * (1 - 0.5 * t)
    rad = r * t
    P = np.stack([rad * np.cos(ang), rad * np.sin(ang), g.normal(0, 0.035, n) * r * (1.2 - t)], 1)
    core = g.normal(0, 0.12 * r, (n // 5, 3)) * np.array([1, 1, 0.5])
    P = np.concatenate([P, core])
    tt = np.concatenate([t, np.zeros(len(core))])
    col = np.array([255, 214, 160.0]) * (1 - tt[:, None]) + np.array([150, 190, 255.0]) * tt[:, None]
    return P, col


AND_P, AND_C = galaxy(14000, seed=1)
MW_P, MW_C = galaxy(9000, seed=2)


def tilt(P, ax, deg):
    a = math.radians(deg)
    if ax == "x":
        R = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    else:
        R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    return P @ R.T


A_POS, M_POS = np.array([1.6, 0, 3.6]), np.array([-1.4, 0, -3.4])


def splat(img, cam, P, col, gain=1.0):
    x, y, z = cam.proj(P)
    ok = (z > 0) & (x >= 0) & (x < W - 1) & (y >= 0) & (y < H - 1)
    lay = np.zeros((H, W, 3), np.float32)
    np.add.at(lay, (y[ok].astype(int), x[ok].astype(int)), col[ok] * 0.35 * gain)
    sharp = cv2.GaussianBlur(lay, (0, 0), 1.0) * 2.2
    soft = cv2.GaussianBlur(cv2.resize(lay, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 3)
    soft = cv2.resize(soft, (W, H)) * 5.0
    img[:] = np.clip(img.astype(np.float32) + sharp + soft, 0, 255).astype(np.uint8)


def s_andromeda(u, T):
    cam = E.Cam((0, 0, 0), lerp(20, 18.5, ease_io(u)), -90 + 8 * u, 6, y0=860)
    img = E.gradient((4, 6, 16), (10, 14, 32)); E.stars(img, cam, 0.8)
    rot = T * 0.05
    PA = tilt(tilt(AND_P * 1.6, "x", 77) @ np.array([[math.cos(rot), -math.sin(rot), 0], [math.sin(rot), math.cos(rot), 0], [0, 0, 1]]).T, "y", 20) + A_POS
    PM = tilt(MW_P * 1.25, "x", 60) + M_POS
    splat(img, cam, PA, AND_C, 1.0)
    splat(img, cam, PM, MW_C, 0.9)
    g = E.Glow()
    k = ease_io(prog(u, 0.15, 0.85))
    a = cam.proj(A_POS); b = cam.proj(M_POS)
    pa, pb = (a[0][0], a[1][0]), (b[0][0], b[1][0])
    ph = (lerp(pa[0], pb[0], k), lerp(pa[1], pb[1], k))
    if k > 0:
        g.line(pa, ph, 10, (60, 140, 255), 0.9)
        cv2.line(img, E._pt(*pa), E._pt(*ph), (170, 225, 255), 3, cv2.LINE_AA, shift=4)
        if k < 1:
            g.dot(ph[0], ph[1], 28, (190, 235, 255), 2.2)
    g.dot(pb[0], pb[1], 10, (255, 230, 160), 1.5 * k)
    g.apply(img)
    return img, {"and": (pa[0], pa[1]), "mw": (pb[0], pb[1]), "yrs": 2.5 * k}


def old_world(t):
    img, info = LY.scene(t)
    return np.clip(img, 0, 255).astype(np.uint8), info, ""


def body_tag(key, text, dy=52, size=40, col=(255, 248, 236), t0f=0.1):
    def f(base, info, T, w0, w1):
        if key in info:
            x, y, R = info[key][:3]
            yy = y + (R + dy if key in ("earth", "moon", "sun") else dy)
            E.tag(base, x, yy, text, T, w0 + t0f * (w1 - w0), w1 - 0.05, size=size, col=col)
    return f


def ring_tag(base, info, T, w0, w1):
    if "ly_ring" in info:
        x, y, z = info["ly_ring"]
        E.tag(base, float(x[0]) - 20, float(y[0]) + 64, "1 ປີແສງ", T, w0 + 0.3 * (w1 - w0), w1 - 0.05, size=46, col=M.ORANGE)


def mmss(s):
    s = int(round(s))
    return f"{s // 60} ນາທີ {s % 60:02d} ວິ"


BEATS = [
    dict(vo="[excited] 1 ປີແສງ ໄກປານໃດກັນແທ້?", src=("old", 0.0, 5.0), pill="ເປີດເລື່ອງ", head=("1 ປີແສງ", "ໄກປານໃດກັນແທ້?"), hs1=110, hs2=72, captions=False),
    dict(vo="ແສງໄວທີ່ສຸດໃນຈັກກະວານ ວິນາທີລະ 300,000 ກິໂລແມັດ", src=("old", 5.0, 8.2), pill="ຄວາມໄວແສງ",
         cards=[("ຄວາມໄວແສງ", "300,000 ກມ./ວິ", "bolt", 0.1)]),
    dict(vo="ແຄ່ 1 ວິນາທີ ແສງອ້ອມໂລກໄດ້ 7.5 ຮອບ", src=("old", 8.2, 11.2), pill="ຄວາມໄວແສງ",
         cards=[("ຄວາມໄວແສງ", "300,000 ກມ./ວິ", "bolt", 0.0), ("ແສງ 1 ວິນາທີ", lambda i, T: f"{i.get('laps', 7.5):.1f} ຮອບໂລກ", "globe", 0.0)]),
    dict(vo="ຈາກໂລກ ໄປດວງເດືອນ ໄກ 384,400 ກິໂລແມັດ ແສງໃຊ້ເວລາແຄ່ 1.3 ວິນາທີ", src=("old", 11.2, 18.0), pill="ໂລກ ຫາ ດວງເດືອນ",
         tags=[body_tag("earth", "ໂລກ"), body_tag("moon", "ດວງເດືອນ")],
         cards=[("ເວລາທີ່ແສງໃຊ້", lambda i, T: f"{i.get('moon_t', 1.282 if T > 0 else 0):.2f} ວິນາທີ", "clock", 0.35)]),
    dict(vo="ແສງຈາກດວງອາທິດ ກວ່າຈະມາຮອດໂລກ ໃຊ້ເວລາ 8 ນາທີ 20 ວິນາທີ", src=("old", 18.0, 25.0), pill="ດວງອາທິດ ຫາ ໂລກ",
         tags=[body_tag("sun", "ດວງອາທິດ", dy=60, t0f=0.25), body_tag("earth", "ໂລກ", t0f=0.25)],
         cards=[("ເວລາທີ່ແສງໃຊ້", lambda i, T: mmss(i.get("sun_t", 499)), "sun", 0.3)]),
    dict(vo="ຍານ Voyager 1 ບິນມາ 49 ປີ ເດືອນພະຈິກນີ້ ຈະໄກຮອດ 1 ວັນແສງ", src=("old", 25.0, 32.0), pill="1 ວັນແສງ",
         tags=[body_tag("voy", "Voyager 1", dy=-26, t0f=0.25)], cards=[("ບິນມາແລ້ວ", "49 ປີ", "probe", 0.2), ("ແສງໃຊ້ເວລາ", "1 ວັນ", "clock", 0.55)]),
    dict(vo="ແສງເດີນທາງ 1 ປີເຕັມ ເອີ້ນວ່າ 1 ປີແສງ", src=("old", 32.0, 35.8), pill="1 ປີແສງ",
         tags=[body_tag("sun", "ດວງອາທິດ", dy=60, size=36, t0f=0.4)],
         cards=[("ແສງເດີນທາງມາແລ້ວ", lambda i, T: f"{int(i.get('days', 0))} ວັນ", "clock", 0.3)]),
    dict(vo="ໄກ 9.46 ລ້ານລ້ານ ກິໂລແມັດ", src=("old", 35.8, 38.4), pill="1 ປີແສງ",
         tags=[ring_tag, body_tag("sun", "ດວງອາທິດ", dy=60, size=36, t0f=0)],
         cards=[("1 ປີແສງ", "9.46 ລ້ານລ້ານ ກມ.", "ruler", 0.1)]),
    dict(vo="ຖ້າຂັບລົດ 100 ກມ. ຕໍ່ຊົ່ວໂມງ ຕ້ອງໃຊ້ເວລາ 10.8 ລ້ານປີ!", src=("old", 38.4, 41.0), pill="1 ປີແສງ",
         tags=[ring_tag], cards=[("1 ປີແສງ", "9.46 ລ້ານລ້ານ ກມ.", "ruler", 0.0), ("ຂັບລົດ 100 ກມ./ຊມ.", "10.8 ລ້ານປີ", "car", 0.25)]),
    dict(vo="ດາວທີ່ໃກ້ເຮົາທີ່ສຸດ ໄກ 4.24 ປີແສງ ແສງທີ່ເຮົາເຫັນ ອອກມາຕັ້ງແຕ່ 4 ປີກ່ອນ!", src=("old", 41.0, 46.4), pill="ດາວທີ່ໃກ້ທີ່ສຸດ",
         tags=[body_tag("prox", "Proxima Centauri", dy=66, size=38, t0f=0.2)], cards=[("Proxima Centauri", "4.24 ປີແສງ", "star", 0.25)]),
    dict(vo="[curious] ສ່ວນກາລັກຊີແອນໂດຣເມດາ ແສງທີ່ເຮົາເຫັນມື້ນີ້ ເດີນທາງມາ 2.5 ລ້ານປີແລ້ວ!",
         src=("new", s_andromeda), pill="ກາລັກຊີ",
         tags=[V.tag_at("and", "ແອນໂດຣເມດາ", dy=-150, size=44, col=(255, 220, 170), t0f=0.05),
               V.tag_at("mw", "ທາງຊ້າງເຜືອກ (ເຮົາຢູ່ນີ້)", dy=125, size=40, col=(170, 215, 255), t0f=0.2)],
         cards=[("ແອນໂດຣເມດາ", "2.5 ລ້ານປີແສງ", "star", 0.3)]),
    dict(vo="ຈື່ໄວ້ ປີແສງ ແມ່ນໄລຍະທາງ! ເຈົ້າຢາກໄປດາວດວງໃດ? ຄອມເມັ້ນເລີຍ!", src=("old", 46.4, 49.6), pill="ບອກຕໍ່",
         head=("ປີແສງ ແມ່ນໄລຍະທາງ ບໍ່ແມ່ນເວລາ!", "ເຈົ້າຢາກໄປດາວດວງໃດ? ຄອມເມັ້ນເລີຍ!"), hs1=60, hs2=54),
    dict(vo="[happy] ຖ້າຮູ້ແລ້ວ ຢ່າລືມ ບອກຕໍ່ ໃຫ້ໝູ່ເດີ້!", src=("old", 49.6, 51.0), pill="ບອກຕໍ່",
         head=("ປີແສງ ແມ່ນໄລຍະທາງ ບໍ່ແມ່ນເວລາ!", "ເຈົ້າຢາກໄປດາວດວງໃດ? ຄອມເມັ້ນເລີຍ!"), hs1=60, hs2=54, captions=False, share=True),
]

SHOW = V.Show(BEATS, old_world, timing_path="out60/EP06_timing.json")

if __name__ == "__main__":
    V.main(SHOW, "ຂໍ້ມູນ: IAU, NASA/JPL, NASA/STScI  |  ພາບປະກອບ ບໍ່ຕາມສັດສ່ວນຈິງ", "f6")
