"""EP.5 ຟີຊິກ — ມະນຸດທັງໂລກ ນ້ອຍເທົ່າກ້ອນນ້ຳຕານ"""
from common import *

DUR = 39.0
HOOK = ["ມະນຸດທຸກຄົນໃນໂລກ", ("ບັນຈຸໃສ່ກ້ອນນ້ຳຕານກ້ອນດຽວໄດ້!", AMBER)]

def cube(img, cx, cy, s, alpha=1.0, glow=True):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if glow:
        glow_spot(layer, cx, cy, s * 1.4, (200, 230, 255), 70)
    d = ImageDraw.Draw(layer)
    top = [(cx, cy - s), (cx + s * 0.87, cy - s * 0.5), (cx, cy), (cx - s * 0.87, cy - s * 0.5)]
    left = [(cx - s * 0.87, cy - s * 0.5), (cx, cy), (cx, cy + s), (cx - s * 0.87, cy + s * 0.5)]
    right = [(cx + s * 0.87, cy - s * 0.5), (cx, cy), (cx, cy + s), (cx + s * 0.87, cy + s * 0.5)]
    d.polygon(top, fill=(252, 252, 250, 255)); d.polygon(left, fill=(214, 216, 222, 255)); d.polygon(right, fill=(186, 190, 200, 255))
    r = np.random.default_rng(3)  # sugar-crystal sparkle
    for _ in range(40):
        u, v = r.random(2)
        x = cx - s * 0.87 + u * s * 1.74
        y = cy - s * 0.6 + v * s * 1.4
        d.point((x, y), fill=(255, 255, 255, 255))
    img.alpha_composite(with_alpha(layer, alpha))

def atom(img, t, cx, cy, R, alpha=1.0):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for k in range(3):
        ang = math.radians(k * 60)
        pts = []
        for q in np.linspace(0, 2 * math.pi, 120):
            x, y = R * math.cos(q), R * 0.36 * math.sin(q)
            pts.append((cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)))
        d.line(pts, fill=CYAN + (110,), width=4)
        q = t * (2.2 + k * 0.4) + k * 2
        x, y = R * math.cos(q), R * 0.36 * math.sin(q)
        ex, ey = cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)
        d.ellipse((ex - 16, ey - 16, ex + 16, ey + 16), fill=CYAN + (255,))
    d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=AMBER + (255,))
    img.alpha_composite(with_alpha(layer, alpha))

_rng = np.random.default_rng(11)
CROWD = [(_rng.uniform(60, W - 60), _rng.uniform(640, 1560), _rng.uniform(0, 1)) for _ in range(900)]

def scene(img, t):
    if t < 4:  # hook: cube
        cube(img, W / 2, 1120, 230 + 30 * ease(prog(t, 0, 2.5)))
    elif t < 9:  # atoms are mostly empty space
        a = fade(t, 4, 9, 0.3, 0.4)
        atom(img, t, W / 2, 1100, 400, a)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        draw_line(d, W / 2 + 120, 1040, "ນິວເຄລຍ", 44, AMBER, align="left")
        d.line((W / 2 + 20, 1090, W / 2 + 110, 1050), fill=AMBER + (255,), width=4)
        img.alpha_composite(with_alpha(layer, a * prog(t, 5, 5.5)))
        draw_block(img, W / 2, 330, ["ອາຕອມເກືອບທັງໝົດ", ("ແມ່ນພື້ນທີ່ຫວ່າງເປົ່າ", AMBER)], 72, alpha=a)
    elif t < 17:  # stadium vs pea
        a = fade(t, 9, 17, 0.3, 0.4)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        x0, y0, x1, y1 = 140, 720, 940, 1480
        d.rounded_rectangle((x0 - 40, y0 - 40, x1 + 40, y1 + 40), 120, fill=(52, 58, 80, 255))
        d.rectangle((x0, y0, x1, y1), fill=(46, 130, 70, 255))
        for i in range(6):
            if i % 2:
                d.rectangle((x0, y0 + i * (y1 - y0) / 6, x1, y0 + (i + 1) * (y1 - y0) / 6), fill=(54, 142, 78, 255))
        d.rectangle((x0, y0, x1, y1), outline=(240, 240, 240, 255), width=5)
        d.line((x0, (y0 + y1) / 2, x1, (y0 + y1) / 2), fill=(240, 240, 240, 255), width=5)
        d.ellipse((W / 2 - 110, 990, W / 2 + 110, 1210), outline=(240, 240, 240, 255), width=5)
        pea = 7
        d.ellipse((W / 2 - pea, 1100 - pea, W / 2 + pea, 1100 + pea), fill=AMBER + (255,))
        p = prog(t, 12.5, 13.2)
        if p > 0:
            r = 26 + 10 * math.sin(t * 6)
            d.ellipse((W / 2 - r, 1100 - r, W / 2 + r, 1100 + r), outline=AMBER + (255,), width=5)
            d.rounded_rectangle((W / 2 + 60, 1010, W / 2 + 400, 1080), 20, fill=(7, 11, 26, 210))
            draw_line(d, W / 2 + 230, 1062, "ນິວເຄລຍ = ເມັດຖົ່ວ", 40, AMBER)
        img.alpha_composite(with_alpha(layer, a))
        draw_block(img, W / 2, 330, ["ຖ້າອາຕອມໃຫຍ່ເທົ່າເດີ່ນບານ", ("ນິວເຄລຍຈະນ້ອຍເທົ່າເມັດຖົ່ວ", AMBER)], 64,
                   alpha=a)
    elif t < 26:  # squeeze 8 billion people into a sugar cube
        a = fade(t, 17, 26, 0.3, 0.4)
        p = ease_io(prog(t, 18.5, 23))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for x, y, ph in CROWD:
            px, py = lerp(x, W / 2, p), lerp(y, 1120, p)
            r = 7 * (1 - p) + 1
            d.ellipse((px - r, py - r, px + r, py + r), fill=(255, 210, 160, int(220 * (1 - 0.7 * p))))
        img.alpha_composite(with_alpha(layer, a))
        if p > 0.75:
            cube(img, W / 2, 1120, 130 * ease(prog(t, 22, 23.4)) + 1, a)
        draw_block(img, W / 2, 330, ["ບີບພື້ນທີ່ຫວ່າງອອກ", ("ມະນຸດ 8 ພັນລ້ານຄົນ", AMBER)], 72, alpha=a)
        if t > 23.4:
            draw_block(img, W / 2, BOTTOM_Y, [("= ກ້ອນນ້ຳຕານ 1 ກ້ອນ", CYAN)], 66, alpha=a * prog(t, 23.4, 23.9))
    elif t < 31:  # but extremely heavy
        a = fade(t, 26, 31, 0.3, 0.4)
        sink = 40 * ease(prog(t, 26.6, 27.4))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.rectangle((W / 2 - 300, 1260 + sink, W / 2 + 300, 1300 + sink), fill=(150, 156, 175, 255))
        d.polygon([(W / 2 - 60, 1300 + sink), (W / 2 + 60, 1300 + sink), (W / 2 + 130, 1480), (W / 2 - 130, 1480)],
                  fill=(100, 106, 125, 255))
        img.alpha_composite(with_alpha(layer, a))
        cube(img, W / 2, 1150 + sink, 130, a)
        draw_block(img, W / 2, 330, ["ແຕ່ໜັກ", ("ຫຼາຍຮ້ອຍລ້ານໂຕນ!", AMBER)], 84, alpha=a)
    else:  # CTA, back to the opening look
        cube(img, W / 2, 1120, 260, fade(t, 31, 99, 0.4, 1))
        a = fade(t, 31, DUR - 1.4, 0.4, 0.5)
        draw_block(img, W / 2, 330, ["ແບ່ງປັນໃຫ້ໝູ່", ("ທີ່ມັກວິທະຍາສາດເບິ່ງແດ່!", AMBER)], 72, alpha=a)
        draw_block(img, W / 2, BOTTOM_Y, [("ກົດຕິດຕາມ ຮູ້ບໍ່? ໄວ້ເລີຍ", CYAN)], 56, alpha=fade(t, 32.0, 35.5, 0.4, 0.4))
        share_cta(img, t, 35.6, DUR - 1.4)

if __name__ == "__main__":
    run(5, "ຟີຊິກ", "Astronomy.com", DUR, scene, HOOK, "EP05_SugarCube_9x16.mp4")
