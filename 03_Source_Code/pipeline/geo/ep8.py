"""EP.8 — Python: origin, popularity, uses, why AI. Realistic three.js scenes (statue/python.html) + Bounthanh VO."""
import os
import eng3d as E
from eng3d import M, W
import v60 as V
import real3d as R

E.setup(8, "ເຕັກໂນໂລຢີ")
BLUE, YEL = (130, 185, 255), (255, 214, 90)


def seg_tag(labels):
    def f(base, info, T, w0, w1):
        n = len(labels); u = (T - w0) / max(1e-6, w1 - w0); i = min(n - 1, int(u * n))
        a, b = w0 + i * (w1 - w0) / n, w0 + (i + 1) * (w1 - w0) / n
        E.tag(base, W / 2, 470, labels[i], T, a + 0.05, b - 0.05, size=56, col=YEL)
    return f

BEATS = [
    dict(vo="[excited] ພາສາຫຼັກຂອງ AI ທຸກມື້ນີ້ ເລີ່ມຕົ້ນຈາກວຽກອະດິເລກ ໃນຊ່ວງວັນຄຣິສມາສ!", pill="ເປີດເລື່ອງ",
         head=("Python", "ຈາກວຽກອະດິເລກ ສູ່ພາສາຂອງ AI"), hs1=110, hs2=62, captions=False),
    dict(vo="ເດືອນທັນວາ ປີ 1989 ກີໂດ ແວນ ຣອສຊຳ ນັກຂຽນໂປຣແກຣມຊາວເນເທີແລນ ເລີ່ມຂຽນພາສາໃໝ່ ໃນຊ່ວງວັນພັກ.", pill="ຕົ້ນກຳເນີດ",
         cards=[("ຜູ້ສ້າງ", "Guido van Rossum", "people", 0.12), ("ປະເທດ", "ເນເທີແລນ", "flag", 0.3)],
         tags=[V.tag_at("cal", "ທັນວາ 1989", dy=-170, size=46, col=YEL, t0f=0.05)]),
    dict(vo="ຊື່ Python ບໍ່ໄດ້ມາຈາກງູ ແຕ່ມາຈາກລາຍການຕະຫຼົກອັງກິດ ທີ່ລາວມັກເບິ່ງ!", pill="ທີ່ມາຂອງຊື່",
         tags=[V.tag_at("tv", "ລາຍການຕະຫຼົກ BBC", dy=-40, size=44, col=YEL, t0f=0.35)]),
    dict(vo="ປີ 1991 Python ເປີດໃຫ້ໂລກໃຊ້ ຕໍ່ມາມີ Python 2 ປີ 2000 ແລະ Python 3 ປີ 2008.", pill="ປະຫວັດ",
         cards=[("ເປີດໃຫ້ໃຊ້ຄັ້ງທຳອິດ", "ກຸມພາ 1991", "flag", 0.1)],
         tags=[V.tag_at("floppy", "1991 · Python 0.9", dy=-120, size=46, col=YEL, t0f=0.0), V.tag_at("cd", "2000 · Python 2", dy=-150, size=46, col=YEL, t0f=0.35),
               V.tag_at("usb", "2008 · Python 3", dy=-110, size=46, col=YEL, t0f=0.65)]),
    dict(vo="ຈຸດເດັ່ນຄື ອ່ານງ່າຍ ຂຽນແຖວດຽວກໍແລ່ນໄດ້ ເໝາະກັບຄົນເລີ່ມຮຽນ.", pill="ອ່ານງ່າຍ",
         cards=[("ໂປຣແກຣມທຳອິດ", "ແຄ່ 1 ແຖວ", "bolt", 0.5)]),
    dict(vo="ປີ 2025 IEEE Spectrum ຈັດໃຫ້ Python ເປັນອັນດັບ 1 ແລະເທິງ GitHub ປີ 2024 ມັນກໍນິຍົມທີ່ສຸດ.", pill="ຄວາມນິຍົມ",
         tags=[V.tag_at("top", "ອັນດັບ 1", dy=-20, size=50, col=YEL, t0f=0.45)],
         cards=[("IEEE Spectrum 2025", "ອັນດັບ 1", "rank", 0.2), ("GitHub 2024", "ນິຍົມທີ່ສຸດ", "star", 0.55)]),
    dict(vo="Python ເຮັດໄດ້ຫຼາຍຢ່າງ: ສ້າງເວັບໄຊ ວິເຄາະຂໍ້ມູນ ເຮັດວຽກອັດຕະໂນມັດ ແລະວຽກວິທະຍາສາດ.", pill="ເຮັດຫຍັງໄດ້",
         tags=[seg_tag(["1 · ສ້າງເວັບໄຊ", "2 · ວິເຄາະຂໍ້ມູນ", "3 · ວຽກອັດຕະໂນມັດ", "4 · ວຽກວິທະຍາສາດ"])]),
    dict(vo="Google, Microsoft, IBM ແລະ NASA ກໍໃຊ້ Python.", pill="ໃຜໃຊ້ແດ່",
         cards=[("ຜູ້ໃຊ້", "Google · Microsoft · IBM · NASA", "globe", 0.2)]),
    dict(vo="[curious] ແລ້ວເປັນຫຍັງ AI ຈຶ່ງໃຊ້ Python? ເພາະມີເຄື່ອງມືພ້ອມໃຊ້ ເຊັ່ນ NumPy, pandas ແລະ PyTorch.", pill="ເປັນຫຍັງ AI",
         cards=[("ເຄື່ອງມື AI", "ພ້ອມໃຊ້ ບໍ່ຕ້ອງສ້າງໃໝ່", "bolt", 0.55)]),
    dict(vo="ນັກພັດທະນາ AI ຫຼາຍຄົນ ຮຽນ Python ມາກ່ອນແລ້ວ ແລະຊຸມຊົນທົ່ວໂລກ ກໍສ້າງເຄື່ອງມືໃໝ່ເພີ່ມທຸກມື້.", pill="ເປັນຫຍັງ AI",
         cards=[("ຊຸມຊົນ", "ແບ່ງປັນທົ່ວໂລກ", "people", 0.4)]),
    dict(vo="ຂຽນງ່າຍ ແຕ່ເຮັດວຽກໃຫຍ່ໄດ້: ຈາກວຽກອະດິເລກ ກາຍເປັນພາສາຂອງ AI!", pill="ສະຫຼຸບ",
         head=("ຂຽນງ່າຍ ເຮັດວຽກໃຫຍ່ໄດ້", "ຈາກວຽກອະດິເລກ ສູ່ພາສາຂອງ AI"), hs1=66, hs2=54, captions=False),
    dict(vo="[curious] ຢາກຮຽນ Python ກັບ ບອກຕໍ່ຄວາມຮູ້ ບໍ? ຄອມເມັ້ນບອກແດ່!", pill="ບອກຕໍ່",
         head=("ຢາກຮຽນ Python ບໍ?", "ຄອມເມັ້ນບອກແດ່!"), hs1=72, hs2=58),
    dict(vo="[happy] ຖ້າຮູ້ແລ້ວ ຢ່າລືມ ບອກຕໍ່ ໃຫ້ໝູ່ເດີ້!", pill="ບອກຕໍ່",
         head=("ຢາກຮຽນ Python ບໍ?", "ຄອມເມັ້ນບອກແດ່!"), hs1=72, hs2=58, captions=False, share=True),
]
for b in BEATS:
    b.setdefault("src", ("old", 0, 0))
SCN = ["hero", "xmas", "tv", "timeline", "hello", "rank", "uses", "globe", "ai", "comm", "hero", "outro", "outro"]
SHOW = R.build(BEATS, SCN, "/home/claude/statue/frames8", os.environ.get("TIMING", "out60/EP08_timing.json"), 66)
import os
if os.environ.get("REUSE") == "1":
    R.reuse(SHOW, "/home/claude/statue/jobs8_old.json", 66, "out60/EP08_timing_old.json", ("timeline", "uses"))

if __name__ == "__main__":
    R.run(SHOW, "ຂໍ້ມູນ: python.org, CHM, IEEE Spectrum, GitHub  |  ພາບປະກອບ 3D", "p8")
