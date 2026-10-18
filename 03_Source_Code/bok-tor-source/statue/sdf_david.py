"""Sculpt a stylised marble 'David' (public-domain subject) as a signed-distance field, mesh it with marching cubes,
and export positions/normals/colours for three.js.  Units: metres, z up, figure faces -y."""
import json, math, struct, sys
import numpy as np
from skimage import measure

RES = float(sys.argv[1]) if len(sys.argv) > 1 else 0.016


def length(v):
    return np.sqrt(np.sum(v * v, axis=-1))


def sd_round_cone(p, a, b, r1, r2):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ba = b - a
    l2 = ba @ ba
    rr = r1 - r2
    a2 = l2 - rr * rr
    il2 = 1.0 / l2
    pa = p - a
    y = pa @ ba
    z = y - l2
    xv = pa * l2 - y[..., None] * ba
    x2 = np.sum(xv * xv, axis=-1)
    y2 = y * y * l2
    z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    out = np.where(np.sign(z) * a2 * z2 > k, np.sqrt(x2 + z2) * il2 - r2,
                   np.where(np.sign(y) * a2 * y2 < k, np.sqrt(x2 + y2) * il2 - r1,
                            (np.sqrt(x2 * a2 * il2) + y * rr) * il2 - r1))
    return out


def sd_ellipsoid(p, c, r, rot=None):
    q = p - np.asarray(c, float)
    if rot is not None:
        q = q @ rot
    r = np.asarray(r, float)
    k0 = length(q / r)
    k1 = length(q / (r * r))
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def sd_sphere(p, c, r):
    return length(p - np.asarray(c, float)) - r


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def rotz(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def rotx(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


J = dict(rhip=(-0.24, 0.0, 2.66), rknee=(-0.22, -0.02, 1.47), rank=(-0.22, 0.02, 0.24),
         lhip=(0.25, 0.0, 2.56), lknee=(0.40, -0.17, 1.44), lank=(0.50, 0.04, 0.24),
         rsho=(-0.64, 0.03, 4.08), relb=(-0.70, 0.06, 3.36), rwri=(-0.70, 0.02, 2.66),
         lsho=(0.64, 0.03, 4.2), lelb=(0.80, -0.22, 3.64), lwri=(0.50, -0.30, 4.12))


def figure(p):
    k = 0.07
    d = sd_ellipsoid(p, (0, 0.03, 2.78), (0.43, 0.29, 0.36))                       # pelvis
    d = smin(d, sd_ellipsoid(p, (0, 0.01, 3.18), (0.43, 0.28, 0.45)), 0.14)         # abdomen
    d = smin(d, sd_ellipsoid(p, (0, 0.06, 3.72), (0.53, 0.32, 0.56)), 0.14)        # rib cage
    for s in (-1, 1):
        d = smin(d, sd_ellipsoid(p, (s * 0.2, -0.2, 3.96), (0.27, 0.075, 0.13)), 0.13)   # pectorals (broad, flat)
        d = smin(d, sd_ellipsoid(p, (s * 0.16, -0.21, 3.33), (0.13, 0.07, 0.3)), 0.06)   # abdominals
    d = smin(d, sd_ellipsoid(p, (0, 0.24, 3.75), (0.42, 0.13, 0.42)), 0.12)        # back / lats
    d = smin(d, sd_ellipsoid(p, (0, 0.25, 2.62), (0.36, 0.2, 0.25)), 0.1)          # glutes
    # legs
    d = smin(d, sd_round_cone(p, J["rhip"], J["rknee"], 0.31, 0.19), k)
    d = smin(d, sd_round_cone(p, J["lhip"], J["lknee"], 0.3, 0.19), k)
    d = smin(d, sd_ellipsoid(p, (-0.24, -0.06, 2.1), (0.24, 0.23, 0.45)), 0.12)        # quads
    d = smin(d, sd_ellipsoid(p, (0.32, -0.12, 2.0), (0.23, 0.22, 0.43), rotx(-8)), 0.12)
    d = smin(d, sd_round_cone(p, J["rknee"], J["rank"], 0.18, 0.095), 0.06)
    d = smin(d, sd_round_cone(p, J["lknee"], J["lank"], 0.175, 0.095), 0.06)
    d = smin(d, sd_ellipsoid(p, (-0.22, 0.09, 1.05), (0.16, 0.16, 0.33)), 0.07)     # calves
    d = smin(d, sd_ellipsoid(p, (0.45, -0.01, 1.0), (0.15, 0.15, 0.33), rotx(-10)), 0.07)
    d = smin(d, sd_ellipsoid(p, (-0.22, -0.13, 1.47), (0.1, 0.06, 0.1)), 0.04)     # knee caps
    d = smin(d, sd_ellipsoid(p, (0.40, -0.29, 1.44), (0.1, 0.06, 0.1)), 0.04)
    for ax, az in ((-0.22, 0.0), (0.5, 0.06)):                                      # feet
        d = smin(d, sd_ellipsoid(p, (ax, -0.17 + az, 0.1), (0.13, 0.33, 0.1)), 0.06)
        for t in range(5):
            d = smin(d, sd_sphere(p, (ax - 0.09 + t * 0.045, -0.47 + az + abs(t - 1.5) * 0.02, 0.05), 0.035), 0.02)
    # neck & head (turned toward his left, i.e. +x)
    d = smin(d, sd_round_cone(p, (0, 0.04, 4.15), (0.03, 0.0, 4.55), 0.22, 0.17), 0.09)
    for s in (-1, 1):
        d = smin(d, sd_ellipsoid(p, (s * 0.38, 0.06, 4.24), (0.26, 0.14, 0.09)), 0.07)   # trapezius
    R = rotz(18)
    hc = np.array([0.06, -0.02, 4.82])
    d = smin(d, sd_ellipsoid(p, hc, (0.27, 0.31, 0.35), R), 0.06)                  # cranium
    q = (p - hc) @ R
    face = lambda c, r: sd_ellipsoid(q, c, r)
    d = smin(d, face((0, -0.24, -0.17), (0.13, 0.11, 0.11)), 0.06)                   # jaw / chin
    d = smin(d, face((0, -0.29, 0.06), (0.19, 0.06, 0.05)), 0.04)                  # brow ridge
    d = smin(d, sd_round_cone(q, (0, -0.29, 0.04), (0, -0.36, -0.08), 0.03, 0.042), 0.025)   # nose
    for s in (-1, 1):
        d = smax(d, -face((s * 0.095, -0.315, 0.0), (0.05, 0.03, 0.028)), 0.025)   # eye sockets (shallow)
        d = smin(d, face((s * 0.095, -0.285, 0.0), (0.04, 0.03, 0.026)), 0.015)   # eyeballs
        d = smin(d, face((s * 0.2, -0.05, -0.02), (0.035, 0.06, 0.07)), 0.02)      # ears
    d = smax(d, -face((0, -0.345, -0.14), (0.06, 0.02, 0.01)), 0.01)                # mouth line
    rng = np.random.default_rng(3)
    for i in range(46):                                                             # curls
        th, ph = rng.uniform(0, 2 * np.pi), rng.uniform(-0.15, 1.35)
        if math.sin(th) < -0.55 and ph < 0.6:
            continue
        c = np.array([0.28 * math.cos(ph) * math.cos(th), 0.32 * math.cos(ph) * math.sin(th) + 0.02, 0.35 * math.sin(ph) + 0.04])
        d = smin(d, face(c, (0.07, 0.07, 0.06)), 0.025)
    # arms
    d = smin(d, sd_ellipsoid(p, J["rsho"], (0.23, 0.22, 0.2)), 0.1)                 # deltoids
    d = smin(d, sd_ellipsoid(p, J["lsho"], (0.23, 0.22, 0.2)), 0.1)
    d = smin(d, sd_round_cone(p, J["rsho"], J["relb"], 0.17, 0.115), 0.06)
    d = smin(d, sd_round_cone(p, J["relb"], J["rwri"], 0.125, 0.075), 0.05)
    d = smin(d, sd_round_cone(p, J["lsho"], J["lelb"], 0.17, 0.115), 0.06)
    d = smin(d, sd_round_cone(p, J["lelb"], J["lwri"], 0.125, 0.075), 0.05)
    d = smin(d, sd_ellipsoid(p, (-0.7, 0.04, 3.72), (0.13, 0.13, 0.26)), 0.06)       # biceps
    d = smin(d, sd_ellipsoid(p, (0.74, -0.1, 3.93), (0.13, 0.13, 0.26), rotx(25)), 0.06)
    # right hand hanging (large, as in the original): palm + fingers + thumb
    d = smin(d, sd_ellipsoid(p, (-0.71, 0.0, 2.5), (0.07, 0.13, 0.16)), 0.04)
    for t in range(4):
        y = -0.08 + t * 0.055
        d = smin(d, sd_round_cone(p, (-0.71, y, 2.38), (-0.69, y - 0.02, 2.18), 0.03, 0.022), 0.015)
    d = smin(d, sd_round_cone(p, (-0.68, -0.11, 2.52), (-0.62, -0.16, 2.38), 0.035, 0.025), 0.02)
    # left hand at the shoulder holding the sling
    d = smin(d, sd_ellipsoid(p, (0.42, -0.3, 4.24), (0.1, 0.07, 0.12)), 0.04)
    for t in range(4):
        d = smin(d, sd_sphere(p, (0.36 + t * 0.02, -0.38, 4.3 - t * 0.05), 0.035), 0.02)
    # sling over the left shoulder, down the back to the right hand
    pts = [(0.4, -0.33, 4.3), (0.42, -0.1, 4.45), (0.35, 0.25, 4.3), (0.0, 0.36, 3.7), (-0.45, 0.3, 3.0), (-0.68, 0.12, 2.55)]
    for a, b in zip(pts, pts[1:]):
        d = smin(d, sd_round_cone(p, a, b, 0.028, 0.028), 0.01)
    # tree-stump support behind the right leg
    d = smin(d, sd_round_cone(p, (-0.46, 0.3, 0.0), (-0.42, 0.26, 1.35), 0.2, 0.14), 0.06)
    # integral plinth (rocky base the figure stands on)
    base = sd_ellipsoid(p, (0.1, 0.0, 0.0), (0.95, 0.75, 0.2))
    d = smin(d, base, 0.06)
    d = np.maximum(d, -p[..., 2] + 0.0)          # flat bottom at z = 0
    return d


def main():
    lo = np.array([-1.0, -0.8, -0.02]); hi = np.array([1.15, 0.8, 5.2])
    n = np.ceil((hi - lo) / RES).astype(int) + 1
    xs, ys, zs = [np.linspace(lo[i], lo[i] + RES * (n[i] - 1), n[i]) for i in range(3)]
    vol = np.empty(n, np.float32)
    for k in range(0, n[2], 32):                       # chunked to keep memory small
        X, Y, Z = np.meshgrid(xs, ys, zs[k:k + 32], indexing="ij")
        P = np.stack([X, Y, Z], -1)
        vol[:, :, k:k + 32] = figure(P)
    verts, faces, normals, _ = measure.marching_cubes(vol, 0.0, spacing=(RES, RES, RES))
    verts += lo
    # marble colour: warm white with faint grey veins
    pnoise = np.sin(verts[:, 0] * 9 + np.sin(verts[:, 2] * 3.1) * 2.5) * np.sin(verts[:, 2] * 4.3 + verts[:, 1] * 7)
    vein = np.clip(1 - np.abs(pnoise) * 9, 0, 1) ** 2
    col = np.stack([0.93 - 0.12 * vein, 0.91 - 0.12 * vein, 0.87 - 0.1 * vein], 1)
    col[verts[:, 2] < 0.22] *= 0.78
    normals = -normals if (normals[:, 2].mean() < -1) else normals
    out = sys.argv[2] if len(sys.argv) > 2 else "david.bin"
    with open(out, "wb") as f:
        f.write(struct.pack("<II", len(verts), len(faces)))
        f.write(verts.astype("<f4").tobytes()); f.write(normals.astype("<f4").tobytes())
        f.write(col.astype("<f4").tobytes()); f.write(faces.astype("<u4").tobytes())
    print("verts", len(verts), "faces", len(faces), "grid", n)


if __name__ == "__main__":
    main()
