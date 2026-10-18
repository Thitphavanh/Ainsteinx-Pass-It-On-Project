"""EP.6 — 60 s, realistic three.js space scenes (statue/space.html) + Bounthanh VO timing."""
import ep6_60 as B
import real3d as R
SCN = ["intro", "speed", "laps", "moon", "sun", "voyager", "lyear", "ring", "ring", "prox", "andromeda", "outro", "outro"]
SHOW = R.build(B.BEATS, SCN, "/home/claude/statue/frames6", "out60/EP06_timing.json", 60)
if __name__ == "__main__":
    R.run(SHOW, "ຂໍ້ມູນ: IAU, NASA/JPL, NASA/STScI  |  ພາບປະກອບ ບໍ່ຕາມສັດສ່ວນຈິງ", "r6")
