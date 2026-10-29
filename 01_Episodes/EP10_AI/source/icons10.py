import math
import icons9  # noqa
import mekong as M
_prev = M.icon


def icon(d, kind, cx, cy, s, col):
    c = col + (255,)
    if kind == "chip":
        d.rounded_rectangle((cx - s * 0.6, cy - s * 0.6, cx + s * 0.6, cy + s * 0.6), int(s * 0.12), outline=c, width=max(3, int(s / 7)))
        d.rectangle((cx - s * 0.25, cy - s * 0.25, cx + s * 0.25, cy + s * 0.25), fill=c)
        for k in range(-2, 3):
            o = k * s * 0.22
            for a, b in (((cx + o, cy - s * 0.6), (cx + o, cy - s)), ((cx + o, cy + s * 0.6), (cx + o, cy + s)),
                         ((cx - s * 0.6, cy + o), (cx - s, cy + o)), ((cx + s * 0.6, cy + o), (cx + s, cy + o))):
                d.line([a, b], fill=c, width=max(2, int(s / 9)))
    elif kind == "go":
        w = max(2, int(s / 10))
        for k in range(5):
            o = -s * 0.8 + k * s * 0.4
            d.line([(cx - s * 0.8, cy + o), (cx + s * 0.8, cy + o)], fill=c, width=w)
            d.line([(cx + o, cy - s * 0.8), (cx + o, cy + s * 0.8)], fill=c, width=w)
        for (x, y, f) in ((-0.4, -0.4, (20, 20, 24, 255)), (0.0, 0.0, (250, 250, 245, 255)), (0.4, 0.0, (20, 20, 24, 255)), (0.0, 0.4, (250, 250, 245, 255))):
            d.ellipse((cx + x * s - s * 0.2, cy + y * s - s * 0.2, cx + x * s + s * 0.2, cy + y * s + s * 0.2), fill=f, outline=c, width=2)
    elif kind == "net":
        pts = [[(cx - s * 0.8, cy + (k - 1) * s * 0.6) for k in range(3)], [(cx, cy + (k - 1.5) * s * 0.5) for k in range(4)], [(cx + s * 0.8, cy + (k - 0.5) * s * 0.6) for k in range(2)]]
        for A, B in ((pts[0], pts[1]), (pts[1], pts[2])):
            for a in A:
                for b in B:
                    d.line([a, b], fill=c, width=max(1, int(s / 14)))
        for row in pts:
            for (x, y) in row:
                d.ellipse((x - s * 0.13, y - s * 0.13, x + s * 0.13, y + s * 0.13), fill=c)
    elif kind == "card":
        d.polygon([(cx - s * 0.9, cy - s * 0.45), (cx + s * 0.9, cy - s * 0.45), (cx + s * 0.9, cy + s * 0.45), (cx - s * 0.7, cy + s * 0.45), (cx - s * 0.9, cy + s * 0.25)], outline=c, width=max(3, int(s / 7)))
        d.ellipse((cx - s * 0.6, cy - s * 0.2, cx - s * 0.2, cy + s * 0.2), fill=c)
    else:
        _prev(d, kind, cx, cy, s, col)


M.icon = icon
