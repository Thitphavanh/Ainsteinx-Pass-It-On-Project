"""Re-use already-rendered 3D frames after a timing change: pick the frame of the same scene/beat with the nearest u."""
import json, bisect
import v60 as V

class Reuse:
    def __init__(self, beats, jobs_file, min_total, new_show, old_timing=None, skip=()):
        self.skip = set(skip)
        self.new = new_show
        self.scn = [b["src"][1].__name__.replace("r3d_", "") if b["src"][0] == "new" else None for b in beats]
        old = V.Show(beats, None, timing_path=old_timing, min_total=min_total)
        self.tab = {}
        for j in json.load(open(jobs_file)):
            k = old.idx(j["t"])
            if self.scn[k] != j["scene"]:
                k += 1
            self.tab.setdefault(k, []).append((j["u"], j["out"]))
        for k in self.tab:
            self.tab[k].sort()
        self.old = old

    def path(self, name, u, T):
        if name in self.skip:
            return None
        k = self.new.idx(T)
        if self.scn[k] != name:
            k += 1
        lst = self.tab.get(k)
        if not lst:
            return None
        us = [a for a, _ in lst]
        i = bisect.bisect_left(us, u)
        c = [x for x in (i - 1, i) if 0 <= x < len(lst)]
        best = min(c, key=lambda x: abs(lst[x][0] - u))
        return lst[best][1]
