"""Original copyright-free bed (Am-F-C-G pads + plucks) with soft swells at scene changes."""
import subprocess, re, numpy as np
import sys
SR, total = 48000, float(sys.argv[1])
n = int(SR * total); t = np.arange(n) / SR
note = lambda m: 440.0 * 2 ** ((m - 69) / 12)
chords = [[57, 60, 64], [53, 57, 60], [48, 55, 64], [55, 59, 62]]
bed = np.zeros(n, np.float32); L = 4.0
for k in range(int(np.ceil(total / L)) + 1):
    c = chords[k % 4]; a0, a1 = k * L - 0.6, k * L + L + 0.6
    i0, i1 = max(0, int(a0 * SR)), min(n, int(a1 * SR))
    if i0 >= i1: continue
    tt = t[i0:i1] - a0
    env = (np.clip(tt / 1.2, 0, 1) * np.clip((a1 - a0 - tt) / 1.2, 0, 1)) ** 1.5
    for m in c + [c[0] - 12]:
        fr = note(m)
        w = np.sin(2*np.pi*fr*tt) + .25*np.sin(2*np.pi*fr*2*tt+.3) + .15*np.sin(2*np.pi*fr*1.003*tt)
        bed[i0:i1] += (w * env * (0.6 if m < c[0] else 1.0)).astype(np.float32)
for beat in range(int(total * 2)):          # 8th-note plucks, a little more motion for a map story
    c = chords[(beat // 8) % 4]; fr = note(c[[0, 2, 1, 2, 0, 1, 2, 1][beat % 8]] + 12)
    i0 = int(beat * 0.5 * SR); m_ = min(int(0.6 * SR), n - i0)
    if m_ <= 0: break
    tt = np.arange(m_) / SR
    bed[i0:i0+m_] += (0.28 * np.sin(2*np.pi*fr*tt) * np.exp(-tt * 6)).astype(np.float32)
bed /= np.abs(bed).max()
a, b = int(.5*SR), int(1.5*SR)
bed[:a] *= np.linspace(0, 1, a); bed[-b:] *= np.linspace(1, 0, b)
rng = np.random.default_rng(1)
for sc in [float(v) for v in sys.argv[2].split(",")]:
    m_ = int(0.7 * SR); i0 = int((sc - 0.45) * SR)
    nz = np.convolve(rng.standard_normal(m_), np.ones(30) / 30, 'same') * np.sin(np.linspace(0, np.pi, m_)) ** 2
    bed[i0:i0+m_] += (nz * 0.9).astype(np.float32)
p = subprocess.Popen(["ffmpeg","-v","error","-y","-f","f32le","-ar",str(SR),"-ac","1","-i","-","-af","lowpass=f=6000,aformat=channel_layouts=stereo","_bed.wav"], stdin=subprocess.PIPE)
p.communicate(bed.astype(np.float32).tobytes())
I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", subprocess.run(["ffmpeg","-i","_bed.wav","-af","ebur128","-f","null","-"],capture_output=True,text=True).stderr)[-1])
subprocess.run(["ffmpeg","-v","error","-y","-i","_bed.wav","-af",f"volume={-16-I:.2f}dB,alimiter=limit=0.8:level=false",sys.argv[3]],check=True)
print("bed ok", I)
