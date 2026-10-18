"""EP.5 — 60 s, realistic three.js scenes (frames rendered by statue/atoms.html), UI composited here."""
import os, json, sys
import numpy as np
from PIL import Image
import lightyear as LY
import eng3d as E
from eng3d import M, C, W, H, prog, ease_io, lerp, clamp
import v60 as V
import ep5_60 as B

E.setup(5, "ຟີຊິກ")
R3D = "/home/claude/statue/frames5"
_need = []
_RU = [None]


def r3d(name):
    def fn(u, T):
        f = int(round(T * 30))
        p = f"{R3D}/{name}_{f:05d}.jpg"
        if _RU[0] is not None:
            p = _RU[0].path(name, float(u), T) or p
        _need.append(dict(out=p, scene=name, t=round(T, 4), u=round(float(u), 4)))
        img = np.asarray(Image.open(p).convert("RGB")).copy() if os.path.exists(p) else np.zeros((H, W, 3), np.uint8)
        return img, {}
    fn.__name__ = "r3d_" + name
    return fn


SCN = ["cube", "atom", "atom", "stadium", "pea", "earth", "weight", "neutron", "neutron", "outro", "outro"]
TAGS = {2: [V.tag_fixed(W / 2, 760, "ນິວເຄລຍ (ນ້ອຍຫຼາຍ!)", 42, M.ORANGE, 0.05), V.tag_fixed(W / 2, 380, "ອີເລັກຕຣອນ ແລ່ນອ້ອມຢູ່ໄກ", 40, (150, 210, 255), 0.4)],
        3: [V.tag_fixed(W / 2, 760, "ເມັດຖົ່ວ = ນິວເຄລຍ", 42, (170, 235, 120), 0.6)],
        4: [V.tag_fixed(W / 2, 700, "ເມັດຖົ່ວ = ນິວເຄລຍ", 46, (170, 235, 120), 0.0)],
        7: [V.tag_fixed(W / 2, 1180, "ດາວນິວຕຣອນ", 52, (150, 210, 255), 0.3)]}
BEATS = []
for i, b in enumerate(B.BEATS):
    nb = dict(b); nb["src"] = ("new", r3d(SCN[i])); nb["tags"] = TAGS.get(i, [])
    BEATS.append(nb)
SHOW = V.Show(BEATS, None, timing_path="out60/EP05_timing.json", min_total=60)
if os.environ.get('REUSE') == '1':
    import reuse3d
    _RU[0] = reuse3d.Reuse(BEATS, '/home/claude/statue/jobs5.json', 60, SHOW)
FOOT = "ຂໍ້ມູນ: Astronomy.com, US DOE  |  ພາບປະກອບ 3D ບໍ່ແມ່ນມາດຕາສ່ວນຈິງ"

if __name__ == "__main__":
    if sys.argv[1] == "--jobs":
        for fi in range(int(round(SHOW.total * 30))):
            T = fi / 30; i = SHOW.idx(T); w0, w1 = SHOW.w0[i], SHOW.w1[i]
            SHOW.beats[i]["src"][1]((T - w0) / max(1e-6, w1 - w0), T)
            if i + 1 < len(SHOW.beats) and T > w1 - V.XF:
                SHOW.beats[i + 1]["src"][1](0.0, T)
        seen, jobs = set(), []
        for j in _need:
            if j["out"] not in seen:
                seen.add(j["out"]); jobs.append(j)
        json.dump(jobs, open(sys.argv[2], "w")); print("jobs", len(jobs), "total", SHOW.total); sys.exit()
    V.main(SHOW, FOOT, "k5")
