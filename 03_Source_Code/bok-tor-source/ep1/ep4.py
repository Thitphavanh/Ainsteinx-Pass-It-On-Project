"""EP.4 ວິສະວະກຳ — ຍອດຫໍໄອເຟລ ເຄື່ອນຕາມດວງອາທິດ"""
from common import *

DUR = 41.0
HOOK = ["ຍອດຫໍໄອເຟລ", ("ເຄື່ອນທີ່ທຸກມື້ ຕາມດວງອາທິດ!", AMBER)]
STEEL = (196, 150, 98)

def tower(img, cx, base, h, lean=0.0, alpha=1.0, lit=None):
    """Stylised lattice tower. lean = horizontal offset of the tip (px), curved, for illustration."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    def xoff(y):  # bend grows toward the top
        f = (base - y) / h
        return lean * f * f
    def half(y):
        f = (base - y) / h
        return 230 * (1 - f) ** 2.2 + 10
    ys = np.linspace(base, base - h, 26)
    left = [(cx + xoff(y) - half(y), y) for y in ys]
    right = [(cx + xoff(y) + half(y), y) for y in ys]
    col_l = STEEL if lit != "right" else (120, 92, 62)
    col_r = STEEL if lit != "left" else (120, 92, 62)
    if lit == "right":
        col_r = (255, 200, 120)
    d.line(left, fill=col_l + (255,), width=10)
    d.line(right, fill=col_r + (255,), width=10)
    for i in range(len(ys) - 1):
        d.line([left[i], right[i + 1]], fill=STEEL + (150,), width=3)
        d.line([right[i], left[i + 1]], fill=STEEL + (150,), width=3)
    for fy in (0.12, 0.38, 0.62):  # platforms
        y = base - h * fy
        d.rectangle((cx + xoff(y) - half(y) - 18, y - 8, cx + xoff(y) + half(y) + 18, y + 8), fill=STEEL + (255,))
    ay = base - h * 0.12  # arch between the legs
    d.arc((cx - half(base) + 60, ay - 40, cx + half(base) - 60, base + 120), 200, 340, fill=STEEL + (255,), width=8)
    tip = (cx + xoff(base - h), base - h)
    d.line([tip, (tip[0], tip[1] - 60)], fill=STEEL + (255,), width=6)
    img.alpha_composite(with_alpha(layer, alpha))
    return tip

def scene(img, t):
    if t < 3.5:  # hook
        tower(img, W / 2, 1500, 800)
        glow_spot(img, 880, 820, 90, (255, 230, 170), 220, 30)
    elif t < 9:  # steel expands with heat
        a = fade(t, 3.5, 9, 0.3, 0.4)
        p = ease(prog(t, 5.0, 8.0))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        L = 640 + 120 * p
        col = tuple(int(lerp(a0, b0, p)) for a0, b0 in zip((150, 155, 165), (255, 120, 60)))
        d.rounded_rectangle((W / 2 - L / 2, 1040, W / 2 + L / 2, 1150), 16, fill=col + (255,))
        if p > 0.05:
            arrow(d, (W / 2 - 330, 1240), (W / 2 - L / 2 - 20, 1240), AMBER + (255,))
            arrow(d, (W / 2 + 330, 1240), (W / 2 + L / 2 + 20, 1240), AMBER + (255,))
        draw_line(d, W / 2, 1360, "ຮ້ອນຂຶ້ນ ກໍຂະຫຍາຍຕົວ", 60, AMBER if p > 0.5 else CREAM)
        img.alpha_composite(with_alpha(layer, a))
        if p > 0.2:
            glow_spot(img, W / 2, 1095, 380, (255, 120, 40), int(70 * p * a))
        draw_block(img, W / 2, 330, ["ຫໍໄອເຟລເຮັດຈາກ", ("ເຫຼັກ", AMBER)], 76, alpha=a)
    elif t < 13:  # a few millimetres taller
        a = fade(t, 9, 13, 0.3, 0.4)
        p = ease(prog(t, 9.6, 11))
        tower(img, W / 2 - 80, 1500, 800 + 18 * p, alpha=a)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.line((880, 700 - 18 * p, 880, 1500), fill=(255, 255, 255, 80), width=4)
        arrow(d, (880, 780), (880, 690 - 18 * p), AMBER + (255,))
        draw_line(d, 880, 650 - 18 * p, "+ ຫຼາຍ ມມ", 46, AMBER)
        img.alpha_composite(with_alpha(layer, a))
        draw_block(img, W / 2, 330, ["ມື້ຮ້ອນ", ("ສູງຂຶ້ນຫຼາຍມິນລີແມັດ", AMBER)], 72, alpha=a)
    elif t < 21:  # sunny side expands more: tip leans away from the sun
        a = fade(t, 13, 21, 0.3, 0.4)
        p = ease_io(prog(t, 14.5, 17.5))
        glow_spot(img, 930, 820, 100, (255, 230, 170), int(230 * a), 34)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for k in range(5):  # sun rays toward the tower
            y = 900 + k * 120
            d.line((900, 860 + k * 40, 760, y), fill=(255, 220, 140, 70), width=6)
        img.alpha_composite(with_alpha(layer, a))
        tip = tower(img, W / 2 - 60, 1500, 800, lean=-120 * p, alpha=a, lit="right")
        if p > 0.3:
            l2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d2 = ImageDraw.Draw(l2)
            arrow(d2, (tip[0] + 90, tip[1] - 90), (tip[0] - 40, tip[1] - 90), CYAN + (255,))
            draw_line(d2, tip[0] - 60, tip[1] - 130, "ອ່ຽງໜີແດດ", 46, CYAN, align="center")
            draw_line(d2, W / 2, 1610, "(ຂະຫຍາຍເກີນຈິງ ເພື່ອໃຫ້ເຫັນ)", 32, MUTED, 400)
            img.alpha_composite(with_alpha(l2, a * prog(t, 16, 16.5)))
        draw_block(img, W / 2, 330, ["ແດດສ່ອງພຽງດ້ານດຽວ", ("ດ້ານນັ້ນຂະຫຍາຍຫຼາຍກວ່າ", AMBER)], 66, alpha=a)
    elif t < 27:  # top traces a ~15 cm circle over a sunny day (view from above)
        a = fade(t, 21, 27, 0.3, 0.4)
        p = prog(t, 21.8, 26.4)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        cx, cy, R = W / 2, 1130, 260
        d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=(255, 255, 255, 50), width=4)
        pts = [(cx + R * math.cos(math.pi + 2 * math.pi * q), cy + R * math.sin(math.pi + 2 * math.pi * q))
               for q in np.linspace(0, p, max(2, int(80 * p) + 2))]
        d.line(pts, fill=AMBER + (255,), width=12, joint="curve")
        x, y = pts[-1]
        d.ellipse((x - 26, y - 26, x + 26, y + 26), fill=CREAM + (255,))
        d.line((cx - R, cy + R + 70, cx + R, cy + R + 70), fill=CYAN + (255,), width=5)
        d.line((cx - R, cy + R + 50, cx - R, cy + R + 90), fill=CYAN + (255,), width=5)
        d.line((cx + R, cy + R + 50, cx + R, cy + R + 90), fill=CYAN + (255,), width=5)
        draw_line(d, cx, cy + R + 150, "ປະມານ 15 ຊັງຕີແມັດ", 54, CYAN)
        draw_line(d, cx, cy + 20, "ມອງຈາກເທິງ", 40, MUTED, 400)
        img.alpha_composite(with_alpha(layer, a))
        draw_block(img, W / 2, 330, ["ໃນມື້ແດດອອກ", ("ຍອດຫໍເຄື່ອນເປັນວົງ", AMBER)], 72, alpha=a)
    elif t < 31:  # why bridges have expansion joints
        a = fade(t, 27, 31, 0.3, 0.4)
        gap = 46 - 26 * (0.5 + 0.5 * math.sin((t - 27) * 2.2))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.rectangle((60, 1060, W / 2 - gap / 2, 1180), fill=(110, 115, 130, 255))
        d.rectangle((W / 2 + gap / 2, 1060, W - 60, 1180), fill=(110, 115, 130, 255))
        for x in range(100, W - 60, 140):
            if abs(x - W / 2) > 80:
                d.rectangle((x, 1110, x + 70, 1122), fill=(240, 220, 140, 255))
        d.rectangle((W / 2 - 60, 1180, W / 2 + 60, 1500), fill=(80, 84, 98, 255))
        draw_line(d, W / 2, 1000, "ຮ່ອງຂະຫຍາຍຕົວ", 54, AMBER)
        arrow(d, (W / 2, 1012), (W / 2, 1048), AMBER + (255,), width=6, head=20)
        img.alpha_composite(with_alpha(layer, a))
        draw_block(img, W / 2, 330, ["ຂົວ ແລະທາງລົດໄຟ", ("ຈຶ່ງຕ້ອງມີຮ່ອງນີ້", AMBER)], 72, alpha=a)
    else:  # CTA, back to the opening look
        k = fade(t, 31, 99, 0.4, 1)
        tower(img, W / 2, 1500, 800, alpha=k)
        glow_spot(img, 880, 820, 90, (255, 230, 170), int(220 * k), 30)
        a = fade(t, 31, DUR - 1.4, 0.4, 0.5)
        draw_block(img, W / 2, 330, ["ລອງສັງເກດຂົວໃກ້ບ້ານ", ("ເຈົ້າຈະເຫັນຮ່ອງນ້ອຍໆ!", AMBER)], 66, alpha=a)
        draw_block(img, W / 2, BOTTOM_Y, [("ກົດຕິດຕາມໄວ້ ມື້ອື່ນມີເລື່ອງໃໝ່", CYAN)], 54, alpha=fade(t, 33.0, 36.5, 0.4, 0.4))
        share_cta(img, t, 36.6, DUR - 1.4)

if __name__ == "__main__":
    run(4, "ວິສະວະກຳ", "La Tour Eiffel (ທາງການ)", DUR, scene, HOOK, "EP04_Eiffel_9x16.mp4")
