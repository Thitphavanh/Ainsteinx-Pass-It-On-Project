"""Re-time an AI voice-over to scene changes and make it play smoothly.

usage: python3 smooth_vo.py in.mp4 out.mp4 "t1,t2,..."   (anchor = when each line should start)

- splits the voice into lines at its pauses (one line per anchor)
- each line keeps 40 ms of lead-in and 180 ms of tail, with soft fades (no clicks / cut-off endings)
- every line is levelled to the same loudness
- each line starts at its anchor; if it would run into the next line it is nudged later / sped up (max 1.12x)
- a soft, original music bed (generated here, copyright-free) fills the gaps and ducks under the voice
- a very quiet airy swell marks each scene change
- final mix: -14 LUFS, true peak -1.5 dB, stereo 48 kHz
"""
import re, subprocess, sys
import numpy as np

SR = 48000
src, out, anchors_s = sys.argv[1], sys.argv[2], sys.argv[3]
anchors = [float(a) for a in anchors_s.split(",")]
scene_changes = [float(a) for a in sys.argv[4].split(",")] if len(sys.argv) > 4 and sys.argv[4] else []
import os
NOBED = os.environ.get("NOBED") == "1"   # voice only: no music bed, no swells


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def speech_segments(x, n):
    """Return n (start, end) speech spans using an energy gate, merging the shortest gaps until n remain."""
    hop = int(SR * 0.01)
    e = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2) + 1e-12) for i in range(0, len(x) - hop, hop)])
    db = 20 * np.log10(e)
    on = db > -40
    spans, i = [], 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and (on[j] or (j + 25 < len(on) and on[j:j + 25].any())):  # bridge gaps < 250 ms
                j += 1
            spans.append([i * 0.01, j * 0.01])
            i = j
        i += 1
    spans = [s for s in spans if s[1] - s[0] > 0.12]
    while len(spans) > n:  # merge the pair with the smallest gap
        gaps = [spans[k + 1][0] - spans[k][1] for k in range(len(spans) - 1)]
        k = int(np.argmin(gaps))
        spans[k][1] = spans[k + 1][1]
        del spans[k + 1]
    if len(spans) != n:
        sys.exit(f"found {len(spans)} spoken lines but {n} anchors")
    return spans


def fade(seg, fin, fout):
    a, b = int(fin * SR), int(fout * SR)
    if a:
        seg[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    if b:
        seg[-b:] *= np.cos(np.linspace(0, np.pi / 2, b)) ** 2
    return seg


def tempo(seg, factor):
    if abs(factor - 1) < 0.005:
        return seg
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-af", f"atempo={factor:.4f}", "-f", "f32le", "-"], input=seg.tobytes(), capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).copy()


x = load(src)
total = len(x) / SR
spans = speech_segments(x, len(anchors))

# ---- place lines ----
voice = np.zeros(len(x) + SR, np.float32)
target_rms = 10 ** (-19.0 / 20)
cursor = 0.0
report = []
for i, ((a, b), t0) in enumerate(zip(spans, anchors)):
    lead, tail = 0.04, 0.18
    seg = x[max(0, int((a - lead) * SR)):min(len(x), int((b + tail) * SR))].copy()
    core = x[int(a * SR):int(b * SR)]
    seg *= target_rms / (np.sqrt(np.mean(core ** 2)) + 1e-9)
    seg = fade(seg, 0.02, 0.12)
    start = max(t0 - lead, cursor + 0.22)                       # keep a breath after the previous line
    limit = (anchors[i + 1] - 0.08) if i + 1 < len(anchors) else total - 0.15
    room = limit - start
    dur = len(seg) / SR
    f = 1.0
    if dur > room > 0:
        f = min(1.12, dur / room)
        seg = tempo(seg, f)
    s = int(start * SR)
    voice[s:s + len(seg)] += seg[:len(voice) - s]
    cursor = start + len(seg) / SR
    report.append(f"line {i + 1:2d}: was {a:6.2f}s → now {start + lead:6.2f}s  (scene {t0:6.2f}s){'  speed x%.2f' % f if f > 1 else ''}")
voice = voice[:len(x)]

# ---- original music bed: soft pads, Am – F – C – G, 4 s per chord ----
t = np.arange(len(x)) / SR
def note(m):
    return 440.0 * 2 ** ((m - 69) / 12)
chords = [[57, 60, 64], [53, 57, 60], [48, 55, 64], [55, 59, 62]]
bed = np.zeros(len(x), np.float32)
L = 4.0
for k in range(int(np.ceil(total / L)) + 1):
    c = chords[k % 4]
    a0, a1 = k * L - 0.6, k * L + L + 0.6
    i0, i1 = max(0, int(a0 * SR)), min(len(x), int(a1 * SR))
    if i0 >= i1:
        continue
    tt = t[i0:i1] - a0
    env = np.clip(tt / 1.2, 0, 1) * np.clip((a1 - a0 - tt) / 1.2, 0, 1)
    env = env ** 1.5
    for m in c + [c[0] - 12]:
        fr = note(m)
        w = np.sin(2 * np.pi * fr * tt) + 0.25 * np.sin(2 * np.pi * fr * 2 * tt + 0.3) + 0.15 * np.sin(2 * np.pi * fr * 1.003 * tt)
        bed[i0:i1] += (w * env * (0.6 if m < c[0] else 1.0)).astype(np.float32)
# gentle pluck on each beat (1 s), notes from the chord
for beat in range(int(total)):
    c = chords[(beat // 4) % 4]
    fr = note(c[[0, 2, 1, 2][beat % 4]] + 12)
    i0 = int(beat * SR)
    n = min(int(0.9 * SR), len(x) - i0)
    if n <= 0:
        break
    tt = np.arange(n) / SR
    bed[i0:i0 + n] += (0.35 * np.sin(2 * np.pi * fr * tt) * np.exp(-tt * 5.0)).astype(np.float32)
bed /= np.max(np.abs(bed)) + 1e-9
bed = fade(bed, 0.4, 0.6)

# ---- scene-change swells (filtered noise, very quiet) ----
fx = np.zeros(len(x), np.float32)
rng = np.random.default_rng(1)
for sc in scene_changes:
    n = int(0.45 * SR)
    i0 = int((sc - 0.3) * SR)
    if i0 < 0 or i0 + n > len(x):
        continue
    noise = rng.standard_normal(n).astype(np.float32)
    k = 40
    noise = np.convolve(noise, np.ones(k) / k, mode="same")         # soften: low-pass
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    fx[i0:i0 + n] += noise * env

def wav(name, arr):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", name], stdin=subprocess.PIPE)
    p.communicate(arr.astype(np.float32).tobytes())

wav("_voice.wav", voice)
wav("_bed.wav", bed * (0 if NOBED else 0.5))
wav("_fx.wav", fx * (0 if NOBED else 1))

VCHAIN = ("highpass=f=75,equalizer=f=250:t=q:w=1.2:g=-1.5,equalizer=f=3000:t=q:w=1.2:g=2,"
          "deesser=i=0.3,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=150:makeup=2dB,"
          "aecho=0.85:0.6:35|60:0.10|0.06")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "_voice.wav", "-i", "_bed.wav", "-i", "_fx.wav",
                "-filter_complex",
                f"[0:a]{VCHAIN},asplit=2[v][sc];"
                "[1:a]lowpass=f=5000,volume=-25dB[b];[b][sc]sidechaincompress=threshold=0.02:ratio=5:attack=60:release=700[bd];"
                "[2:a]highpass=f=500,lowpass=f=7000,volume=-30dB[fx];"
                "[v][bd][fx]amix=inputs=3:normalize=0,aformat=channel_layouts=stereo[a]",
                "-map", "[a]", "-ar", "48000", "_mix.wav"], check=True)
meas = subprocess.run(["ffmpeg", "-i", "_mix.wav", "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", meas)[-1])
gain = -14.0 - I
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-i", "_mix.wav",
                "-filter_complex", f"[1:a]volume={gain:.2f}dB,alimiter=limit=0.78:attack=3:release=60:level=false[a]",
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-shortest", "-movflags", "+faststart", out], check=True)
print("\n".join(report))
print("done", out)
