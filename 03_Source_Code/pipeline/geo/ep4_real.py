"""EP.4 — 60 s, realistic three.js Eiffel scenes (statue/eiffel.html) + Bounthanh VO timing."""
import ep4_60 as B
import real3d as R
SCN = ["intro", "build", "steel", "hot", "cold", "lean", "trace", "gap", "buckle", "gap", "outro"]
SHOW = R.build(B.BEATS, SCN, "/home/claude/statue/frames4", "out60/EP04_timing.json", 60)
if __name__ == "__main__":
    R.run(SHOW, "ຂໍ້ມູນ: La Tour Eiffel (ທາງການ)  |  ພາບປະກອບ 3D (ຂະຫຍາຍເກີນຈິງ)", "r4")
