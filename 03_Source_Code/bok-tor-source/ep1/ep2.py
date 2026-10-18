"""EP.2 ສິລະປະ — ໂມນາລີຊາ ດັງຂຶ້ນຍ້ອນຖືກລັກ?"""
from common import *

DUR = 40.0
HOOK = ["ພາບວາດທີ່ດັງທີ່ສຸດໃນໂລກ", ("ດັງຂຶ້ນມາຍ້ອນຖືກລັກ?", AMBER)]

def painting(img, cx, cy, w, h, empty=0.0, alpha=1.0, spot=True):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if spot:
        glow_spot(layer, cx, cy - h * 0.1, w * 0.85, (255, 220, 160), 70)
    d = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    fr = 34
    d.rectangle((x0 - fr, y0 - fr, x1 + fr, y1 + fr), fill=GOLD + (255,))
    d.rectangle((x0 - fr + 8, y0 - fr + 8, x1 + fr - 8, y1 + fr - 8), outline=(250, 210, 120, 255), width=4)
    d.rectangle((x0 - 6, y0 - 6, x1 + 6, y1 + 6), fill=(120, 86, 30, 255))
    # canvas: muted landscape + a generic seated figure silhouette (illustration only)
    canvas = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 255))
    cd = ImageDraw.Draw(canvas)
    for i in range(int(h)):
        f = i / h
        c = (int(lerp(110, 50, f)), int(lerp(120, 45, f)), int(lerp(90, 30, f)), 255)
        cd.line((0, i, w, i), fill=c)
    cd.ellipse((w * 0.18, h * 0.55, w * 0.82, h * 1.25), fill=(45, 32, 22, 255))      # shoulders
    cd.ellipse((w * 0.36, h * 0.2, w * 0.64, h * 0.56), fill=(40, 28, 20, 255))       # hair
    cd.ellipse((w * 0.4, h * 0.24, w * 0.6, h * 0.52), fill=(196, 150, 92, 255))     # face
    cd.ellipse((w * 0.42, h * 0.88, w * 0.6, h * 0.98), fill=(196, 150, 92, 255))    # hands
    canvas = canvas.filter(ImageFilter.GaussianBlur(2))
    wall = Image.new("RGBA", canvas.size, (64, 52, 46, 255))
    wd = ImageDraw.Draw(wall)
    wd.rectangle((8, 8, w - 8, h - 8), outline=(84, 70, 62, 255), width=6)
    for hx, hy in ((0.2, 0.08), (0.8, 0.08), (0.2, 0.92), (0.8, 0.92)):
        wd.ellipse((w * hx - 9, h * hy - 9, w * hx + 9, h * hy + 9), fill=(170, 170, 175, 255))
    canvas = Image.blend(canvas, wall, empty)
    layer.alpha_composite(canvas, (int(x0), int(y0)))
    if empty > 0.5:  # empty wall: only hooks, frame removed
        pass
    img.alpha_composite(with_alpha(layer, alpha))

def person(d, x, y, s, col):
    d.ellipse((x - 18 * s, y - 120 * s, x + 18 * s, y - 84 * s), fill=col)
    d.rounded_rectangle((x - 30 * s, y - 80 * s, x + 30 * s, y), 22 * s, fill=col)

def newspaper(img, cx, cy, ang, scale, alpha):
    p = Image.new("RGBA", (420, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(p)
    d.rectangle((0, 0, 420, 300), fill=(236, 228, 210, 255))
    draw_line(d, 210, 70, "ຂ່າວດ່ວນ!", 54, (30, 30, 30), 700)
    d.line((24, 92, 396, 92), fill=(60, 60, 60, 255), width=4)
    d.rectangle((24, 112, 170, 270), fill=(150, 140, 120, 255))
    for i in range(7):
        d.line((190, 120 + i * 22, 396, 120 + i * 22), fill=(120, 120, 120, 255), width=6)
    p = p.resize((int(420 * scale), int(300 * scale))).rotate(ang, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(with_alpha(p, alpha), (int(cx - p.width / 2), int(cy - p.height / 2)))

def scene(img, t):
    # 0-3.5 hook, painting
    if t < 3.5:
        painting(img, W / 2, 1120, 470, 640)
    # 3.5-10 1911: stolen from the Louvre
    elif t < 10:
        a = fade(t, 3.5, 10, 0.3, 0.4)
        e = ease(prog(t, 5.6, 7.0))
        painting(img, W / 2, 1120, 470, 640, empty=e, alpha=a)
        draw_block(img, W / 2, 330, [("ປີ 1911", AMBER)], 130, alpha=a)
        draw_block(img, W / 2, 560, ["ພິພິທະພັນລູບ, ປາຣີ"], 54, MUTED, alpha=a * fade(t, 4, 10, 0.4, 0.4))
        if e > 0.6:
            draw_block(img, W / 2, BOTTOM_Y, [("ຫາຍໄປ!", RED)], 92, alpha=a * prog(t, 6.6, 7.0))
    # 10-14 headlines everywhere
    elif t < 14:
        a = fade(t, 10, 14, 0.3, 0.4)
        painting(img, W / 2, 1120, 470, 640, empty=1, alpha=a * 0.6)
        for i, (x, y, ang) in enumerate(((330, 900, 12), (760, 1080, -9), (400, 1320, -4), (720, 760, 6))):
            p = ease(prog(t, 10.2 + i * 0.4, 11.0 + i * 0.4))
            newspaper(img, lerp(W / 2, x, p), lerp(1900, y, p), ang, 0.9, a * p)
        draw_block(img, W / 2, 330, ["ໜັງສືພິມທົ່ວໂລກ", ("ລົງຂ່າວຫຼາຍເດືອນ", AMBER)], 72, alpha=a)
    # 14-19 crowds queue to see the empty wall
    elif t < 19:
        a = fade(t, 14, 19, 0.3, 0.4)
        painting(img, W / 2, 1000, 470, 640, empty=1, alpha=a)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        n = int(2 + 9 * ease(prog(t, 14.3, 17)))
        for i in range(n):
            x = 120 + (i % 6) * 168 + (40 if i >= 6 else 0)
            y = 1560 if i < 6 else 1640
            person(d, x, y, 1.15 if i >= 6 else 1.0, (30, 36, 60, 255) if i >= 6 else (52, 60, 92, 255))
        img.alpha_composite(with_alpha(layer, a))
        draw_block(img, W / 2, 330, ["ຄົນແຫ່ໄປເບິ່ງ", ("ຝາຫວ່າງໆ!", AMBER)], 72, alpha=a)
    # 19-24 caught in Italy, 1913, 28 months later
    elif t < 24:
        a = fade(t, 19, 24, 0.3, 0.4)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        x0, x1, y = 160, 920, 1050
        p = ease_io(prog(t, 19.6, 22))
        d.line((x0, y, x1, y), fill=(255, 255, 255, 60), width=10)
        d.line((x0, y, lerp(x0, x1, p), y), fill=AMBER + (255,), width=10)
        for x, lab in ((x0, "1911"), (x1, "1913")):
            d.ellipse((x - 22, y - 22, x + 22, y + 22), fill=(AMBER if x == x0 or p > 0.98 else MUTED) + (255,))
            draw_line(d, x, y - 50, lab, 64, CREAM, 800)
        draw_line(d, W / 2, y + 110, "28 ເດືອນ", 56, MUTED, 400)
        draw_line(d, x0, y + 110, "ຫາຍໄປ", 44, MUTED, 400)
        if p > 0.98:
            draw_line(d, x1, y + 110, "ໄດ້ຄືນ", 44, AMBER, 700)
        img.alpha_composite(with_alpha(layer, a))
        draw_block(img, W / 2, 330, ["ຈັບຄົນລັກໄດ້", ("ຢູ່ຟລໍເຣນ, ອີຕາລີ", AMBER)], 72, alpha=a * fade(t, 20.4, 24, 0.4, 0.4))
    # 24-30 back on the wall, world-famous
    elif t < 30:
        a = fade(t, 24, 30, 0.4, 0.4)
        s = 0.9 + 0.1 * ease(prog(t, 24, 27))
        painting(img, W / 2, 1120, 470 * s, 640 * s, alpha=a)
        draw_block(img, W / 2, 330, ["ກາຍເປັນພາບທີ່", ("ທຸກຄົນຮູ້ຈັກ", AMBER)], 76, alpha=a)
    # 30-38 CTA, ends on the opening look
    else:
        painting(img, W / 2, 1120, 470, 640, alpha=fade(t, 30, 99, 0.4, 1))
        a = fade(t, 30, DUR - 1.4, 0.4, 0.5)
        draw_block(img, W / 2, 330, ["ຖ້າບໍ່ຖືກລັກ", "ພາບນີ້ຈະດັງ", ("ຂະໜາດນີ້ບໍ່?", AMBER)], 68, alpha=a)
        draw_block(img, W / 2, BOTTOM_Y, [("ຄອມເມັ້ນມາເລີຍ!", CYAN)], 66, alpha=fade(t, 31.0, 34.5, 0.4, 0.4))
        share_cta(img, t, 34.6, DUR - 1.4)

if __name__ == "__main__":
    run(2, "ສິລະປະ", "Smithsonian, History.com", DUR, scene, HOOK, "EP02_MonaLisa_9x16.mp4")
