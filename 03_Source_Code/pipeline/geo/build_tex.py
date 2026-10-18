"""Orange-navy relief texture for a lon/lat box. usage: python3 build_tex.py out.png lon0 lon1 lat0 lat1 ppd"""
import sys
import numpy as np
from PIL import Image, ImageFilter
Image.MAX_IMAGE_PIXELS = None

out, LON0, LON1, LAT0, LAT1, PPD = sys.argv[1], *map(float, sys.argv[2:7])
box = lambda w, h: (int((LON0 + 180) / 360 * w), int((90 - LAT1) / 180 * h), int((LON1 + 180) / 360 * w), int((90 - LAT0) / 180 * h))
RW, RH = int((LON1 - LON0) * PPD), int((LAT1 - LAT0) * PPD)
sr = Image.open('shadedrelief.jpg')
srr = sr.crop(box(*sr.size)).resize((RW, RH), Image.LANCZOS).convert('L')
et = Image.open('etopo1.jpg'); etr = et.crop(box(*et.size)).resize((RW, RH), Image.BICUBIC)
Mi = Image.fromarray(np.load('landmask.npy'))
Mr = np.asarray(Mi.crop(box(*Mi.size)).resize((RW, RH), Image.BILINEAR), np.float32) / 255
hsv = np.asarray(etr.convert('HSV'), np.float32); H = hsv[..., 0] * 360 / 255; S = hsv[..., 1] / 255
e = np.select([(H > 70) & (H < 170), (H >= 40) & (H <= 70), (H >= 15) & (H < 40)],
              [0.05 + 0.25 * np.clip((170 - H) / 100, 0, 1), 0.30 + 0.25 * ((70 - H) / 30), 0.55 + 0.2 * ((40 - H) / 25)], 0.85)
e = np.where(S < 0.18, 0.9, e)
blur = max(2, PPD / 6)
e = np.asarray(Image.fromarray((np.clip(e, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur)), np.float32) / 255
L = np.asarray(srr, np.float32) / 255
Lb = np.asarray(srr.filter(ImageFilter.GaussianBlur(blur * 1.5)), np.float32) / 255
v = np.clip(0.18 + 0.72 * e + np.clip((L - Lb) * 2.4, -0.5, 0.5), 0, 1)
c = [np.array(x, float) for x in [(34, 20, 10), (110, 62, 28), (176, 110, 52), (222, 170, 104), (244, 222, 182)]]
st = [0, 0.3, 0.55, 0.8, 1.0]
land = np.zeros(v.shape + (3,))
for i in range(4):
    m = (v >= st[i]) & (v <= st[i + 1]); f = ((v - st[i]) / (st[i + 1] - st[i]))[..., None]
    land = np.where(m[..., None], c[i] + (c[i + 1] - c[i]) * f, land)
etn = np.asarray(etr, np.float32) / 255
ocean = np.array([12, 22, 44]) + np.array([16, 28, 46]) * np.clip((etn[..., 1] - 0.55) / 0.35, 0, 1)[..., None]
tex = land * Mr[..., None] + ocean * (1 - Mr[..., None])
Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)).save(out)
print(out, RW, RH)
