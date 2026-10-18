"""Three minimal logo directions for ບອກຕໍ່ຄວາມຮູ້. Flat colour, one mark, no gradients/glow."""
from PIL import Image, ImageDraw, ImageFont

S = 4096                       # draw big, downsample for clean edges
NAVY = (14, 26, 58)
CREAM = (250, 246, 238)
AMBER = (242, 163, 58)
LAO_B = "/root/fonts/lao700.ttf"
LAO_R = "/root/fonts/lao400.ttf"


def canvas(bg):
    return Image.new("RGB", (S, S), bg)


def bubble(d, box, fill, tail="left"):
    """Rounded speech bubble with a small tail at the bottom."""
    x0, y0, x1, y1 = box
    r = (x1 - x0) * 0.28
    d.rounded_rectangle(box, r, fill=fill)
    w = x1 - x0
    if tail == "left":
        d.polygon([(x0 + w * 0.18, y1 - r * 0.5), (x0 + w * 0.42, y1 - 2), (x0 + w * 0.08, y1 + w * 0.17)], fill=fill)


def arrow(d, cx, cy, size, fill, width):
    """Clean right-pointing arrow: shaft + chevron with round caps."""
    hx = cx + size * 0.5
    d.line([(cx - size * 0.5, cy), (hx - width * 0.3, cy)], fill=fill, width=width)
    for dy in (-1, 1):
        d.line([(hx, cy), (hx - size * 0.38, cy + dy * size * 0.38)], fill=fill, width=width)
    for (x, y) in [(cx - size * 0.5, cy), (hx - size * 0.38, cy - size * 0.38), (hx - size * 0.38, cy + size * 0.38), (hx, cy)]:
        d.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=fill)


def text_c(d, cx, cy, txt, size, fill, path=LAO_B):
    f = ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    d.text((cx, cy), txt, font=f, fill=fill, anchor="mm")


def option_a():
    """A — speech bubble + forward arrow ('tell' + 'pass on'). Cream on navy."""
    img = canvas(NAVY)
    d = ImageDraw.Draw(img)
    m = S * 0.27
    bubble(d, (m, m - S * 0.03, S - m, S - m - S * 0.03), CREAM)
    arrow(d, S / 2, S / 2 - S * 0.03, S * 0.26, NAVY, int(S * 0.045))
    return img


def option_b():
    """B — typographic: the name stacked, one amber full stop. Navy on cream."""
    img = canvas(CREAM)
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(LAO_B, int(S * 0.165), layout_engine=ImageFont.Layout.RAQM)
    l1, l2 = "ບອກຕໍ່", "ຄວາມຮູ້"
    x = S / 2 - max(f.getlength(l1), f.getlength(l2)) / 2
    d.text((x, S * 0.49), l1, font=f, fill=NAVY, anchor="ls")
    d.text((x, S * 0.70), l2, font=f, fill=NAVY, anchor="ls")
    dot = S * 0.032
    ex = x + f.getlength(l2) + dot * 1.8
    d.ellipse((ex - dot, S * 0.70 - dot * 2, ex + dot, S * 0.70), fill=AMBER)
    return img


def option_c():
    """C — relay: one dot passes to the next (knowledge handed on). Navy + amber on cream."""
    img = canvas(CREAM)
    d = ImageDraw.Draw(img)
    r = S * 0.10
    cy = S / 2 + S * 0.09
    x1, x2 = S * 0.32, S * 0.68
    lw = int(S * 0.034)
    top = cy - r - S * 0.06               # arc ends just above each dot
    d.arc((x1, top - S * 0.22, x2, top + S * 0.22), 180, 340, fill=NAVY, width=lw)
    # arrowhead at the right end, pointing down onto the amber dot
    import math
    ex, ey = S / 2 + (x2 - x1) / 2 * math.cos(math.radians(340)), top + S * 0.22 * math.sin(math.radians(340))
    h = S * 0.075
    d.polygon([(ex + h * 0.15, ey + h * 0.95), (ex - h * 0.75, ey - h * 0.15), (ex + h * 0.75, ey - h * 0.45)], fill=NAVY)
    d.ellipse((x1 - r, cy - r, x1 + r, cy + r), fill=NAVY)
    d.ellipse((x2 - r, cy - r, x2 + r, cy + r), fill=AMBER)
    return img


def lockup(mark_fn, path, bg, fg, accent):
    """Horizontal mark + wordmark for banners."""
    w, h = 3200, 900
    img = Image.new("RGB", (w, h), bg)
    m = mark_fn().resize((900, 900), Image.LANCZOS)
    img.paste(m, (0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(LAO_B, 230, layout_engine=ImageFont.Layout.RAQM)
    a, b = "ບອກຕໍ່", "ຄວາມຮູ້"
    x = 1000
    d.text((x, 470), a, font=f, fill=fg, anchor="ls")
    d.text((x + f.getlength(a) + 50, 470), b, font=f, fill=accent, anchor="ls")
    g = ImageFont.truetype(LAO_R, 90, layout_engine=ImageFont.Layout.RAQM)
    d.text((x + 6, 640), "ອາວະກາດ · ສິລະປະ · ເຕັກໂນໂລຢີ · ວິສະວະກຳ · ຟີຊິກ", font=g, fill=fg, anchor="ls")
    img.save(path)


if __name__ == "__main__":
    import os
    os.makedirs("brand/minimal", exist_ok=True)
    opts = {"A": option_a(), "B": option_b(), "C": option_c()}
    for k, im in opts.items():
        im.resize((1024, 1024), Image.LANCZOS).save(f"brand/minimal/logo_{k}_1024.png")
    # review sheet: each option large, as a circle avatar, and tiny (40 px) like in a comment list
    W, H = 1500, 620
    sheet = Image.new("RGB", (W, H), (236, 236, 236))
    d = ImageDraw.Draw(sheet)
    for i, (k, im) in enumerate(opts.items()):
        x = 30 + i * 490
        big = im.resize((300, 300), Image.LANCZOS)
        sheet.paste(big, (x, 30))
        mask = Image.new("L", (160, 160), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 160, 160), fill=255)
        sheet.paste(im.resize((160, 160), Image.LANCZOS), (x, 360), mask)
        m2 = Image.new("L", (40, 40), 0)
        ImageDraw.Draw(m2).ellipse((0, 0, 40, 40), fill=255)
        sheet.paste(im.resize((40, 40), Image.LANCZOS), (x + 190, 420), m2)
        d.text((x + 320, 40), k, fill=(40, 40, 40), font=ImageFont.truetype("/root/fonts/lat700.ttf", 48))
    sheet.save("brand/minimal/_review.png")
    print("ok")
