"""EP.3 ເຕັກໂນໂລຢີ — Bug ໂຕທຳອິດ ແມ່ນແມງແທ້ໆ"""
from common import *

DUR = 40.0
HOOK = ["Bug ໂຕທຳອິດໃນຄອມພິວເຕີ", ("ແມ່ນແມງແທ້ໆ!", AMBER)]

def moth(img, cx, cy, s, t=0.0, alpha=1.0, flap=True):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    k = 1 - (0.25 * (0.5 + 0.5 * math.sin(t * 14)) if flap else 0)
    wing1, wing2 = (150, 118, 82, 255), (118, 90, 60, 255)
    for side in (-1, 1):
        fw = [(cx, cy - 10 * s), (cx + side * 150 * s * k, cy - 95 * s), (cx + side * 175 * s * k, cy - 10 * s), (cx, cy + 10 * s)]
        hw = [(cx, cy + 5 * s), (cx + side * 125 * s * k, cy + 20 * s), (cx + side * 95 * s * k, cy + 95 * s), (cx, cy + 30 * s)]
        d.polygon(fw, fill=wing1); d.polygon(hw, fill=wing2)
        d.ellipse((cx + side * 95 * s * k - 14 * s, cy - 55 * s, cx + side * 95 * s * k + 14 * s, cy - 27 * s), fill=(80, 60, 40, 255))
        d.line([(cx + side * 6 * s, cy - 60 * s), (cx + side * 45 * s, cy - 130 * s)], fill=(90, 70, 50, 255), width=max(2, int(4 * s)))
    d.ellipse((cx - 16 * s, cy - 70 * s, cx + 16 * s, cy + 70 * s), fill=(92, 70, 48, 255))
    d.ellipse((cx - 14 * s, cy - 82 * s, cx + 14 * s, cy - 56 * s), fill=(70, 52, 36, 255))
    img.alpha_composite(with_alpha(layer, alpha))

def computer(img, t, alpha=1.0, error=0.0):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(3):
        x0 = 110 + i * 290
        d.rounded_rectangle((x0, 760, x0 + 270, 1460), 14, fill=(58, 64, 80, 255), outline=(90, 98, 120, 255), width=4)
        for r in range(9):
            for c in range(5):
                on = (math.sin(t * 6 + r * 1.7 + c * 2.3 + i) > 0.2)
                col = RED if error > 0.5 and on else ((AMBER if on else (80, 70, 50)))
                x, y = x0 + 40 + c * 48, 820 + r * 64
                d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=col + (255,))
        d.rectangle((x0 + 30, 1400, x0 + 240, 1430), fill=(40, 44, 56, 255))
    img.alpha_composite(with_alpha(layer, alpha))

def relays(img, t, alpha):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((90, 720, 990, 1480), 20, fill=(46, 50, 64, 255))
    for r in range(4):
        for c in range(5):
            x, y = 150 + c * 165, 780 + r * 175
            d.rounded_rectangle((x, y, x + 120, y + 130), 10, fill=(170, 150, 110, 255))
            d.rectangle((x + 20, y + 30, x + 100, y + 50), fill=(110, 90, 60, 255))
            d.line((x + 30, y + 80, x + 90, y + 80), fill=(80, 80, 90, 255), width=6)
    img.alpha_composite(with_alpha(layer, alpha))

def logbook(img, t, alpha):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((120, 700, 960, 1500), 12, fill=(238, 228, 200, 255))
    for i in range(14):
        d.line((150, 760 + i * 52, 930, 760 + i * 52), fill=(170, 190, 215, 255), width=2)
    d.line((240, 720, 240, 1480), fill=(220, 140, 140, 255), width=3)
    draw_line(d, 260, 800, "1545   Relay #70 Panel F", 34, (40, 50, 90), 400, align="left")
    draw_line(d, 260, 1420, "First actual case of bug being found.", 34, (40, 50, 90), 400, align="left")
    img.alpha_composite(with_alpha(layer, alpha))
    moth(img, 560, 1100, 1.25, t, alpha, flap=False)
    tape = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tape)
    td.rectangle((380, 1060, 740, 1140), fill=(255, 255, 240, 110))
    img.alpha_composite(with_alpha(tape, alpha))

def scene(img, t):
    if t < 3.5:  # hook
        computer(img, t, 0.35)
        moth(img, W / 2, 1120, 1.6 + 0.2 * ease(prog(t, 0, 2)), t)
    elif t < 10:  # 1947 Harvard Mark II misbehaves
        a = fade(t, 3.5, 10, 0.3, 0.4)
        err = 1.0 if (t > 7.2 and int(t * 4) % 2 == 0) else 0.0
        computer(img, t, a, error=1.0 if t > 7.2 else 0.0)
        draw_block(img, W / 2, 330, [("ປີ 1947", AMBER)], 130, alpha=a)
        draw_block(img, W / 2, 560, ["Harvard Mark II"], 54, MUTED, w=400, alpha=a)
        if t > 7.2:
            draw_block(img, W / 2, BOTTOM_Y, [("ເຄື່ອງເຮັດວຽກຜິດປົກກະຕິ!", RED)], 64, alpha=a * (0.6 + 0.4 * err))
    elif t < 15:  # open it: moth stuck in a relay
        a = fade(t, 10, 15, 0.3, 0.4)
        relays(img, t, a)
        z = ease(prog(t, 11, 12.2))
        if z > 0:
            moth(img, 562, 1135, 0.55, t, a * z, flap=False)
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(layer).ellipse((440, 1010, 690, 1260), outline=RED + (255,), width=10)
            img.alpha_composite(with_alpha(layer, a * z))
        draw_block(img, W / 2, 330, ["ພົບແມງກະເບື້ອກາງຄືນ", ("ຕິດຢູ່ໃນຣີເລ", AMBER)], 72, alpha=a)
    elif t < 22:  # the word existed, the insect was a first
        a = fade(t, 15, 22, 0.3, 0.4)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for i, (y, top, bot, col, t0) in enumerate(((760, "ຄຳວ່າ bug", "ໝາຍເຖິງບັນຫາເຄື່ອງຈັກ ມີມາກ່ອນແລ້ວ", CYAN, 15.3),
                                                   (1140, "ປີ 1947", "ພົບແມງແທ້ໆ ເທື່ອທຳອິດ!", AMBER, 18.0))):
            p = ease(prog(t, t0, t0 + 0.6))
            if p <= 0:
                continue
            x0 = lerp(-900, 110, p)
            d.rounded_rectangle((x0, y, x0 + 860, y + 300), 30, fill=(255, 255, 255, 22), outline=col + (255,), width=4)
            draw_line(d, x0 + 430, y + 120, top, 66, col, 800)
            draw_line(d, x0 + 430, y + 220, bot, 46, CREAM, 400)
        img.alpha_composite(with_alpha(layer, a))
        draw_block(img, W / 2, 330, ["Bug ທີ່ເປັນ", ("ແມງແທ້ໆ", AMBER)], 76, alpha=a)
    elif t < 30:  # taped into the logbook, now at the Smithsonian
        a = fade(t, 22, 30, 0.4, 0.4)
        logbook(img, t, a)
        draw_block(img, W / 2, 330, ["ຕິດໄວ້ໃນປຶ້ມບັນທຶກ"], 72, alpha=a)
        if t > 25.5:
            draw_block(img, W / 2, BOTTOM_Y, [("ປັດຈຸບັນຢູ່ພິພິທະພັນ Smithsonian", AMBER)], 50, alpha=a * prog(t, 25.5, 26))
    else:  # CTA, back to opening look
        computer(img, t, 0.35 * fade(t, 30, 99, 0.4, 1))
        moth(img, W / 2, 1120, 1.8, t, fade(t, 30, 99, 0.4, 1))
        a = fade(t, 30, DUR - 1.4, 0.4, 0.5)
        draw_block(img, W / 2, 330, ["ເຈົ້າເຄີຍພົບ bug", ("ແປກໆແບບໃດແດ່?", AMBER)], 72, alpha=a)
        draw_block(img, W / 2, BOTTOM_Y, [("ຂຽນມາເລົ່າໃຫ້ຟັງແດ່!", CYAN)], 66, alpha=fade(t, 31.0, 34.5, 0.4, 0.4))
        share_cta(img, t, 34.6, DUR - 1.4)

if __name__ == "__main__":
    run(3, "ເຕັກໂນໂລຢີ", "Computer History Museum", DUR, scene, HOOK, "EP03_FirstBug_9x16.mp4")
