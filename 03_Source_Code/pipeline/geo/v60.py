"""Beat-driven 60-second versions. A 'beat' = one voice-over line with its scene, captions, cards and tags.
Timing comes from the real voice-over (timing json) when available, otherwise from a reading-speed estimate."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw
import eng3d as E
from eng3d import M, C, W, H, prog, ease_io, lerp, clamp, draw_line
from common import line_width

XF = 0.35
CHARS_PER_S = 11.5


def est(text):
    t = text.replace("[pause]", "")
    return max(1.8, len(t) / CHARS_PER_S)


class Show:
    def __init__(self, beats, old_world, timing_path=None, lead=0.25, gap=0.32, tail=1.3, min_total=None):
        self.beats, self.old_world = beats, old_world
        spans = None
        if timing_path and os.path.exists(timing_path):
            spans = json.load(open(timing_path))          # [[start, end], ...] in final video time
        if spans and len(spans) == len(beats):
            self.start = [s for s, e in spans]
            self.end = [e for s, e in spans]
        else:
            self.start, self.end = [], []
            t = lead
            for b in beats:
                d = est(b["vo"])
                self.start.append(t); self.end.append(t + d)
                t += d + gap
        self.total = self.end[-1] + tail
        if min_total:
            self.total = max(self.total, min_total)
        # scene windows: from end of previous line to end of this line
        self.w0 = [0.0] + self.end[:-1]
        self.w1 = self.end[:-1] + [self.total]

    def idx(self, T):
        for i in range(len(self.beats)):
            if T < self.w1[i]:
                return i
        return len(self.beats) - 1

    def render_src(self, src, u, T):
        if src[0] == "old":
            t = src[1] + (src[2] - src[1]) * clamp(u)
            out = self.old_world(t)
            return out[0], out[1]
        return src[1](clamp(u), T)

    def contiguous(self, a, b):
        return a[0] == "old" and b[0] == "old" and abs(a[2] - b[1]) < 1e-6

    def world(self, T):
        i = self.idx(T)
        w0, w1 = self.w0[i], self.w1[i]
        u = (T - w0) / max(1e-6, (w1 - w0))
        img, info = self.render_src(self.beats[i]["src"], u, T)
        if i + 1 < len(self.beats) and T > w1 - XF and not self.contiguous(self.beats[i]["src"], self.beats[i + 1]["src"]):
            img2, info2 = self.render_src(self.beats[i + 1]["src"], 0.0, T)
            img = E.blend(img, img2, (T - (w1 - XF)) / XF)
        return img, info, i

    # ---------- UI ----------
    def captions(self, base, T, i):
        b = self.beats[i]
        import re
        text = re.sub(r"\[[^\]]*\]\s*", "", b.get("cap", b["vo"])).strip()
        chunks = b.get("chunks") or chunk(text)
        s, e = self.start[i], self.end[i]
        L = sum(len(c) for c in chunks)
        t = s
        for c in chunks:
            d = (e - s) * len(c) / L
            M.caption(base, c, T, t, t + d + 0.12, col=b.get("capcol", M.CREAMT))
            t += d

    def ui(self, base, T, i, info):
        M.brand(base)
        # pills spanning consecutive beats with the same label
        k = 0
        while k < len(self.beats):
            p = self.beats[k].get("pill")
            j = k
            while j + 1 < len(self.beats) and self.beats[j + 1].get("pill") == p:
                j += 1
            if p:
                M.pill(base, p, T, self.w0[k] + 0.15, self.w1[j] - 0.1 if j + 1 < len(self.beats) else self.total + 1)
            k = j + 1
        b = self.beats[i]
        w0, w1 = self.w0[i], self.w1[i]
        if "head" in b:
            l1, l2 = b["head"]
            a = i
            while a > 0 and self.beats[a - 1].get("head") == b["head"]:
                a -= 1
            z = i
            while z + 1 < len(self.beats) and self.beats[z + 1].get("head") == b["head"]:
                z += 1
            hend = (self.w1[z] - 0.1) if z + 1 < len(self.beats) else self.total + 1
            E.headline(base, T, self.w0[a] + 0.2, hend, l1, l2, y=430, s1=b.get("hs1", 80), s2=b.get("hs2", 60))
        if b.get("captions", True):
            self.captions(base, T, i)
        cards = b.get("cards", [])
        n = len(cards)
        for k, cd in enumerate(cards):
            label, value, icon = cd[:3]
            delay = cd[3] if len(cd) > 3 else 0.1 + 0.35 * k
            if callable(value):
                value = value(info, T)
            t0 = w0 + delay * (w1 - w0)
            if n == 1:
                M.card(base, T, t0, w1 - 0.05, W / 2, 620, label, value, icon)
            else:
                M.card(base, T, t0, w1 - 0.05, 285 if k == 0 else 795, 480, label, value, icon)
        for tg in b.get("tags", []):
            tg(base, info, T, w0, w1)
        if "note" in b:
            d = ImageDraw.Draw(base)
            draw_line(d, W / 2, 1640, b["note"], 32, (170, 178, 200, 255), 400)
        if b.get("share"):
            M.caption(base, C.SHARE_CTA, T, w0 + 0.2, self.total + 1, y=1640, size=50, col=(120, 210, 255))

    def frame(self, T, footer):
        img, info, i = self.world(T)
        base = Image.fromarray(np.ascontiguousarray(img)).convert("RGBA")
        self.ui(base, T, i, info)
        E.footer(base, footer)
        return np.asarray(base.convert("RGB"))

    def dump(self, path):
        json.dump({"total": self.total, "start": self.start, "end": self.end,
                   "lines": [b["vo"] for b in self.beats]}, open(path, "w"), ensure_ascii=False, indent=1)


def chunk(text, size=50, maxw=900):
    words = text.split(" ")
    out, cur = [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if cur and line_width(cand, size) > maxw:
            out.append(cur); cur = w
        else:
            cur = cand
    if cur:
        out.append(cur)
    return [c.rstrip(".") for c in out]


def tag_at(key, text, dy=60, size=44, col=(255, 248, 236), t0f=0.15, idx=None, dx=0):
    def f(base, info, T, w0, w1):
        if key not in info:
            return
        v = info[key]
        x, y = v[0], v[1]
        if idx is not None:
            x, y = x[idx], y[idx]
        x = float(np.atleast_1d(x)[0]); y = float(np.atleast_1d(y)[0])
        E.tag(base, x + dx, y + dy, text, T, w0 + t0f * (w1 - w0), w1 - 0.05, size=size, col=col)
    return f


def tag_fixed(x, y, text, size=40, col=(255, 248, 236), t0f=0.15):
    def f(base, info, T, w0, w1):
        E.tag(base, x, y, text, T, w0 + t0f * (w1 - w0), w1 - 0.05, size=size, col=col)
    return f


def main(show, footer, prefix):
    if sys.argv[1] == "--still":
        for s in sys.argv[2].split(","):
            Image.fromarray(show.frame(float(s), footer)).save(f"{prefix}_{float(s):05.1f}.png"); print("still", s)
        return
    if sys.argv[1] == "--dump":
        show.dump(sys.argv[2]); print("total", show.total); return
    f0, f1 = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (None, None)
    E.render(lambda T: show.frame(T, footer), show.total, sys.argv[1], f0, f1)
