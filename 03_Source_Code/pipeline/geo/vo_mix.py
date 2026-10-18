"""Place each VO line at its beat start and mux onto the silent video.
usage: python3 vo_mix.py video.mp4 voice.mp3 timing.json out.mp4 [bed]   (bed = add soft original music bed)"""
import json, re, subprocess, sys, os
import numpy as np
SR = 48000
vid, vo, tim, out = sys.argv[1:5]
BED = len(sys.argv) > 5 and sys.argv[5] == "bed"
src = json.load(open(tim.replace(".json", "_src.json"))); timing = json.load(open(tim))
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", vid], capture_output=True, text=True).stdout)
x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", vo, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32)
n = int(dur * SR); v = np.zeros(n, np.float32)
def fade(s, a, b):
    a, b = int(a * SR), int(b * SR)
    s[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2; s[-b:] *= np.cos(np.linspace(0, np.pi / 2, b)) ** 2
    return s
rms = 10 ** (-19 / 20)
if os.environ.get('CONT') == '1':
    lead = timing[0][0] - src[0][0]; s0 = int(lead * SR); seg = x.copy() * (rms / (np.sqrt(np.mean(x[np.abs(x) > 0.01] ** 2)) + 1e-9)); m = min(len(seg), n - s0); v[s0:s0 + m] += seg[:m]; src = []
for (a, b), (t0, t1) in zip(src, timing):
    seg = x[max(0, int((a - 0.04) * SR)):int((b + 0.15) * SR)].copy()
    core = x[int(a * SR):int(b * SR)]
    seg *= rms / (np.sqrt(np.mean(core ** 2)) + 1e-9)
    seg = fade(seg, 0.02, 0.1)
    s = int((t0 - 0.04) * SR); m = min(len(seg), n - s)
    v[s:s + m] += seg[:m]
def wav(p, arr):
    q = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", p], stdin=subprocess.PIPE)
    q.communicate(arr.astype(np.float32).tobytes())
wav("/tmp/_v.wav", v)
VCH = ("highpass=f=75,equalizer=f=250:t=q:w=1.2:g=-1.5,equalizer=f=3000:t=q:w=1.2:g=2,"
       "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=150:makeup=2dB")
if BED:
    subprocess.run(["python3", "music_gen.py", f"{dur:.2f}", ",".join(f"{t0:.2f}" for t0, _ in timing[1:]), "/tmp/_b.wav"], check=True, capture_output=True)
    fc = (f"[0:a]{VCH},asplit=2[v][sc];[1:a]aformat=channel_layouts=mono,lowpass=f=5000,volume=-24dB[b];"
          "[b][sc]sidechaincompress=threshold=0.02:ratio=5:attack=60:release=700[bd];[v][bd]amix=inputs=2:normalize=0,aformat=channel_layouts=stereo[a]")
    ins = ["-i", "/tmp/_v.wav", "-i", "/tmp/_b.wav"]
else:
    fc = f"[0:a]{VCH},aformat=channel_layouts=stereo[a]"; ins = ["-i", "/tmp/_v.wav"]
subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "[a]", "-ar", "48000", "/tmp/_m.wav"], check=True)
I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", subprocess.run(["ffmpeg", "-i", "/tmp/_m.wav", "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr)[-1])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", "/tmp/_m.wav", "-filter_complex",
                f"[1:a]volume={-14 - I:.2f}dB,alimiter=limit=0.8:level=false[a]", "-map", "0:v", "-map", "[a]",
                "-c:v", "libx264", "-b:v", "2700k", "-maxrate", "3500k", "-bufsize", "6000k", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
print("ok", out, round(dur, 2))
