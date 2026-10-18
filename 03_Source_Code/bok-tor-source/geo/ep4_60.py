"""EP.4 — 60 s version (beats + new scenes: construction, winter shrink, bridge buckling)."""
import math
import numpy as np, cv2
import eng3d as E
from eng3d import M, C, W, H, prog, ease_io, lerp, clamp, unit
import ep4_3d as P4
import v60 as V

E.setup(4, "ວິສະວະກຳ")
rng = np.random.default_rng(8)


def s_build(u, T):
    img = P4.sky(); g = E.Glow()
    cam = E.Cam((0, 0, 150), 640, 40 + T * 7, 8)
    sd = P4.sun_dir(T * 7 - 100, 28)
    P4.draw_sun(img, g, cam, sd)
    P4.ground(img, cam)
    cut = 335 * ease_io(clamp(u / 0.72))
    A, B, cols, Wd, N = P4.tower_segments(0, np.zeros(2), sd[:2] / np.linalg.norm(sd[:2]), 0.2)
    keep = np.maximum(A[:, 2], B[:, 2]) <= cut + 0.01
    for V_, Fc in P4.platforms(0, np.zeros(2)):
        if V_[:, 2].max() <= cut:
            E.mesh(img, cam, V_, Fc, (200, 140, 80), sd, 0.45)
    xa, ya, za = cam.proj(A[keep]); xb, yb, zb = cam.proj(B[keep])
    cc, ww = cols[keep], Wd[keep]
    for i in np.argsort(-(za + zb)):
        w = clamp(cam.f * ww[i] / ((za[i] + zb[i]) / 2), 1, 9)
        cv2.line(img, E._pt(xa[i], ya[i]), E._pt(xb[i], yb[i]), tuple(float(c) for c in cc[i]), max(1, int(round(w))), cv2.LINE_AA, shift=4)
    if cut < 330:   # rivet sparks at the build line
        hw = P4.wz(min(cut, 312))
        pts = np.array([[sx * hw, sy * hw, cut] for sx in (-1, 1) for sy in (-1, 1)])
        x, y, z = cam.proj(pts)
        for k in range(4):
            fl = 0.6 + 0.4 * math.sin(T * 40 + k * 2)
            g.dot(x[k], y[k], 22, (255, 170, 60), 1.4 * fl)
    xt, yt, _ = cam.proj([0, 0, 330])
    g.apply(img)
    return img, {"top": (xt[0], yt[0])}


SNOW = rng.uniform(0, 1, (420, 3))


def s_cold(u, T):
    img = P4.sky(); g = E.Glow()
    cam = E.Cam((0, 0, 165), 600, -90 + T * 1.5, 8)
    P4.ground(img, cam, 0.16)
    shrink = -0.06 * ease_io(prog(u, 0.15, 0.6))
    tip = P4.draw_tower(img, cam, grow=shrink, sun=None, heat=0.0)
    # cold tint
    f = img.astype(np.float32)
    lum = f.mean(2, keepdims=True)
    f = f * 0.55 + lum * np.array([0.55, 0.75, 1.05], np.float32) * 0.6
    img[:] = np.clip(f, 0, 255).astype(np.uint8)
    info = {}
    if shrink < -0.002:
        x0, y0, _ = cam.proj([[-40, 0, 330], [40, 0, 330]])
        cv2.line(img, E._pt(x0[0], y0[0]), E._pt(x0[1], y0[1]), (220, 230, 255), 2, cv2.LINE_AA, shift=4)
        xt, yt, _ = cam.proj(tip)
        ax = x0[1] + 40
        cv2.arrowedLine(img, E._pt(ax, y0[0]), E._pt(ax, yt[0]), (150, 210, 255), 4, cv2.LINE_AA, shift=4, tipLength=0.3)
        info["dim"] = (ax + 20, (y0[0] + yt[0]) / 2)
    # snow
    for sx, sy, sz in SNOW:
        x = (sx * W + math.sin(T * 1.3 + sz * 9) * 30) % W
        y = (sy * H + T * (60 + 80 * sz)) % H
        r = 1.5 + 2.5 * sz
        cv2.circle(img, E._pt(x, y), int(r * 16), (235, 245, 255), -1, cv2.LINE_AA, shift=4)
    g.apply(img)
    return img, info


def s_buckle(u, T):
    img = E.gradient((30, 12, 18), (70, 34, 30)); g = E.Glow()
    cam = E.Cam((0, 0, 4), 80, -100 + T * 0.8, 12)
    sd = unit(-30, 45)
    P4.draw_sun(img, g, cam, sd)
    P4.ground(img, cam, 0.15)
    lift = 7.0 * ease_io(prog(u, 0.25, 0.7))
    shake = 0.12 * math.sin(T * 60) * (prog(u, 0.2, 0.3) - prog(u, 0.7, 0.8))
    for (V_, Fc), col in P4.bridge_geom(0.0):
        V_ = V_.copy()
        if abs(V_[:, 0]).max() < 45 and V_[:, 2].min() > 6:      # deck parts, not piers
            d = np.clip(1 - np.abs(V_[:, 0]) / 20.0, 0, 1)
            V_[:, 2] += lift * d ** 1.6 + shake
        E.mesh(img, cam, V_, Fc, col, sd, 0.4)
    x, y, _ = cam.proj([0, 0, 9.4 + lift])
    hot = prog(u, 0.15, 0.4)
    g.dot(x[0], y[0], 55, (255, 60, 20), 1.3 * hot * (0.7 + 0.3 * math.sin(T * 8)))
    g.apply(img)
    return img, {"joint": (x[0], y[0])}


TIP = (140, 215, 255)
BEATS = [
    dict(vo="[excited] ຍອດຫໍໄອເຟລ ເຄື່ອນທີ່ທຸກມື້ ຕາມດວງອາທິດ!", src=("old", 0.0, 2.9), pill="ເປີດເລື່ອງ",
         head=("ຍອດຫໍໄອເຟລ", "ເຄື່ອນທີ່ທຸກມື້ ຕາມດວງອາທິດ!"), hs1=84, hs2=62, captions=False),
    dict(vo="ຫໍສູງ 330 ແມັດ ສ້າງສຳເລັດປີ 1889 ໃຊ້ເຫຼັກ 18,038 ຊິ້ນ ແລະໝຸດຍ້ຳ 2.5 ລ້ານໂຕ.", src=("new", s_build), pill="ຮູ້ຈັກຫໍໄອເຟລ",
         cards=[("ຄວາມສູງ / ສ້າງສຳເລັດ", "330 ມ. · ປີ 1889", "ruler", 0.05), ],
         tags=[V.tag_at("top", "330 ມ.", dy=-30, size=46, col=M.ORANGE, t0f=0.55)]),
    dict(vo="ແລະເຫຼັກ ຮ້ອນແລ້ວຈະຂະຫຍາຍຕົວ.", src=("old", 3.6, 9.0), pill="ເຫຼັກ",
         cards=[("ເຫຼັກ / ໝຸດຍ້ຳ", "18,038 ຊິ້ນ · 2.5 ລ້ານ", "mountain", 0.0)],
         tags=[V.tag_fixed(W / 2, 360, "ອາຕອມເຫຼັກ ສັ່ນແຮງຂຶ້ນ ແລະ ຫ່າງກັນອອກ", 40, (255, 200, 140), 0.45)]),
    dict(vo="ໃນມື້ຮ້ອນ ຫໍຈະສູງຂຶ້ນຫຼາຍມິນລີແມັດ.", src=("old", 9.0, 12.6), pill="ຮ້ອນ ແລະ ໜາວ",
         cards=[("ມື້ຮ້ອນ", "+ ຫຼາຍ ມມ.", "sun", 0.1)], tags=[V.tag_at("dim", "+ ຫຼາຍ ມມ.", dy=14, dx=120, col=TIP, t0f=0.25)],
         note="(ຂະຫຍາຍເກີນຈິງ ເພື່ອໃຫ້ເຫັນ)"),
    dict(vo="ສ່ວນໃນລະດູໜາວ ເຫຼັກຫົດຕົວ ຫໍກໍເຕ້ຍລົງຄືນ.", src=("new", s_cold), pill="ຮ້ອນ ແລະ ໜາວ",
         cards=[("ລະດູໜາວ", "- ຫຼາຍ ມມ.", "globe", 0.1)], tags=[V.tag_at("dim", "- ຫຼາຍ ມມ.", dy=14, dx=120, col=TIP, t0f=0.3)],
         note="(ຂະຫຍາຍເກີນຈິງ ເພື່ອໃຫ້ເຫັນ)"),
    dict(vo="[curious] ແຕ່ທີ່ໜ້າງຶດກວ່ານັ້ນ: ແດດສ່ອງພຽງດ້ານດຽວ ດ້ານນັ້ນຈຶ່ງຂະຫຍາຍຫຼາຍກວ່າ ເຮັດໃຫ້ຍອດຫໍອ່ຽງໜີແດດ.", src=("old", 13.0, 21.0), pill="ອ່ຽງໜີແດດ",
         cards=[("ດ້ານຖືກແດດ", "ຮ້ອນ ຂະຫຍາຍ", "sun", 0.1), ("ດ້ານຮົ່ມ", "ເຢັນ ຂະຫຍາຍໜ້ອຍ", "flag", 0.3)],
         tags=[V.tag_at("tip", "ອ່ຽງໜີແດດ", dy=-40, size=46, col=TIP, t0f=0.5)], note="(ຂະຫຍາຍເກີນຈິງ ເພື່ອໃຫ້ເຫັນ)"),
    dict(vo="ໃນມື້ແດດອອກ ຍອດຫໍຈະເຄື່ອນເປັນວົງ ກວ້າງປະມານ 15 ຊັງຕີແມັດ ຕາມການເຄື່ອນຂອງດວງອາທິດ.", src=("old", 21.0, 27.0), pill="ຕາມດວງອາທິດ",
         cards=[("ເສັ້ນທາງຂອງຍອດຫໍ", "ວົງກວ້າງ 15 ຊມ.", "ruler", 0.3)], note="(ຂະຫຍາຍເກີນຈິງ ເພື່ອໃຫ້ເຫັນ)"),
    dict(vo="ນີ້ຄືເຫດຜົນທີ່ຂົວ ແລະທາງລົດໄຟ ຕ້ອງມີຮ່ອງຂະຫຍາຍຕົວ.", src=("old", 27.0, 31.0), pill="ວິສະວະກຳ",
         tags=[V.tag_at("gap", "ຮ່ອງຂະຫຍາຍຕົວ", dy=70, size=46, col=M.ORANGE, t0f=0.2)]),
    dict(vo="ຖ້າບໍ່ມີຮ່ອງນີ້ ໃນມື້ຮ້ອນ ພື້ນຂົວຈະດັນກັນ ຈົນໂກ່ງ ຫຼື ແຕກໄດ້!", src=("new", s_buckle), pill="ວິສະວະກຳ",
         cards=[("ບໍ່ມີຮ່ອງຂະຫຍາຍ", "ຂົວໂກ່ງ!", "flag", 0.45)],
         tags=[V.tag_at("joint", "ດັນກັນ ຈົນໂກ່ງ!", dy=-90, size=48, col=(255, 140, 90), t0f=0.45)]),
    dict(vo="[warmly] ລອງສັງເກດຂົວໃກ້ບ້ານ ເຈົ້າຈະເຫັນຮ່ອງນ້ອຍໆ ນັ້ນແຫຼະຄືເຫດຜົນ! ກົດຕິດຕາມໄວ້ ມື້ອື່ນມີເລື່ອງໃໝ່.", src=("old", 31.0, 36.4), pill="ວິສະວະກຳ",
         tags=[V.tag_at("gap", "ຮ່ອງຂະຫຍາຍຕົວ", dy=70, size=46, col=M.ORANGE, t0f=0.05)]),
    dict(vo="[happy] ຖ້າຮູ້ແລ້ວ ຢ່າລືມ ບອກຕໍ່ ໃຫ້ໝູ່ເດີ້!", src=("old", 36.4, 41.0), pill="ບອກຕໍ່",
         head=("ຮ້ອນຂະຫຍາຍ ເຢັນຫົດ", "ວິສະວະກອນຕ້ອງຄິດໄວ້ກ່ອນ!"), hs1=72, hs2=60, captions=False, share=True),
]


def old_world(t):
    return P4.world(t)


SHOW = V.Show(BEATS, old_world, timing_path="out60/EP04_timing.json")

if __name__ == "__main__":
    V.main(SHOW, "ຂໍ້ມູນ: La Tour Eiffel (ທາງການ)  |  ພາບປະກອບ 3D", "f4")
