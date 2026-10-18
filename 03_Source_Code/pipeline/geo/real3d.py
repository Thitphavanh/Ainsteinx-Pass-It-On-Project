"""Swap a 60 s beat show onto realistic three.js frames (rendered by statue/*.html), keeping all UI."""
import os, json, sys
import numpy as np
from PIL import Image
import eng3d as E
from eng3d import W, H
import v60 as V

_need = []
_RU = [None]


def reuse(show, jobs_file, min_total, old_timing=None, skip=()):
    import reuse3d
    _RU[0] = reuse3d.Reuse(show.beats, jobs_file, min_total, show, old_timing, skip)


def r3d(R3D, name, post=None):
    def fn(u, T):
        f = int(round(T * 15)) * 2
        T = f / 30
        p = f"{R3D}/{name}_{f:05d}.jpg"
        if _RU[0] is not None:
            p = _RU[0].path(name, float(u), T) or p
        _need.append(dict(out=p, scene=name, t=round(T, 4), u=round(float(u), 4)))
        if os.path.exists(p):
            img = np.asarray(Image.open(p).convert("RGB")).copy()
            js = p[:-4] + ".json"
            info = json.load(open(js)) if os.path.exists(js) else {}
        else:
            img, info = np.zeros((H, W, 3), np.uint8), {}
        info = {k: (tuple(v) if isinstance(v, list) and k != "ly_ring" else v) for k, v in info.items()}
        if post:
            info = post(info, u, T)
        return img, info
    fn.__name__ = "r3d_" + name
    return fn


def build(beats, scn, R3D, timing, min_total=None, posts=None):
    posts = posts or {}
    nb = []
    for i, b in enumerate(beats):
        d = dict(b); d["src"] = ("new", r3d(R3D, scn[i], posts.get(i))); nb.append(d)
    return V.Show(nb, None, timing_path=timing, min_total=min_total)


def run(show, footer, prefix):
    if sys.argv[1] == "--jobs":
        for fi in range(int(round(show.total * 30))):
            T = fi / 30; i = show.idx(T); w0, w1 = show.w0[i], show.w1[i]
            show.beats[i]["src"][1]((T - w0) / max(1e-6, w1 - w0), T)
            if i + 1 < len(show.beats) and T > w1 - V.XF:
                show.beats[i + 1]["src"][1](0.0, T)
        seen, jobs = set(), []
        for j in _need:
            if j["out"] not in seen:
                seen.add(j["out"]); jobs.append(j)
        json.dump(jobs, open(sys.argv[2], "w")); print("jobs", len(jobs), "total", show.total); sys.exit()
    V.main(show, footer, prefix)
