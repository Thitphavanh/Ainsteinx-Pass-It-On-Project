"""EP.5 — 60 s version (beats + new: nucleus holds 99.9% of the mass, neutron star)."""
import math
import numpy as np, cv2
import eng3d as E
from eng3d import M, C, W, H, prog, ease_io, lerp, clamp, unit
import ep5_3d as P5
import v60 as V

E.setup(5, "ຟີຊິກ")


def rotz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def roty(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def field_lines():
    out = []
    th = np.linspace(0.12, math.pi - 0.12, 90)
    for Lshell in (1.8, 2.6, 3.6):
        for k in range(8):
            ph = k * math.pi / 4
            r = Lshell * np.sin(th) ** 2
            pts = np.stack([r * np.sin(th) * math.cos(ph), r * np.sin(th) * math.sin(ph), r * np.cos(th)], 1)
            pts = pts[np.linalg.norm(pts, axis=1) > 1.02]
            out.append(pts)
    return out


FIELD = field_lines()


def s_neutron(u, T):
    zoom = ease_io(clamp(u))
    cam = E.Cam((0, 0, 0), lerp(13, 8.5, zoom), 25 + T * 6, 12, y0=860)
    img = P5.space_bg(cam); g = E.Glow()
    spin = T * 2.4
    R = rotz(spin) @ roty(math.radians(28))            # magnetic axis tilted from the spin axis
    for pts in FIELD:
        P = pts @ R.T
        E.polyline(img, cam, P, (110, 160, 255), 2, alpha=0.45)
    # pulsar beams
    ax = R @ np.array([0, 0, 1.0])
    for s in (1, -1):
        a = cam.proj(ax * s * 1.05); b = cam.proj(ax * s * 7.5)
        if a[2][0] > 0 and b[2][0] > 0:
            for w, al in ((70, 0.35), (34, 0.7), (12, 1.2)):
                g.line((a[0][0], a[1][0]), (b[0][0], b[1][0]), w, (150, 200, 255), al)
    x, y, z = cam.proj([0, 0, 0])
    Rs = cam.f * 1.0 / z[0]
    g.dot(x[0], y[0], Rs * 2.6, (90, 140, 255), 1.0)
    E.sphere(img, x[0], y[0], Rs, (205, 225, 255), cam.view(unit(-120, 40)), 0.55, 0.7, rim=(120, 170, 255))
    g.apply(img)
    return img, {"ns": (x[0], y[0], Rs)}


BEATS = [
    dict(vo="[excited] ມະນຸດທຸກຄົນໃນໂລກ ບັນຈຸໃສ່ກ້ອນນ້ຳຕານກ້ອນດຽວໄດ້!", src=("old", 0.0, 3.8), pill="ເປີດເລື່ອງ",
         head=("ມະນຸດທຸກຄົນໃນໂລກ", "ບັນຈຸໃສ່ກ້ອນນ້ຳຕານກ້ອນດຽວໄດ້!"), hs1=78, hs2=58, captions=False),
    dict(vo="ອາຕອມເກືອບທັງໝົດ ແມ່ນພື້ນທີ່ຫວ່າງເປົ່າ.", src=("old", 4.0, 6.5), pill="ອາຕອມ",
         cards=[("ພື້ນທີ່ຫວ່າງໃນອາຕອມ", "ເກືອບ 100%", "globe", 0.2)]),
    dict(vo="ຢູ່ກາງແມ່ນນິວເຄລຍ ສ່ວນອີເລັກຕຣອນ ແລ່ນອ້ອມຢູ່ໄກແສນໄກ.", src=("old", 6.5, 8.6), pill="ອາຕອມ",
         tags=[V.tag_at("nuc", "ນິວເຄລຍ", dy=110, dx=120, size=42, col=M.ORANGE, t0f=0.05),
               V.tag_fixed(W / 2, 360, "ອີເລັກຕຣອນ ແລ່ນອ້ອມຢູ່ໄກ", 40, (150, 210, 255), 0.4)]),
    dict(vo="[curious] ຖ້າອາຕອມມີຂະໜາດເທົ່າເດີ່ນບານ ນິວເຄລຍຢູ່ກາງຈະນ້ອຍພຽງເທົ່າເມັດຖົ່ວ.", src=("old", 9.0, 16.2), pill="ທຽບຂະໜາດ",
         cards=[("ອາຕອມ", "= ເດີ່ນບານ", "globe", 0.1), ("ນິວເຄລຍ", "= ເມັດຖົ່ວ", "star", 0.5)],
         tags=[V.tag_at("pea", "ເມັດຖົ່ວ = ນິວເຄລຍ", dy=-60, size=42, col=(170, 235, 120), t0f=0.55)]),
    dict(vo="ແຕ່ນ້ຳໜັກຂອງອາຕອມ ຫຼາຍກວ່າ 99.9% ຢູ່ໃນເມັດຖົ່ວນ້ອຍໆນັ້ນ!", src=("old", 16.2, 16.6), pill="ທຽບຂະໜາດ",
         cards=[("ນ້ຳໜັກຢູ່ໃນນິວເຄລຍ", "ຫຼາຍກວ່າ 99.9%", "rank", 0.15)],
         tags=[V.tag_at("pea", "ເມັດຖົ່ວ = ນິວເຄລຍ", dy=-60, size=42, col=(170, 235, 120), t0f=0.0)]),
    dict(vo="ຖ້າບີບເອົາພື້ນທີ່ຫວ່າງອອກທັງໝົດ ມະນຸດ 8 ພັນລ້ານຄົນ ຈະນ້ອຍເທົ່າກ້ອນນ້ຳຕານ", src=("old", 17.0, 26.0), pill="ບີບອັດ",
         cards=[("ມະນຸດທັງໂລກ", "8 ພັນລ້ານຄົນ", "people", 0.05), ("ບີບແລ້ວ ເຫຼືອ", "1 ກ້ອນນ້ຳຕານ", "mountain", 0.7)]),
    dict(vo="[surprised] ແຕ່ໜັກຫຼາຍຮ້ອຍລ້ານໂຕນ!", src=("old", 26.0, 30.6), pill="ນ້ຳໜັກ",
         cards=[("ນ້ຳໜັກ", "ຫຼາຍຮ້ອຍລ້ານໂຕນ", "rank", 0.25)], capcol=M.ORANGE),
    dict(vo="ໃນອະວະກາດ ມີສິ່ງທີ່ອັດແໜ້ນແບບນີ້ແທ້ໆ ເອີ້ນວ່າ ດາວນິວຕຣອນ.", src=("new", s_neutron), pill="ດາວນິວຕຣອນ",
         tags=[V.tag_at("ns", "ດາວນິວຕຣອນ", dy=230, size=48, col=(150, 210, 255), t0f=0.35)]),
    dict(vo="ກວ້າງພຽງ 20 ກິໂລແມັດ ແຕ່ໜັກກວ່າດວງອາທິດ ເນື້ອດາວແຄ່ບ່ວງກາເຟດຽວ ໜັກປະມານພັນລ້ານໂຕນ!", src=("new", s_neutron), pill="ດາວນິວຕຣອນ",
         cards=[("ຂະໜາດ", "ກວ້າງ 20 ກມ.", "ruler", 0.05), ("ບ່ວງກາເຟດຽວ", "~ພັນລ້ານໂຕນ", "rank", 0.55)]),
    dict(vo="[warmly] ແບ່ງປັນໃຫ້ໝູ່ທີ່ມັກວິທະຍາສາດເບິ່ງແດ່!", src=("old", 31.0, 35.5), pill="ບອກຕໍ່",
         head=("ແບ່ງປັນໃຫ້ໝູ່", "ທີ່ມັກວິທະຍາສາດເບິ່ງແດ່!"), hs1=80, hs2=62, captions=False),
    dict(vo="[happy] ຖ້າຮູ້ແລ້ວ ຢ່າລືມ ບອກຕໍ່ ໃຫ້ໝູ່ເດີ້!", src=("old", 35.5, 39.0), pill="ບອກຕໍ່",
         head=("ແບ່ງປັນໃຫ້ໝູ່", "ທີ່ມັກວິທະຍາສາດເບິ່ງແດ່!"), hs1=80, hs2=62, captions=False, share=True),
]


def old_world(t):
    return P5.world(t)


SHOW = V.Show(BEATS, old_world, timing_path="out60/EP05_timing.json")

if __name__ == "__main__":
    V.main(SHOW, "ຂໍ້ມູນ: Astronomy.com, US DOE  |  ພາບປະກອບ 3D ບໍ່ແມ່ນມາດຕາສ່ວນຈິງ", "f5")
