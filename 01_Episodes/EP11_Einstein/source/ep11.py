"""EP.11 — ປະຫວັດ ອັລເບີດ ໄອສະຕາຍ. Realistic three.js scenes (statue/einstein.html) + Bounthanh VO. No faces, no logos."""
import os
import eng3d as E
from eng3d import W
import v60 as V
import real3d as R
import icons11  # noqa: compass/atom/medal/doc/eclipse/plane icons

E.setup(11, "ຟີຊິກ")
YEL, CY, RED, GRN = (255, 214, 90), (140, 210, 255), (255, 110, 95), (110, 255, 150)


def hook(l1, l2):
    def f(base, info, T, w0, w1):
        E.headline(base, T, -1.0, w1 - 0.1, l1, l2, y=420, s1=80, s2=60)
    return f


def span(key, text, a, b, col=YEL, dy=-60, size=48):
    def f(base, info, T, w0, w1):
        if key not in info:
            return
        x, y = float(info[key][0]), float(info[key][1])
        x = min(max(x, 230), W - 230)
        E.tag(base, x, min(max(y + dy, 300), 1200), text, T, w0 + a * (w1 - w0), w0 + b * (w1 - w0), size=size, col=col)
    return f


def at(x, y, text, a, b, col=YEL, size=50):
    def f(base, info, T, w0, w1):
        E.tag(base, x, y, text, T, w0 + a * (w1 - w0), w0 + b * (w1 - w0), size=size, col=col)
    return f


def fixed(y, text, a, b, col=YEL, size=58):
    def f(base, info, T, w0, w1):
        E.tag(base, W / 2, y, text, T, w0 + a * (w1 - w0), w0 + b * (w1 - w0), size=size, col=col)
    return f


L = [l.strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "vo_in/EP11.txt")).read().split(" [pause] ")]
BEATS = [
    dict(vo=L[0], pill="ເປີດເລື່ອງ", tags=[hook("ອາຍຸ 26 ປີ ປ່ຽນໂລກໄດ້ແນວໃດ?", "5 ງານວິໄຈ ໃນປີດຽວ")],
         cards=[("ປີ 1905", "ງານວິໄຈ 5 ເລື່ອງ", "doc", 0.35)]),
    dict(vo=L[1], pill="ແມ່ນໃຜ?", cards=[("ອັລເບີດ ໄອສະຕາຍ", "ປີ 1905 ອາຍຸ 26 ປີ", "doc", 0.12)],
         tags=[fixed(560, "ປີມະຫັດສະຈັນ 1905", 0.45, 1.0)]),
    dict(vo=L[2], pill="ໄວເດັກ", cards=[("ເກີດ 14 ມີນາ 1879", "ເມືອງ ອູມ ປະເທດເຢຍລະມັນ", "flag", 0.15)],
         tags=[fixed(560, "ເມືອງ ອູມ · ປີ 1879", 0.3, 1.0, col=CY)]),
    dict(vo=L[3], pill="ໄວເດັກ", cards=[("ອາຍຸ 5 ປີ", "ເຂັມທິດ ຈຸດປະກາຍຄວາມສົງໄສ", "compass", 0.2)],
         tags=[span("north", "ຊີ້ທາງດຽວ ສະເໝີ", 0.45, 1.0, dy=-90)]),
    dict(vo=L[4], pill="ການຮຽນ", cards=[("ປີ 1896 · ເມືອງ ຊູຣິກ", "ຮຽນ ຟີຊິກ ແລະຄະນິດສາດ", "doc", 0.15)],
         tags=[fixed(560, "ປະເທດສະວິດ", 0.35, 1.0, col=CY)]),
    dict(vo=L[5], pill="ວຽກທຳອິດ", cards=[("ປີ 1902 · ເມືອງ ເບີນ", "ພະນັກງານກວດສິດທິບັດ", "doc", 0.15)],
         tags=[fixed(560, "ກວດສິ່ງປະດິດ ທຸກມື້", 0.4, 1.0)]),
    dict(vo=L[6], pill="ປີ 1905", cards=[("ງານທີ 1 · ແສງ", "ກ້ອນພະລັງງານນ້ອຍໆ", "bolt", 0.2)],
         tags=[fixed(560, "ແສງ ມາເປັນກ້ອນ", 0.35, 1.0)]),
    dict(vo=L[7], pill="ປີ 1905", cards=[("ງານທີ 2 ແລະ 3 · ອະຕອມ", "ອະນຸພາກ ເຕັ້ນໄປມາໃນນ້ຳ", "atom", 0.15)],
         tags=[span("grain", "ອະນຸພາກ", 0.3, 1.0, dy=-110, col=YEL)]),
    dict(vo=L[8], pill="ປີ 1905", cards=[("ງານທີ 4 · ສຳພັດທະພາບ", "ເວລາ ບໍ່ເທົ່າກັນ", "clock", 0.12)],
         tags=[at(330, 330, "ຢູ່ກັບທີ່", 0.2, 1.0, col=GRN), at(640, 1190, "ເຄື່ອນທີ່ໄວ ເວລາຊ້າລົງ", 0.35, 1.0, col=CY, size=44)]),
    dict(vo=L[9], pill="ປີ 1905", cards=[("ງານທີ 5", "ມວນ ກາຍເປັນພະລັງງານໄດ້", "bolt", 0.25)],
         tags=[fixed(560, "ສູດທີ່ດັງທີ່ສຸດ", 0.1, 1.0)]),
    dict(vo=L[10], pill="ພິສູດ", cards=[("ປີ 1919 · ສຸລິຍະຄາດ", "ແສງດາວໂຄ້ງ ຕາມທີ່ທຳນາຍ", "eclipse", 0.15)],
         tags=[span("star", "ດາວ", 0.3, 1.0, col=CY, dy=-60), span("ghost", "ຕຳແໜ່ງທີ່ເຫັນ", 0.74, 1.0, col=YEL, dy=90, size=42),
               span("earth", "ໂລກ", 0.3, 1.0, col=GRN, dy=-150)]),
    dict(vo=L[11], pill="ລາງວັນໂນເບວ", cards=[("ໂນເບວ ຟີຊິກ ປີ 1921", "ຍ້ອນເລື່ອງແສງ ບໍ່ແມ່ນສຳພັດທະພາບ", "medal", 0.2)],
         tags=[fixed(560, "ແສງ ເຕະອີເລັກຕຣອນ ອອກຈາກໂລຫະ", 0.4, 1.0, col=CY, size=48)]),
    dict(vo=L[12], pill="ບອກຕໍ່",
         head=("ໄອສະຕາຍ ເກັ່ງຍ້ອນຫຍັງ?", "ຄອມເມັ້ນ ກ ຫຼື ຂ"), hs1=76, hs2=62,
         cards=[("ກ", "ຄວາມສົງໄສ", "compass", 0.1), ("ຂ", "ຄວາມພະຍາຍາມ", "doc", 0.2)],
         note="ຕອນໜ້າ · ເຮືອບິນ ບິນໄດ້ແນວໃດ"),
    dict(vo=L[13], pill="ບອກຕໍ່",
         head=("ຕິດຕາມໄວ້ ຕອນໜ້າ", "ເຮືອບິນ ບິນໄດ້ແນວໃດ"), hs1=74, hs2=60, captions=False, share=True),
]
SCN = ["hook", "y1905", "town", "compass", "study", "office", "photon", "brown", "clocks", "emc", "eclipse", "nobel", "cta", "cta"]
SHOW = R.build(BEATS, SCN, "/home/claude/statue/frames11", os.environ.get("TIMING", "out60/EP11_timing.json"), 60)

if __name__ == "__main__":
    R.run(SHOW, "ຂໍ້ມູນ: NobelPrize.org, ສະຖາບັນສິດທິບັດ ສະວິດ, AMNH, Physics World  |  ພາບປະກອບ 3D ຈຳລອງ", "p11")
