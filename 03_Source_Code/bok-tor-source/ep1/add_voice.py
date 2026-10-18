"""Lay a voice-over MP3 onto a ຮູ້ບໍ່? episode, one SRT line per spoken sentence.

usage: python3 add_voice.py video.mp4 voice.mp3 captions.srt out.mp4

The MP3 is split at its pauses into as many pieces as the SRT has lines. Each piece
starts at its SRT start time; if a piece is longer than its slot it is sped up
(max 1.25x) so it never runs into the next line."""
import re, subprocess, sys, json, os, tempfile

video, voice, srt, out = sys.argv[1:5]
tmp = tempfile.mkdtemp()

def sec(ts):
    h, m, s = ts.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)

slots = [(sec(a), sec(b)) for a, b in re.findall(r"(\d\d:\d\d:\d\d,\d+) --> (\d\d:\d\d:\d\d,\d+)", open(srt, encoding="utf-8").read())]
n = len(slots)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", voice],
                           capture_output=True, text=True).stdout)

def silences(noise="-35dB", d=0.25):
    r = subprocess.run(["ffmpeg", "-i", voice, "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r)]
    return list(zip(st, en))

# pick the n-1 longest inner pauses as sentence boundaries
best = None
for d in (0.45, 0.35, 0.25, 0.18, 0.12):
    sil = [(a, b) for a, b in silences(d=d) if a > 0.3 and b < dur - 0.3]
    if len(sil) >= n - 1:
        best = sorted(sorted(sil, key=lambda p: p[1] - p[0], reverse=True)[: n - 1])
        break
if best is None:
    sys.exit(f"Found fewer than {n - 1} pauses in the voice file; add a short pause between sentences and retry.")

cuts = [0.0] + [(a + b) / 2 for a, b in best] + [dur]
filters, labels = [], []
for i, ((s0, s1), (c0, c1)) in enumerate(zip(slots, zip(cuts, cuts[1:]))):
    length = c1 - c0
    room = (slots[i + 1][0] if i + 1 < n else s1 + 1.0) - s0 - 0.05
    tempo = min(1.25, max(1.0, length / room)) if room > 0 else 1.0
    filters.append(f"[1:a]atrim={c0:.3f}:{c1:.3f},asetpts=PTS-STARTPTS,silenceremove=start_periods=1:start_threshold=-40dB,"
                   f"atempo={tempo:.3f},adelay={int(s0 * 1000)}|{int(s0 * 1000)}[v{i}]")
    labels.append(f"[v{i}]")
    print(f"line {i + 1}: {length:.2f}s into slot {room:.2f}s (speed x{tempo:.2f})")
filters.append("".join(labels) + f"amix=inputs={n}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,apad[a]")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", voice, "-filter_complex", ";".join(filters),
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-shortest", "-movflags", "+faststart", out], check=True)
print("done", out)
