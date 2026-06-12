"""Generate the GitHub profile README image: ASCII portrait left, neofetch-style info right.

Stats come from github-stats.json (produced by fetch_github_stats.py).
"""

import json
import os

from PIL import Image, ImageDraw, ImageFont

ASCII_PATH = "ascii-art.txt"
OUT_PATH = "github-profile.png"

BG = (13, 17, 23, 255)        # github dark bg
ART = (201, 209, 217, 255)    # light grey
LABEL = (255, 166, 87, 255)   # orange
DOTS = (110, 118, 129, 255)   # grey
VALUE = (121, 192, 255, 255)  # light blue
HEADER = (230, 237, 243, 255) # near white
RULE = (139, 148, 158, 255)   # grey
GREEN = (86, 211, 100, 255)   # additions
RED = (248, 81, 73, 255)      # deletions

ART_SIZE = 16
TEXT_SIZE = 26
PAD = 60
GAP = 70
TEXT_W = 62  # right column width in chars

# (regular, bold, is_ttc) - Menlo on macOS, DejaVu on GitHub Actions ubuntu runners
FONT_CANDIDATES = [
    ("/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Menlo.ttc", True),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", False),
]


def load_font(size, bold=False):
    for reg, bld, is_ttc in FONT_CANDIDATES:
        path = bld if bold else reg
        if not os.path.exists(path):
            continue
        if not is_ttc:
            return ImageFont.truetype(path, size)
        target = "Bold" if bold else "Regular"
        for i in range(4):
            try:
                f = ImageFont.truetype(path, size, index=i)
            except OSError:
                break
            if target in f.getname()[1] and "Italic" not in f.getname()[1]:
                return f
        return ImageFont.truetype(path, size, index=0)
    raise RuntimeError("no monospace font found")


def kv(label, value):
    used = 2 + len(label) + 2 + 1 + len(value)  # ". " + label + ": " + " " + value
    dots = "." * max(TEXT_W - used, 3)
    return [
        (". ", DOTS, False),
        (label + ":", LABEL, True),
        (" " + dots, DOTS, False),
        (" " + value, VALUE, False),
    ]


def section(title):
    fill = "─" * max(TEXT_W - len(title) - 4, 3)
    return [("─ ", RULE, False), (title + " ", HEADER, True), (fill, RULE, False)]


def kv2(l1, v1, l2, v2, left_w=31):
    right_w = TEXT_W - left_w - 3
    d1 = "." * max(left_w - (2 + len(l1) + 1 + 2 + len(v1)), 3)
    d2 = "." * max(right_w - (len(l2) + 1 + 2 + len(v2)), 3)
    return [
        (". ", DOTS, False),
        (l1 + ":", LABEL, True),
        (" " + d1, DOTS, False),
        (" " + v1, VALUE, False),
        (" | ", RULE, False),
        (l2 + ":", LABEL, True),
        (" " + d2, DOTS, False),
        (" " + v2, VALUE, False),
    ]


def loc_line(net, adds, dels):
    label = "Lines of Code on GitHub"
    net_s, add_s, del_s = f"{net:,}", f"{adds:,}++", f"{dels:,}--"
    used = 2 + len(label) + 1 + 2 + len(net_s) + 3 + len(add_s) + 2 + len(del_s) + 2
    dots = "." * max(TEXT_W - used, 1)
    return [
        (". ", DOTS, False),
        (label + ":", LABEL, True),
        (" " + dots, DOTS, False),
        (" " + net_s, VALUE, False),
        (" ( ", RULE, False),
        (add_s, GREEN, False),
        (", ", RULE, False),
        (del_s, RED, False),
        (" )", RULE, False),
    ]


def load_stats():
    stats = {"repos": 62, "stars": 11, "followers": 34,
             "commits": 0, "additions": 0, "deletions": 0, "net": 0}
    if os.path.exists("github-stats.json"):
        stats.update(json.load(open("github-stats.json")))
    return stats


STATS = load_stats()

# widen the column if the LOC line does not fit at the minimum width
_loc_chars = sum(len(t) for t, _, _ in loc_line(STATS["net"], STATS["additions"], STATS["deletions"]))
TEXT_W = max(TEXT_W, _loc_chars)


def header(user, host):
    title = user + "@" + host
    fill = "─" * max(TEXT_W - len(title) - 1, 3)
    return [(user, HEADER, True), ("@", LABEL, True), (host, HEADER, True), (" " + fill, RULE, False)]


LINES = [
    header("santi", "marro"),
    kv("OS", "macOS, Linux"),
    kv("Host", "Santex"),
    kv("Kernel", "AI Lead Specialist"),
    kv("Uptime", "2.5 years @ Santex"),
    kv("Shell", "zsh + Claude Code"),
    kv("Education", "PhD in AI, NLP"),
    kv("Location", "Cordoba, Argentina"),
    [(".", DOTS, False)],
    kv("Languages.Programming", "Python, TypeScript, SQL"),
    kv("Languages.AI", "Claude Code, Agent SDK, MCP, RAG"),
    kv("Languages.Real", "Spanish, English"),
    [(".", DOTS, False)],
    kv("Focus.Build", "agentic platforms, AI code analytics"),
    kv("Focus.Research", "NLP, reasoning assessment"),
    [(".", DOTS, False)],
    kv("Hobbies.Music", "vinyl (70+), guitar, live concerts"),
    kv("Hobbies.Music.Level", "flew to Europe for one show"),
    kv("Hobbies.Offline", "reading, gaming with friends"),
    [],
    section("Contact"),
    kv("Email", "smarro@gmail.com"),
    kv("LinkedIn", "santiago-marro"),
    kv("GitHub", "santimarro"),
    [],
    section("GitHub Stats"),
    kv2("Repos", str(STATS["repos"]), "Stars", str(STATS["stars"])),
    kv2("Commits", f"{STATS['commits']:,}", "Followers", str(STATS["followers"])),
    loc_line(STATS["net"], STATS["additions"], STATS["deletions"]),
]


def main():
    art_font = load_font(ART_SIZE)
    text_font = load_font(TEXT_SIZE)
    text_font_bold = load_font(TEXT_SIZE, bold=True)

    raw = open(ASCII_PATH).read().splitlines()
    art = [l.rstrip() for l in raw]
    while art and not art[0].strip():
        art.pop(0)
    while art and not art[-1].strip():
        art.pop()
    indent = min(len(l) - len(l.lstrip()) for l in art if l.strip())
    art = [l[indent:] for l in art]

    art_lh = int(ART_SIZE * 1.25)
    text_lh = int(TEXT_SIZE * 1.3)
    art_adv = art_font.getlength("M")

    art_w = int(max(len(l) for l in art) * art_adv)
    art_h = len(art) * art_lh
    text_w = 0
    for segments in LINES:
        w = sum((text_font_bold if bold else text_font).getlength(text)
                for text, _, bold in segments)
        text_w = max(text_w, int(w) + 1)
    text_h = len(LINES) * text_lh

    W = PAD + art_w + GAP + text_w + PAD
    H = 2 * PAD + max(art_h, text_h)

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, W - 1, H - 1], radius=40, fill=BG)

    y = (H - art_h) // 2
    for line in art:
        draw.text((PAD, y), line, font=art_font, fill=ART)
        y += art_lh

    x0 = PAD + art_w + GAP
    y = (H - text_h) // 2
    for segments in LINES:
        x = x0
        for text, color, bold in segments:
            f = text_font_bold if bold else text_font
            draw.text((x, y), text, font=f, fill=color)
            x += f.getlength(text)
        y += text_lh

    img.save(OUT_PATH)
    print(f"wrote {OUT_PATH} ({W}x{H})")


if __name__ == "__main__":
    main()
