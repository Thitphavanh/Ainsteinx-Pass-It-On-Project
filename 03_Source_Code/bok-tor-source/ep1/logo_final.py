"""Final logo: relay mark (option C) with the channel name underneath, + minimal banner and cover."""
from PIL import Image, ImageChops, ImageDraw, ImageFont
from logo_minimal import option_c, NAVY, CREAM, AMBER, LAO_B, LAO_R, S

def mark_only():
    im = option_c()
    bg = Image.new("RGB", im.size, CREAM)
    box = ImageChops.difference(im, bg).getbbox()
    return im.crop(box)

MARK = mark_only()

def wordmark(d, cx, base, size, dot=True):
    f = ImageFont.truetype(LAO_B, size, layout_engine=ImageFont.Layout.RAQM)
    t = "ບອກຕໍ່ຄວາມຮູ້"
    w = f.getlength(t)
    r = size * 0.11
    total = w + (r * 3.2 if dot else 0)
    x = cx - total / 2
    d.text((x, base), t, font=f, fill=NAVY, anchor="ls")
    if dot:
        ex = x + w + r * 2
        d.ellipse((ex - r, base - 2 * r, ex + r, base), fill=AMBER)
    return w

def logo(size=1024):
    img = Image.new("RGB", (S, S), CREAM)
    mw = int(S * 0.46)
    m = MARK.resize((mw, int(MARK.height * mw / MARK.width)), Image.LANCZOS)
    top = int(S * 0.24)
    img.paste(m, ((S - mw) // 2, top))
    d = ImageDraw.Draw(img)
    wordmark(d, S / 2, top + m.height + S * 0.19, int(S * 0.095))
    return img.resize((size, size), Image.LANCZOS)

def lockup_banner(w, h, mark_h, text_size, gap, sub_size, path):
    sc = 2
    img = Image.new("RGB", (w * sc, h * sc), CREAM)
    d = ImageDraw.Draw(img)
    mh = mark_h * sc
    m = MARK.resize((int(MARK.width * mh / MARK.height), mh), Image.LANCZOS)
    f = ImageFont.truetype(LAO_B, text_size * sc, layout_engine=ImageFont.Layout.RAQM)
    tw = f.getlength("ບອກຕໍ່ຄວາມຮູ້") + text_size * sc * 0.35
    total = m.width + gap * sc + tw
    x0 = (w * sc - total) / 2
    cy = h * sc / 2
    img.paste(m, (int(x0), int(cy - mh / 2 - text_size * sc * 0.05)))
    tx = x0 + m.width + gap * sc
    d.text((tx, cy + text_size * sc * 0.18), "ບອກຕໍ່ຄວາມຮູ້", font=f, fill=NAVY, anchor="ls")
    r = text_size * sc * 0.11
    ex = tx + f.getlength("ບອກຕໍ່ຄວາມຮູ້") + r * 2
    base = cy + text_size * sc * 0.18
    d.ellipse((ex - r, base - 2 * r, ex + r, base), fill=AMBER)
    from common import draw_line   # mixes Lao + Latin fonts so the "·" separators render
    draw_line(d, tx + 4, base + sub_size * sc * 1.6, "ອາວະກາດ · ສິລະປະ · ເຕັກໂນໂລຢີ · ວິສະວະກຳ · ຟີຊິກ",
              sub_size * sc, NAVY, 400, align="left")
    img.resize((w, h), Image.LANCZOS).save(path)

if __name__ == "__main__":
    out = "brand/minimal/"
    lg = logo()
    lg.save(out + "logo_final_1024.png")
    lg.resize((800, 800), Image.LANCZOS).save(out + "logo_final_800.png")
    # YouTube: everything inside the 1546x423 centre safe area
    lockup_banner(2560, 1440, 230, 120, 70, 40, out + "youtube_banner_2560x1440.png")
    lockup_banner(1640, 924, 200, 100, 56, 34, out + "facebook_cover_1640x924.png")
    # review
    sheet = Image.new("RGB", (1500, 560), (236, 236, 236))
    sheet.paste(lg.resize((420, 420), Image.LANCZOS), (20, 20))
    mask = Image.new("L", (200, 200), 0); ImageDraw.Draw(mask).ellipse((0, 0, 200, 200), fill=255)
    sheet.paste(lg.resize((200, 200), Image.LANCZOS), (110, 450 - 100), mask) if False else None
    sheet.paste(lg.resize((200, 200), Image.LANCZOS), (470, 20), mask)
    m2 = Image.new("L", (48, 48), 0); ImageDraw.Draw(m2).ellipse((0, 0, 48, 48), fill=255)
    sheet.paste(lg.resize((48, 48), Image.LANCZOS), (546, 250), m2)
    yb = Image.open(out + "youtube_banner_2560x1440.png").resize((800, 450), Image.LANCZOS)
    gd = ImageDraw.Draw(yb)
    gd.rectangle((400 - 241, 225 - 66, 400 + 241, 225 + 66), outline=(255, 80, 80))
    sheet.paste(yb, (690, 20))
    sheet.save(out + "_review_final.png")
    print("ok")
