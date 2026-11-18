#!/usr/bin/env python3
"""Render entry.png: one image summing up the world's news of
Tuesday 17 November 2026. Deterministic: no random, no time, no network,
fixed fonts. Run: python3 render.py  ->  entry.png beside this file."""

import os

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
PAPER = (247, 243, 234)
NAVY = (20, 33, 61)
NAVY_DARK = (13, 22, 42)
RED = (192, 57, 43)
GOLD = (232, 184, 75)
INK = (26, 26, 26)
MUTED = (88, 88, 88)
WHITE = (255, 255, 255)
BORDER = (222, 214, 198)
PANEL = (255, 255, 255)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def fb(size):
    return ImageFont.truetype(FONT_BOLD, size)


def fr(size):
    return ImageFont.truetype(FONT_REG, size)


def fit_font(draw, text, path, max_size, max_w):
    """Largest font size up to max_size whose text fits max_w on one line."""
    size = max_size
    while size > 10:
        fnt = ImageFont.truetype(path, size)
        if draw.textlength(text, font=fnt) <= max_w:
            return fnt
        size -= 1
    return ImageFont.truetype(path, 10)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, text, fnt, fill, max_w, leading=None):
    """Draw wrapped text; return y just below the last line."""
    lh = leading or int(fnt.size * 1.28)
    for line in wrap(draw, text, fnt, max_w):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += lh
    return y


# ---------------------------------------------------------------- icons
def icon_bridge(d, cx, cy, s, col):
    """Suspension bridge: two towers, sagging main cable, deck, water."""
    w = s
    x0, x1 = cx - w // 2, cx + w // 2
    t1, t2 = x0 + s // 6, x1 - s // 6
    top = cy - s // 2
    deck = cy + s // 6
    d.line([(x0, deck), (x1, deck)], fill=col, width=max(3, s // 22))
    for tx in (t1, t2):
        d.rectangle([tx - s // 40, top, tx + s // 40, deck], fill=col)
    # main cable: sags from tower tops down to just above the deck
    n = 24
    pts = []
    for i in range(n + 1):
        t = i / n
        x = t1 + (t2 - t1) * t
        # parabola: top at the towers, lowest at mid-span
        y = top + (deck - s // 10 - top) * 4 * t * (1 - t)
        pts.append((x, y))
    d.line(pts, fill=col, width=max(2, s // 30))
    # side spans from the towers down to the deck ends
    d.line([(x0, deck - s // 12), (t1, top)], fill=col,
           width=max(2, s // 30))
    d.line([(t2, top), (x1, deck - s // 12)], fill=col,
           width=max(2, s // 30))
    # suspenders from the cable down to the deck
    for i in range(1, 6):
        t = i / 6
        x = t1 + (t2 - t1) * t
        cable_y = top + (deck - s // 10 - top) * 4 * t * (1 - t)
        d.line([(x, cable_y), (x, deck)], fill=col, width=max(2, s // 40))
    for i in range(3):
        d.line([(x0, deck + s // 5 + i * s // 12),
                (x1, deck + s // 5 + i * s // 12)],
               fill=col, width=max(2, s // 40))


def icon_tanker(d, cx, cy, s, col):
    """Oil tanker: hull, containers, waves."""
    w = s
    x0, x1 = cx - w // 2, cx + w // 2
    hull_y = cy - s // 10
    d.polygon([(x0, hull_y), (x1, hull_y),
               (x1 - s // 6, hull_y + s // 4),
               (x0 + s // 8, hull_y + s // 4)], fill=col)
    for i in range(3):
        bx = x0 + s // 8 + i * s // 5
        d.rectangle([bx, hull_y - s // 5, bx + s // 6, hull_y],
                    fill=col)
    d.rectangle([x1 - s // 4, hull_y - s // 4, x1 - s // 8, hull_y],
                fill=col)
    for i in range(3):
        d.arc([x0 + i * s // 3, hull_y + s // 3,
               x0 + (i + 1) * s // 3, hull_y + s // 2],
              0, 180, fill=col, width=max(2, s // 30))


def icon_flags(d, cx, cy, s, col):
    """Three summit flags on poles."""
    for i, c in enumerate((RED, NAVY, GOLD)):
        px = cx - s // 3 + i * s // 3
        d.line([(px, cy - s // 2), (px, cy + s // 2)], fill=col,
               width=max(2, s // 30))
        d.polygon([(px, cy - s // 2), (px + s // 4, cy - s // 3),
                   (px, cy - s // 6)], fill=c)


def icon_globe(d, cx, cy, s, col):
    """Globe: circle with meridians and latitudes."""
    r = s // 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col,
              width=max(3, s // 25))
    d.ellipse([cx - r // 3, cy - r, cx + r // 3, cy + r], outline=col,
              width=max(2, s // 35))
    d.line([(cx - r, cy), (cx + r, cy)], fill=col, width=max(2, s // 35))
    d.arc([cx - r, cy - r // 2, cx + r, cy + r // 2], 0, 180, fill=col,
          width=max(2, s // 35))
    d.arc([cx - r, cy - r // 2, cx + r, cy + r // 2], 180, 360, fill=col,
          width=max(2, s // 35))


def icon_lock(d, cx, cy, s, col):
    """Padlock: shackle arc + body + keyhole."""
    r = s // 4
    d.arc([cx - r, cy - s // 2, cx + r, cy], 180, 360, fill=col,
          width=max(3, s // 22))
    d.rounded_rectangle([cx - s // 3, cy - s // 8, cx + s // 3, cy + s // 2],
                        radius=s // 12, fill=col)
    d.ellipse([cx - s // 18, cy + s // 12, cx + s // 18, cy + s // 4],
              fill=WHITE)
    d.rectangle([cx - s // 60, cy + s // 6, cx + s // 60, cy + s // 3],
                fill=WHITE)


def icon_rocket(d, cx, cy, s, col):
    """Rocket: body, nose, fins, flame, window."""
    d.polygon([(cx, cy - s // 2), (cx + s // 6, cy - s // 6),
               (cx + s // 6, cy + s // 4), (cx - s // 6, cy + s // 4),
               (cx - s // 6, cy - s // 6)], fill=col)
    d.polygon([(cx - s // 6, cy + s // 8), (cx - s // 3, cy + s // 3),
               (cx - s // 6, cy + s // 4)], fill=RED)
    d.polygon([(cx + s // 6, cy + s // 8), (cx + s // 3, cy + s // 3),
               (cx + s // 6, cy + s // 4)], fill=RED)
    d.polygon([(cx, cy + s // 4), (cx + s // 7, cy + s // 2),
               (cx - s // 7, cy + s // 2)], fill=GOLD)
    d.ellipse([cx - s // 12, cy - s // 6, cx + s // 12, cy - s // 12],
              fill=WHITE)


# ---------------------------------------------------------------- layout
STORIES = [
    ("MIDDLE EAST · WAR", "TANKERS HIT BY MINES NEAR HORMUZ",
     "Two tankers hit mines and caught fire south of Hormuz; Iranian "
     "drones struck a US radar base in Bahrain.",
     icon_tanker),
    ("ASIA · DIPLOMACY", "XI, TRUMP, PUTIN TO MEET IN SHENZHEN",
     "China confirms the first three-way summit of the three leaders, "
     "Thursday 19 November, at APEC.",
     icon_flags),
    ("ASIA · SUMMIT", "TRUMP IN MANILA FOR QUAD TALKS",
     "Trump joins Quad leaders at the ASEAN summit; vows the US will "
     "catch up with China on rare earths.",
     icon_globe),
    ("TECH · CYBERATTACK", "CYBERATTACK HITS 178 TOP WEBSITES",
     "Malicious code via Optimizely hit CNN, BBC, Zoom, HSBC and more "
     "to steal crypto and card data.",
     icon_lock),
    ("SPACE · LAUNCH", "VULCAN ROCKET FAILS AFTER LIFTOFF",
     "The ULA rocket failed minutes after launch from Florida; all 40 "
     "Amazon Leo satellites were lost.",
     icon_rocket),
]

ALSO = [
    "EU sanctions 12 people and 101 entities over Russia",
    "Delhi chokes in severe air pollution",
    "Japan protests after Russian jets violate its airspace",
]


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- header band
    d.rectangle([0, 0, W, 148], fill=NAVY)
    d.rectangle([0, 148, W, 154], fill=GOLD)
    d.text((48, 22), "T H E   W O R L D   I N   O N E   P I C T U R E",
           font=fb(25), fill=GOLD)
    date_fnt = fit_font(d, "TUESDAY 17 NOVEMBER 2026", FONT_BOLD, 62,
                        W - 96)
    d.text((48, 56), "TUESDAY 17 NOVEMBER 2026",
           font=date_fnt, fill=WHITE)

    # ---- lead story panel
    lx, ly, lw, lh = 24, 168, W - 48, 204
    d.rounded_rectangle([lx, ly, lx + lw, ly + lh], radius=14, fill=PANEL,
                        outline=BORDER, width=2)
    d.rounded_rectangle([lx, ly, lx + 12, ly + lh], radius=6, fill=RED)
    icon_bridge(d, lx + 118, ly + lh // 2 + 6, 150, NAVY)
    tx = lx + 218
    d.text((tx, ly + 20), "LEAD STORY · EUROPE · WAR",
           font=fb(20), fill=RED)
    head_fnt = fit_font(d, "UKRAINE HITS CRIMEA BRIDGE AGAIN", FONT_BOLD,
                        40, lw - 218 - 28)
    y = draw_wrapped(d, tx, ly + 50, "UKRAINE HITS CRIMEA BRIDGE AGAIN",
                     head_fnt, INK, lw - 218 - 28, leading=48)
    draw_wrapped(d, tx, y + 6,
                 "Second strike in under 24 hours halts traffic; "
                 "Zelenskyy hails an “unprecedented operation” as Russia "
                 "hits Kyiv bridges.",
                 fr(21), MUTED, lw - 218 - 28, leading=27)

    # ---- story grid: 2 columns x 3 rows
    gx, gy = 24, 388
    cw, chh, gap = 480, 176, 16
    for i, (kick, head, body, icon) in enumerate(STORIES):
        col, row = i % 2, i // 2
        px = gx + col * (cw + gap)
        py = gy + row * (chh + gap)
        d.rounded_rectangle([px, py, px + cw, py + chh], radius=12,
                            fill=PANEL, outline=BORDER, width=2)
        icon(d, px + 62, py + chh // 2, 92, NAVY)
        tx = px + 122
        d.text((tx, py + 14), kick, font=fb(16), fill=RED)
        y = draw_wrapped(d, tx, py + 38, head, fb(25), INK,
                         cw - 122 - 16, leading=30)
        lines = wrap(d, body, fr(17), cw - 122 - 16)[:3]
        by = y + 4
        for line in lines:
            d.text((tx, by), line, font=fr(17), fill=MUTED)
            by += 21

    # ---- also-today cell (bottom right of the grid)
    px = gx + (cw + gap)
    py = gy + 2 * (chh + gap)
    d.rounded_rectangle([px, py, px + cw, py + chh], radius=12,
                        fill=NAVY, outline=NAVY, width=2)
    d.text((px + 20, py + 14), "ALSO TODAY", font=fb(18), fill=GOLD)
    y = py + 44
    for item in ALSO:
        d.text((px + 20, y), "•", font=fb(18), fill=GOLD)
        y = draw_wrapped(d, px + 40, y, item, fr(17), WHITE,
                         cw - 60, leading=22) + 2

    # ---- footer
    fy = 952
    d.line([(24, fy), (W - 24, fy)], fill=BORDER, width=2)
    d.text((24, fy + 12),
           "Compiled from wire reports · All events happened or were first "
           "reported on 17 November 2026",
           font=fr(19), fill=MUTED)
    d.text((24, fy + 40), "17 NOV 2026  ·  THE WORLD IN ONE PICTURE",
           font=fb(17), fill=NAVY)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "entry.png")
    img.save(out, format="PNG")
    print("wrote", out, img.size)


if __name__ == "__main__":
    main()
