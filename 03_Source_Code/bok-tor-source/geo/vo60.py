"""Measure a full-script voice-over and write the beat timing json.
usage: python3 vo60.py voice.mp3 N out_timing.json [target_total]"""
import json, subprocess, sys
import numpy as np

SR = 48000
src, n, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
target = float(sys.argv[4]) if len(sys.argv) > 4 else 60.0
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.float32)
hop = SR // 100
e = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2) + 1e-12) for i in range(0, len(x) - hop, hop)])
on = 20 * np.log10(e) > -40
spans, i = [], 0
while i < len(on):
    if on[i]:
        j = i
        while j < len(on) and (on[j] or (j + 25 < len(on) and on[j:j + 25].any())):
            j += 1
        spans.append([i / 100, j / 100]); i = j
    i += 1
spans = [s for s in spans if s[1] - s[0] > 0.12]
while len(spans) > n:
    gaps = [spans[k + 1][0] - spans[k][1] for k in range(len(spans) - 1)]
    k = int(np.argmin(gaps)); spans[k][1] = spans[k + 1][1]; del spans[k + 1]
if len(spans) != n:
    sys.exit(f"found {len(spans)} lines, expected {n}")
d = [b - a + 0.08 for a, b in spans]
lead, tail, gap = 0.25, 1.3, 0.35
natural = lead + sum(d) + gap * (n - 1) + tail
extra = max(0.0, target - natural)
gap += min(0.9, extra / max(1, n - 1))
t, timing = lead, []
for k in range(n):
    timing.append([round(t, 3), round(t + d[k], 3)])
    t += d[k] + gap
json.dump(timing, open(out, "w"))
print("lines", [round(v, 2) for v in d])
print("total", round(timing[-1][1] + tail, 2), "gap", round(gap, 2))
print("anchors", ",".join(f"{a:.2f}" for a, _ in timing))
