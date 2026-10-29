import math
import mekong as M
_orig_icon = M.icon


def icon(d, kind, cx, cy, s, col):
    c = col + (255,)
    if kind == "bolt":
        d.polygon([(cx + s * 0.2, cy - s), (cx - s * 0.6, cy + s * 0.15), (cx - s * 0.05, cy + s * 0.15), (cx - s * 0.25, cy + s),
                   (cx + s * 0.6, cy - s * 0.2), (cx + s * 0.05, cy - s * 0.2)], fill=c)
    elif kind == "globe":
        d.ellipse((cx - s, cy - s, cx + s, cy + s), outline=c, width=max(3, int(s / 6)))
        d.ellipse((cx - s * 0.45, cy - s, cx + s * 0.45, cy + s), outline=c, width=max(2, int(s / 8)))
        d.line([(cx - s, cy), (cx + s, cy)], fill=c, width=max(2, int(s / 8)))
    elif kind == "moon":
        d.ellipse((cx - s, cy - s, cx + s, cy + s), fill=c)
        d.ellipse((cx - s * 0.45, cy - s * 1.1, cx + s * 1.3, cy + s * 0.7), fill=(12, 18, 34, 255))
    elif kind == "sun":
        d.ellipse((cx - s * 0.5, cy - s * 0.5, cx + s * 0.5, cy + s * 0.5), fill=c)
        for k in range(8):
            a = k * math.pi / 4
            d.line([(cx + math.cos(a) * s * 0.7, cy + math.sin(a) * s * 0.7), (cx + math.cos(a) * s, cy + math.sin(a) * s)], fill=c, width=max(3, int(s / 6)))
    elif kind == "probe":
        d.ellipse((cx - s * 0.35, cy - s * 0.35, cx + s * 0.35, cy + s * 0.35), fill=c)
        d.pieslice((cx - s * 1.0, cy - s * 1.2, cx + s * 0.6, cy + s * 0.2), 200, 340, fill=c)
        d.line([(cx, cy), (cx + s, cy + s * 0.8)], fill=c, width=max(3, int(s / 6)))
        d.line([(cx, cy), (cx - s, cy + s * 0.8)], fill=c, width=max(3, int(s / 6)))
    elif kind == "clock":
        d.ellipse((cx - s, cy - s, cx + s, cy + s), outline=c, width=max(3, int(s / 6)))
        d.line([(cx, cy), (cx, cy - s * 0.6)], fill=c, width=max(3, int(s / 6)))
        d.line([(cx, cy), (cx + s * 0.45, cy + s * 0.2)], fill=c, width=max(3, int(s / 6)))
    elif kind == "car":
        d.rounded_rectangle((cx - s, cy - s * 0.1, cx + s, cy + s * 0.5), int(s * 0.2), fill=c)
        d.polygon([(cx - s * 0.6, cy - s * 0.1), (cx - s * 0.35, cy - s * 0.6), (cx + s * 0.4, cy - s * 0.6), (cx + s * 0.65, cy - s * 0.1)], fill=c)
        for ox in (-0.55, 0.55):
            d.ellipse((cx + ox * s - s * 0.25, cy + s * 0.3, cx + ox * s + s * 0.25, cy + s * 0.8), fill=(12, 18, 34, 255), outline=c, width=3)
    elif kind == "star":
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            rr = s if k % 2 == 0 else s * 0.42
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        d.polygon(pts, fill=c)
    else:
        _orig_icon(d, kind, cx, cy, s, col)


M.icon = icon
