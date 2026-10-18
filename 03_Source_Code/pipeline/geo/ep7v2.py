"""EP.7 v2 — Leonardo da Vinci, denser 75–80 s script read as ONE continuous take (smooth), visuals timed to the real speech."""
import os, json
import ep7_leo as L
import v60 as V

L.R3D = "/home/claude/statue/frames7b"
_orig_r3d = L.r3d
def _r3d15(name, post=None):
    fn0 = _orig_r3d(name, post)
    def fn(u, T):
        return fn0(u, round(T * 15) / 15)
    fn.__name__ = fn0.__name__
    return fn
L.r3d = _r3d15
r3d, pins, mirror_panel = L.r3d, L.pins_tag, L.mirror_panel

LINES = [
    ("[excited] ຈິດຕະກອນ ວິສະວະກອນ ແລະນັກວິທະຍາສາດ ໃນຄົນດຽວ ລາວຄື ເລໂອນາໂດ ດາວິນຊີ!",
     dict(src=("new", r3d("hero")), pill="ເປີດເລື່ອງ", head=("ເລໂອນາໂດ ດາວິນຊີ", "ອັດສະລິຍະ ທີ່ເກັ່ງທຸກດ້ານ!"), hs1=80, hs2=60, captions=False)),
    ("ລາວເກີດປີ 1452 ໃກ້ເມືອງວິນຊີ ປະເທດອີຕາລີ.",
     dict(src=("new", L.s_birth), pill="ຊີວິດ", tags=[pins], cards=[("ເກີດ", "15 ເມສາ 1452", "star", 0.15), ("ບ້ານເກີດ", "ໃກ້ເມືອງ ວິນຊີ", "flag", 0.45)])),
    ("ອາຍຸປະມານ 15 ປີ ລາວໄປຝຶກງານ ກັບຈິດຕະກອນເວໂຣກກີໂອ ທີ່ຟລໍເຣນ.",
     dict(src=("new", L.s_birth), pill="ຊີວິດ", tags=[pins], cards=[("ອາຍຸ ~15 ປີ", "ຝຶກງານທີ່ ຟລໍເຣນ", "people", 0.1), ("ຄູ", "Verrocchio", "star", 0.5)])),
    ("ລາວແຕ້ມ ອາຫານຄ່ຳມື້ສຸດທ້າຍ ແລະໂມນາລີຊາ ທີ່ທຸກວັນນີ້ ຢູ່ພິພິທະພັນລູບ.",
     dict(src=("new", L.s_works), pill="ຜົນງານ", tags=[pins], cards=[("ອາຫານຄ່ຳມື້ສຸດທ້າຍ", "1495–1498", "flag", 0.15), ("ໂມນາລີຊາ", "ລູບ, ປາຣີ", "star", 0.55)])),
    ("ຮູບຊາຍວິທຣູວຽນ ຂອງລາວ ສຶກສາສັດສ່ວນຂອງຮ່າງກາຍມະນຸດ.",
     dict(src=("new", r3d("notebook")), pill="ສິລະປະ + ວິທະຍາສາດ", cards=[("ຊາຍວິທຣູວຽນ", "ປະມານ 1490", "star", 0.15), ("ສຶກສາ", "ສັດສ່ວນຮ່າງກາຍ", "ruler", 0.5)])),
    ("ບັນທຶກ ແລະແບບແຕ້ມທີ່ລາວປະໄວ້ ມີຫຼາຍກວ່າ 10,000 ໜ້າ.",
     dict(src=("new", r3d("notebook", L._note_post)), pill="ບັນທຶກ", cards=[("ບັນທຶກ ແລະ ແບບແຕ້ມ", lambda i, T: f"{i.get('pages', 10000):,} ໜ້າ", "clock", 0.05)])),
    ("ລາວຂຽນດ້ວຍມືຊ້າຍ ແບບປີ້ນກັບ ຕ້ອງສ່ອງແວ່ນຈຶ່ງອ່ານໄດ້!",
     dict(src=("new", r3d("mirror", L._mirror_post)), pill="ບັນທຶກ", tags=[mirror_panel], cards=[("ຖະນັດ", "ມືຊ້າຍ", "people", 0.1), ("ຂຽນແບບ", "ສ່ອງແວ່ນ", "star", 0.5)])),
    ("ລາວຜ່າສົບສຶກສາ ປະມານ 30 ສົບ ແລະແຕ້ມຫົວໃຈ ກ້າມເນື້ອ ກະດູກ ຢ່າງລະອຽດ.",
     dict(src=("new", r3d("heart")), pill="ກາຍວິພາກ", cards=[("ຜ່າສົບສຶກສາ", "ປະມານ 30 ສົບ", "people", 0.15), ("ແຕ້ມ", "ຫົວໃຈ · ກ້າມເນື້ອ · ກະດູກ", "bolt", 0.55)])),
    ("ເລື່ອງການບິນ ລາວຂຽນກວ່າ 35,000 ຄຳ ແລະແຕ້ມປະມານ 500 ຮູບ ກ່ອນມີເຮືອບິນເກືອບ 400 ປີ.",
     dict(src=("new", r3d("flight")), pill="ການບິນ", cards=[("ເລື່ອງການບິນ", "35,000+ ຄຳ", "ruler", 0.15), ("ຮູບແຕ້ມ", "~500 ຮູບ", "star", 0.5)])),
    ("ແບບຮົ່ມຊູຊີບຂອງລາວ ປີ 2000 ມີຄົນສ້າງຕາມ ແລ້ວໂດດລົງມາໄດ້ແທ້!",
     dict(src=("new", r3d("parachute")), pill="ຮົ່ມຊູຊີບ", cards=[("ອອກແບບ", "ຮົ່ມຊູຊີບ ຊົງປີຣາມິດ", "flag", 0.1), ("ປີ 2000 ລອງໂດດ", "ລອຍລົງໄດ້ແທ້!", "rank", 0.55)])),
    ("ປີ 1516 ກະສັດຝຣັ່ງເຊີນລາວໄປຢູ່ຝຣັ່ງ ແລະລາວເສຍຊີວິດທີ່ນັ້ນ ປີ 1519.",
     dict(src=("new", L.s_france), pill="ບັ້ນປາຍຊີວິດ", tags=[pins], cards=[("ປີ 1516", "ໄປຢູ່ຝຣັ່ງ", "flag", 0.15), ("ເສຍຊີວິດ", "2 ພຶດສະພາ 1519", "clock", 0.55)])),
    ("500 ກວ່າປີຜ່ານມາ ຄວາມຄິດຂອງລາວ ຍັງສ້າງແຮງບັນດານໃຈໃຫ້ໂລກ.",
     dict(src=("new", r3d("hero")), pill="ມໍລະດົກ", cards=[("ຜ່ານມາແລ້ວ", "500+ ປີ", "clock", 0.2)])),
    ("[curious] ເຈົ້າວ່າ ດາວິນຊີ ເກັ່ງດ້ານໃດທີ່ສຸດ? ຄອມເມັ້ນບອກແດ່!",
     dict(src=("new", r3d("hero")), pill="ບອກຕໍ່", head=("ດາວິນຊີ ເກັ່ງດ້ານໃດທີ່ສຸດ?", "ຄອມເມັ້ນບອກແດ່!"), hs1=70, hs2=62)),
    ("[happy] ຖ້າຮູ້ແລ້ວ ຢ່າລືມບອກຕໍ່ ໃຫ້ໝູ່ເດີ້!",
     dict(src=("new", r3d("hero")), pill="ບອກຕໍ່", head=("ດາວິນຊີ ເກັ່ງດ້ານໃດທີ່ສຸດ?", "ຄອມເມັ້ນບອກແດ່!"), hs1=70, hs2=62, captions=False, share=True)),
]
BEATS = []
for vo, d in LINES:
    d = dict(d); d["vo"] = vo; BEATS.append(d)

TIMING = os.environ.get("TIMING", "out60/EP07v2_timing.json")
SHOW = V.Show(BEATS, None, timing_path=TIMING, lead=0.25, gap=0.22, tail=1.4)
if os.environ.get("REUSE") == "1":
    import reuse3d
    L._RU[0] = reuse3d.Reuse(BEATS, "/home/claude/statue/jobs7b_old.json", None, SHOW, "out60/EP07v2_timing_old.json")
FOOT = "ຂໍ້ມູນ: Britannica, Smithsonian NASM, Louvre  |  ພາບປະກອບ 3D"

if __name__ == "__main__":
    import sys
    if sys.argv[1] == "--jobs":
        for fi in range(int(round(SHOW.total * 30))):
            T = fi / 30; i = SHOW.idx(T); w0, w1 = SHOW.w0[i], SHOW.w1[i]
            SHOW.beats[i]["src"][1]((T - w0) / max(1e-6, w1 - w0), T)
            if i + 1 < len(SHOW.beats) and T > w1 - V.XF:
                SHOW.beats[i + 1]["src"][1](0.0, T)
        seen, jobs = set(), []
        for j in L._need:
            if j["out"] not in seen:
                seen.add(j["out"]); jobs.append(j)
        json.dump(jobs, open(sys.argv[2], "w")); print("jobs", len(jobs), "total", SHOW.total); sys.exit()
    V.main(SHOW, FOOT, "d7")
