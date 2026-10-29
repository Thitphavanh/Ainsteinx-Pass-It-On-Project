"""EP.10 — AI ແມ່ນຫຍັງ ແລະຮຽນຮູ້ແນວໃດ. Realistic three.js scenes (statue/ai.html) + Bounthanh VO."""
import os
import eng3d as E
from eng3d import W
import v60 as V
import real3d as R
import icons10  # noqa: chip/go/net/card icons

E.setup(10, "ເຕັກໂນໂລຢີ")
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
        E.tag(base, x, y + dy, text, T, w0 + a * (w1 - w0), w0 + b * (w1 - w0), size=size, col=col)
    return f


def fixed(y, text, a, b, col=YEL, size=58):
    def f(base, info, T, w0, w1):
        E.tag(base, W / 2, y, text, T, w0 + a * (w1 - w0), w0 + b * (w1 - w0), size=size, col=col)
    return f


L = [l.strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "vo_in/EP10.txt")).read().split(" [pause] ")]
BEATS = [
    dict(vo=L[0], pill="ເປີດເລື່ອງ", tags=[hook("ຄອມພິວເຕີ ຮຽນເອງໄດ້ແທ້ບໍ?", "ປີ 2016 ຊະນະຍອດນັກຫຼິ້ນ 4 ຕໍ່ 1")],
         cards=[("ເກມໝາກດາມ (Go)", "AI ຊະນະ 4 ຕໍ່ 1", "go", 0.3)]),
    dict(vo=L[1], pill="ຫຼາຍກວ່າອະຕອມ", tags=[fixed(560, "ຫຼາຍກວ່າ ອະຕອມໃນຈັກກະວານ", 0.3, 1.0, size=54)],
         cards=[("ຮູບແບບກະດານ ທີ່ເປັນໄປໄດ້", "ປະມານ 10 ຍົກກຳລັງ 170", "go", 0.1)]),
    dict(vo=L[2], pill="ຕ້ອງຮຽນເອງ", tags=[fixed(560, "ສອນທຸກທ່າ ບໍ່ໄດ້", 0.05, 0.5, col=CY), fixed(560, "ມັນຕ້ອງຮຽນເອງ", 0.5, 1.0)],
         cards=[("ນີ້ແຫຼະ ຄື", "AI", "bolt", 0.55)]),
    dict(vo=L[3], pill="AI ແມ່ນຫຍັງ", cards=[("AI ແມ່ນ", "ປັນຍາປະດິດ", "chip", 0.15)],
         tags=[fixed(560, "Artificial Intelligence", 0.3, 1.0, col=CY, size=54)]),
    dict(vo=L[4], pill="ເກີດເມື່ອໃດ", cards=[("ປີ 1956", "ງານປະຊຸມ Dartmouth", "clock", 0.15)],
         tags=[fixed(1150, "AI ກາຍເປັນວິຊາໃໝ່", 0.45, 1.0)]),
    dict(vo=L[5], pill="ຄອມພິວເຕີທຳມະດາ", cards=[("ຄອມພິວເຕີທຳມະດາ", "ເຮັດຕາມຄຳສັ່ງ ເທົ່ານັ້ນ", "chip", 0.15)]),
    dict(vo=L[6], pill="AI ຮຽນແນວໃດ", cards=[("AI", "ຮຽນຈາກຕົວຢ່າງ", "star", 0.15)],
         tags=[fixed(560, "ເຫັນແມວຫຼາຍໂຕ ກໍຈື່ໄດ້", 0.35, 1.0, col=CY, size=54)]),
    dict(vo=L[7], pill="AI ຮຽນແນວໃດ", cards=[("Neural Network", "ຈຳລອງມາຈາກສະໝອງ", "net", 0.2)],
         tags=[fixed(560, "ເຄືອຂ່າຍປະສາດທຽມ", 0.1, 1.0)]),
    dict(vo=L[8], pill="AI ຮຽນແນວໃດ", cards=[("ທາຍຜິດ", "ປັບຕົວເອງ ເທື່ອລະໜ້ອຍ", "net", 0.3)],
         tags=[span("o0", "ທາຍຜິດ", 0.02, 0.55, col=RED, dy=-70), span("o1", "ທາຍຖືກ", 0.6, 1.0, col=GRN, dy=70)]),
    dict(vo=L[9], pill="ປະຫວັດ", cards=[("ປີ 1958 · Perceptron", "ລອງ 50 ເທື່ອ ກໍແຍກໄດ້", "card", 0.15)],
         tags=[fixed(560, "ແຍກບັດ ຊ້າຍ ຫຼື ຂວາ", 0.35, 1.0)]),
    dict(vo=L[10], pill="ປະຫວັດ", cards=[("ປີ 2012 · AlexNet", "ຊິບກຣາຟິກ + ຮູບມະຫາສານ", "chip", 0.15)],
         tags=[fixed(1150, "ຮຽນຈາກຮູບ ຈຳນວນມະຫາສານ", 0.4, 1.0, col=CY, size=52)]),
    dict(vo=L[11], pill="AlphaGo", cards=[("AlphaGo", "ຫຼິ້ນກັບຕົວເອງ ຫຼາຍພັນເກມ", "go", 0.3)],
         tags=[fixed(560, "ຮຽນຈາກເກມຂອງຄົນ", 0.03, 0.45, col=CY), fixed(560, "ແລ້ວຫຼິ້ນກັບຕົວເອງ", 0.45, 1.0)]),
    dict(vo=L[12], pill="ບອກຕໍ່",
         head=("AI ເກັ່ງຍ້ອນຫຍັງ?", "ຄອມເມັ້ນ ກ ຫຼື ຂ"), hs1=78, hs2=62,
         cards=[("ກ", "ຂໍ້ມູນຫຼາຍ", "star", 0.12), ("ຂ", "ຄອມພິວເຕີແຮງ", "chip", 0.22)],
         note="ຕອນໜ້າ · ປະຫວັດ ອັລເບີດ ໄອສະຕາຍ"),
    dict(vo=L[13], pill="ບອກຕໍ່",
         head=("ຕິດຕາມໄວ້ ຕອນໜ້າ", "ປະຫວັດ ອັລເບີດ ໄອສະຕາຍ"), hs1=74, hs2=58, captions=False, share=True),
]
SCN = ["hook", "cosmos", "learn", "brain", "y1956", "rules", "cats", "net", "fix", "perc", "gpu", "self", "cta", "cta"]
SHOW = R.build(BEATS, SCN, "/home/claude/statue/frames10", os.environ.get("TIMING", "out60/EP10_timing.json"), 60)

if __name__ == "__main__":
    R.run(SHOW, "ຂໍ້ມູນ: Google DeepMind, CHM, Britannica, IEEE Spectrum, Cornell  |  ພາບປະກອບ 3D ຈຳລອງ", "p10")
