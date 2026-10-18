"""Split a mix into voice + background with UVR-MDX-NET-Voc_FT (ONNX).
usage: python3 separate.py in.wav vocals.wav background.wav   (44.1 kHz stereo in)"""
import sys, numpy as np, subprocess, onnxruntime as ort

N_FFT, HOP, DIM_F, DIM_T, COMP = 6144, 1024, 3072, 256, 1.021
CHUNK = HOP * (DIM_T - 1)
TRIM = N_FFT // 2
GEN = CHUNK - 2 * TRIM
WIN = (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(N_FFT) / N_FFT)).astype(np.float32)  # periodic hann
N_BINS = N_FFT // 2 + 1

def stft(x):  # x: (ch, CHUNK) -> (ch, F, T) complex, torch.stft(center=True, reflect)
    pad = N_FFT // 2
    xp = np.pad(x, ((0, 0), (pad, pad)), mode="reflect")
    T = 1 + (xp.shape[1] - N_FFT) // HOP
    idx = np.arange(N_FFT)[None, :] + HOP * np.arange(T)[:, None]
    frames = xp[:, idx] * WIN  # (ch, T, N_FFT)
    return np.fft.rfft(frames, axis=-1).transpose(0, 2, 1)

def istft(S, length):  # S: (ch, F, T)
    frames = np.fft.irfft(S.transpose(0, 2, 1), n=N_FFT, axis=-1) * WIN
    ch, T, _ = frames.shape
    out = np.zeros((ch, N_FFT + HOP * (T - 1)), np.float32)
    norm = np.zeros(N_FFT + HOP * (T - 1), np.float32)
    for t in range(T):
        out[:, t * HOP:t * HOP + N_FFT] += frames[:, t]
        norm[t * HOP:t * HOP + N_FFT] += WIN ** 2
    pad = N_FFT // 2
    out = out[:, pad:pad + length] / np.maximum(norm[pad:pad + length], 1e-8)
    return out

def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", "44100", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).T.copy()

def save(path, x):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", "2", "-ar", "44100", "-i", "-", path],
                         stdin=subprocess.PIPE)
    p.communicate(np.ascontiguousarray(x.T.astype(np.float32)).tobytes())

mix = load(sys.argv[1])
n = mix.shape[1]
pad = GEN - n % GEN
mixp = np.concatenate([np.zeros((2, TRIM), np.float32), mix, np.zeros((2, pad + TRIM), np.float32)], 1)
sess = ort.InferenceSession("/root/models/voc_ft.onnx", providers=["CPUExecutionProvider"])
outs = []
for i in range(0, n + pad, GEN):
    seg = mixp[:, i:i + CHUNK]
    S = stft(seg)[:, :DIM_F, :]  # (2, F, T)
    inp = np.stack([S[0].real, S[0].imag, S[1].real, S[1].imag])[None].astype(np.float32)
    o = sess.run(None, {"input": inp})[0][0]
    V = np.zeros((2, N_BINS, DIM_T), np.complex64)
    V[0, :DIM_F] = o[0] + 1j * o[1]
    V[1, :DIM_F] = o[2] + 1j * o[3]
    outs.append(istft(V, CHUNK)[:, TRIM:-TRIM])
voc = np.concatenate(outs, 1)[:, :n] * COMP
save(sys.argv[2], voc)
save(sys.argv[3], mix - voc)
print("separated", n / 44100, "s")
