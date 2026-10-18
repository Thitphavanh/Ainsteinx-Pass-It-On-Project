"""Stylised anatomical heart as SDF -> marching cubes -> heart.bin (pos, normals(unused), colour, faces)."""
import struct, math, numpy as np
from skimage import measure
from sdf_david import sd_round_cone, sd_ellipsoid, sd_sphere, smin, smax, rotx, rotz
def roty(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d)); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
R = rotz(-20) @ roty(25)
def arc(p, c, r, a0, a1, rad, n=8, plane='xz'):
    d = None; pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append(np.array(c) + np.array([r * math.cos(a), 0, r * math.sin(a)]))
    for a, b in zip(pts, pts[1:]):
        v = sd_round_cone(p, a, b, rad, rad); d = v if d is None else np.minimum(d, v)
    return d
def heart(p):
    q = p @ R
    lv = sd_ellipsoid(q, (0.12, 0, -0.25), (0.42, 0.38, 0.62))          # left ventricle (apex down)
    rv = sd_ellipsoid(q, (-0.22, -0.12, -0.12), (0.36, 0.3, 0.5))        # right ventricle
    d = smin(lv, rv, 0.12)
    d = smin(d, sd_ellipsoid(q, (0.2, 0.12, 0.35), (0.3, 0.27, 0.25)), 0.1)    # left atrium
    d = smin(d, sd_ellipsoid(q, (-0.32, 0.05, 0.32), (0.28, 0.25, 0.25)), 0.1) # right atrium
    d = smin(d, sd_round_cone(q, (0.0, 0.0, 0.3), (0.02, -0.02, 0.75), 0.15, 0.14), 0.08)   # ascending aorta
    d = smin(d, arc(q, (0.22, 0.0, 0.75), 0.22, 180, 0, 0.13), 0.05)                         # aortic arch
    d = smin(d, sd_round_cone(q, (0.44, 0.0, 0.75), (0.5, 0.05, 0.25), 0.12, 0.11), 0.05)   # descending
    for x in (0.12, 0.24, 0.36):
        d = smin(d, sd_round_cone(q, (x, 0, 0.92), (x + 0.02, 0, 1.12), 0.045, 0.04), 0.03)  # arch branches
    d = smin(d, sd_round_cone(q, (-0.14, -0.15, 0.25), (-0.05, -0.12, 0.7), 0.13, 0.11), 0.07)  # pulmonary trunk
    d = smin(d, sd_round_cone(q, (-0.4, 0.1, 0.45), (-0.42, 0.12, 1.0), 0.11, 0.1), 0.06)       # superior vena cava
    groove = sd_round_cone(q, (-0.05, -0.42, 0.25), (0.05, -0.28, -0.7), 0.025, 0.025)
    d = smax(d, -groove, 0.04)                                                                  # interventricular groove
    return d
RES = 0.012
lo, hi = np.array([-1.0, -0.9, -1.1]), np.array([1.0, 0.9, 1.4])
n = np.ceil((hi - lo) / RES).astype(int) + 1
xs, ys, zs = [np.linspace(lo[i], lo[i] + RES * (n[i] - 1), n[i]) for i in range(3)]
X, Y, Z = np.meshgrid(xs, ys, zs, indexing='ij')
vol = heart(np.stack([X, Y, Z], -1)).astype(np.float32)
v, f, nrm, _ = measure.marching_cubes(vol, 0.0, spacing=(RES,) * 3); v += lo
q = v @ R
red = np.array([0.62, 0.08, 0.1]); vessel = np.array([0.75, 0.32, 0.3]); vein = np.array([0.3, 0.22, 0.5])
col = np.tile(red, (len(v), 1))
col[q[:, 2] > 0.55] = vessel
col[(q[:, 0] < -0.3) & (q[:, 2] > 0.5)] = vein
col *= (0.9 + 0.1 * np.sin(v[:, 0] * 40) * np.sin(v[:, 2] * 37))[:, None]
with open('heart.bin', 'wb') as fh:
    fh.write(struct.pack('<II', len(v), len(f))); fh.write(v.astype('<f4').tobytes()); fh.write(nrm.astype('<f4').tobytes())
    fh.write(col.astype('<f4').tobytes()); fh.write(f.astype('<u4').tobytes())
print('heart', len(v), len(f))
