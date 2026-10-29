import math
import icons10  # noqa
import mekong as M
_prev = M.icon


def icon(d, kind, cx, cy, s, col):
    c = col + (255,)
    w = max(3, int(s / 7))
    if kind == "compass":
        d.ellipse((cx - s, cy - s, cx + s, cy + s), outline=c, width=w)
        d.polygon([(cx, cy - s * 0.8), (cx + s * 0.2, cy), (cx - s * 0.2, cy)], fill=(255, 110, 95, 255))
        d.polygon([(cx, cy + s * 0.8), (cx + s * 0.2, cy), (cx - s * 0.2, cy)], fill=c)
    elif kind == "atom":
        for a in (0, 60, 120):
            r = math.radians(a)
            pts = [(cx + s * math.cos(t) * math.cos(r) - s * 0.35 * math.sin(t) * math.sin(r), cy + s * math.cos(t) * math.sin(r) + s * 0.35 * math.sin(t) * math.cos(r)) for t in [k * math.pi / 24 for k in range(49)]]
            d.line(pts, fill=c, width=max(2, int(s / 9)))
        d.ellipse((cx - s * 0.18, cy - s * 0.18, cx + s * 0.18, cy + s * 0.18), fill=c)
    elif kind == "medal":
        d.polygon([(cx - s * 0.5, cy - s), (cx - s * 0.1, cy - s), (cx + s * 0.1, cy - s * 0.3), (cx - s * 0.2, cy - s * 0.3)], fill=c)
        d.polygon([(cx + s * 0.5, cy - s), (cx + s * 0.1, cy - s), (cx - s * 0.1, cy - s * 0.3), (cx + s * 0.2, cy - s * 0.3)], fill=c)
        d.ellipse((cx - s * 0.6, cy - s * 0.35, cx + s * 0.6, cy + s * 0.85), outline=c, width=w)
        d.ellipse((cx - s * 0.3, cy - s * 0.05, cx + s * 0.3, cy + s * 0.55), fill=c)
    elif kind == "doc":
        d.polygon([(cx - s * 0.65, cy - s), (cx + s * 0.35, cy - s), (cx + s * 0.65, cy - s * 0.7), (cx + s * 0.65, cy + s), (cx - s * 0.65, cy + s)], outline=c, width=w)
        for k in range(4):
            y = cy - s * 0.4 + k * s * 0.38
            d.line([(cx - s * 0.4, y), (cx + s * 0.4, y)], fill=c, width=max(2, int(s / 9)))
    elif kind == "eclipse":
        d.ellipse((cx - s, cy - s, cx + s, cy + s), fill=c)
        d.ellipse((cx - s * 0.78, cy - s * 0.78, cx + s * 0.78, cy + s * 0.78), fill=(12, 18, 34, 255))
    elif kind == "plane":
        d.polygon([(cx + s, cy - s * 0.6), (cx - s, cy), (cx - s * 0.2, cy + s * 0.15), (cx, cy + s * 0.8), (cx + s * 0.2, cy + s * 0.1)], fill=c)
    else:
        _prev(d, kind, cx, cy, s, col)


M.icon = icon
