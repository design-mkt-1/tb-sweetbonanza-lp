#!/usr/bin/env python3
"""
Generate web-optimised assets for the TopBet x Sweet Bonanza landing page.

Reads the untouched originals in assets/Symbols, assets/Gameart and logo/,
writes everything index.html actually references into assets/web/, and
subsets the FiraGO webfonts from assets/fonts/_src/ into assets/fonts/.

Re-runnable and idempotent: both output trees are rebuilt from scratch each
time. Requires Pillow, fontTools and brotli (ImageMagick is not available on
this machine, so all raster work goes through Pillow).

    python scripts/build-assets.py
"""

import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path

from fontTools.subset import main as pyftsubset
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

# Sources are 3000-5800px game art; Pillow's decompression-bomb guard would
# otherwise refuse them.
Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parent.parent
SRC_SYMBOLS = ROOT / "assets" / "Symbols"
SRC_GAMEART = ROOT / "assets" / "Gameart"
SRC_LOGO = ROOT / "logo"
OUT = ROOT / "assets" / "web"
OUT_SYM = OUT / "sym"
FONTS = ROOT / "assets" / "fonts"
FONTS_SRC = FONTS / "_src"

# Total budget for assets/web/ + assets/fonts/. The page must stay light
# enough for a mobile landing page on a cold connection.
SIZE_BUDGET_KB = 600

# The brand guide (Figma slide 3:1756) specifies FiraGO. It is not on Google
# Fonts; fontsource is the only CDN that ships it.
FONT_WEIGHTS = (400, 500, 600, 700, 800)
FONT_CDN = (
    "https://cdn.jsdelivr.net/npm/@fontsource/firago@5.3.0/files/"
    "firago-latin-{weight}-normal.woff2"
)

# fontsource's FiraGO "latin" files are mislabelled: each one carries the full
# 2519-codepoint set (Cyrillic, Greek, Georgian) and weighs ~250K, so five
# weights would be 1.25M of font against 300K of imagery. Subset to what the
# page actually renders. Emoji are left to the system font.
FONT_UNICODES = ",".join(
    [
        "U+0020-007E",  # basic latin
        "U+00A0",  # nbsp
        "U+00D7",  # multiplication sign
        "U+00AE,U+2122",  # (R) and TM
        "U+2018-201D",  # curly quotes
        "U+2022",  # bullet, used for the masked password
        "U+2026",  # ellipsis
        "U+2192",  # right arrow
    ]
)

# source filename -> output slug. The names in assets/Symbols are the raw
# Pragmatic Play exports ("frsw_pic_5_red apple copy.png"); the page uses
# short semantic slugs. These are the LOSING symbols only.
#
# frsw_scatter (the lollipop) is deliberately left out: in Sweet Bonanza it is
# the real scatter, so showing it as a non-winning cell next to the 200%/150FS
# bomb would muddy the single "find this one symbol" rule the grid is built on.
SYMBOLS = {
    "frsw_pic_1_red heart gem copy.png": "gem-heart",
    "frsw_pic_2_square purple gem copy.png": "gem-purple",
    "frsw_pic_3_green polygon gem copy.png": "gem-green",
    "frsw_pic_4_blue rectangle gem copy.png": "gem-blue",
    "frsw_pic_5_red apple copy.png": "apple",
    "frsw_pic_6_purple plum copy.png": "plum",
    "frsw_pic_7_green watermelon copy.png": "watermelon",
    "frsw_pic_8_blue berries copy.png": "berries",
    "frsw_pic_9_yellow bananas copy.png": "bananas",
}

SYMBOL_PX = 256
SYMBOL_QUALITY = 82

# The one winning symbol. Unlike every other export this one is RGB with no
# alpha channel — the art sits on a pure-black plate — so it gets cropped to
# its content, re-padded to a square and rendered on a black card face rather
# than alpha-trimmed. Slightly larger than the others because it carries text.
WINNER_SRC = "winner_scatter.png"
WINNER_SLUG = "bomb"
WINNER_PX = 320
# Luminance above which a pixel counts as artwork rather than backing plate.
# The backing measures 0-3; the glow starts well above 8.
WINNER_BLACK_THRESHOLD = 8

report: list[tuple[str, int]] = []


def record(path: Path) -> None:
    report.append((str(path.relative_to(ROOT)), path.stat().st_size))


def trim_alpha(im: Image.Image) -> Image.Image:
    """Crop transparent padding. The exports carry a lot of it -- the scatter's
    real content is 1731x2046 inside a 2771x2763 canvas."""
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    bbox = im.getbbox()
    return im.crop(bbox) if bbox else im


def build_symbols() -> None:
    OUT_SYM.mkdir(parents=True, exist_ok=True)
    for filename, slug in SYMBOLS.items():
        src = SRC_SYMBOLS / filename
        if not src.exists():
            sys.exit(f"missing source symbol: {src}")
        with Image.open(src) as im:
            im.load()
            im = trim_alpha(im)
            im.thumbnail((SYMBOL_PX, SYMBOL_PX), Image.LANCZOS)
            dst = OUT_SYM / f"{slug}.webp"
            im.save(dst, "WEBP", quality=SYMBOL_QUALITY, method=6)
        record(dst)


def build_winner() -> None:
    src = SRC_SYMBOLS / WINNER_SRC
    if not src.exists():
        sys.exit(f"missing winning symbol: {src}")

    with Image.open(src) as im:
        im.load()
        im = im.convert("RGB")

        # No alpha to trim against, so find the artwork by luminance instead.
        mask = im.convert("L").point(
            lambda p: 255 if p > WINNER_BLACK_THRESHOLD else 0
        )
        bbox = mask.getbbox()
        if not bbox:
            sys.exit(f"{WINNER_SRC} looks entirely black")
        im = im.crop(bbox)

        # Square it on the same black the source uses, so the tile drops onto
        # the black card face without a visible seam. The 12% margin keeps the
        # fuse off the card's gold border.
        side = int(max(im.size) * 1.12)
        square = Image.new("RGB", (side, side), (0, 0, 0))
        square.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
        square = square.resize((WINNER_PX, WINNER_PX), Image.LANCZOS)

        dst = OUT_SYM / f"{WINNER_SLUG}.webp"
        square.save(dst, "WEBP", quality=88, method=6)
    record(dst)


def build_background() -> None:
    src = SRC_GAMEART / "frsw_basegame_BG.jpg"
    if not src.exists():
        sys.exit(f"missing source background: {src}")
    with Image.open(src) as im:
        im.load()
        im = im.convert("RGB")
        for width in (1600, 800):
            resized = im.copy()
            resized.thumbnail((width, width), Image.LANCZOS)
            dst = OUT / f"bg-candy-{width}.webp"
            # This sits behind a dark scrim at low opacity, so aggressive
            # compression is invisible.
            resized.save(dst, "WEBP", quality=70, method=6)
            record(dst)


def build_game_logo() -> None:
    variants = [
        ("Sweet Bonanza™_EN_landscape copy.png", "sb-logo-landscape", 900),
        ("Sweet Bonanza™_EN_Portrait copy.png", "sb-logo-portrait", 560),
    ]
    for filename, slug, width in variants:
        src = ROOT / "assets" / filename
        if not src.exists():
            sys.exit(f"missing source game logo: {src}")
        with Image.open(src) as im:
            im.load()
            im = trim_alpha(im)
            im.thumbnail((width, width * 2), Image.LANCZOS)
            dst = OUT / f"{slug}.webp"
            im.save(dst, "WEBP", quality=85, method=6)
        record(dst)


def build_og_image() -> None:
    """The link-preview card (og:image / twitter:image). Composed from the same
    key visual the page uses, so a shared link matches the landing page."""
    W, H = 1200, 630

    # Pillow cannot rasterise SVG and there is no PNG of the TopBet wordmark in
    # the repo, so the card carries the campaign key visual and the offer; the
    # brand name rides along in og:title / og:site_name. Drop a
    # logo/logo_topbet.png in and extend this function if that changes.
    with Image.open(SRC_GAMEART / "frsw_basegame_BG.jpg") as bg:
        bg.load()
        bg = bg.convert("RGB")
        scale = max(W / bg.width, H / bg.height)
        bg = bg.resize((round(bg.width * scale), round(bg.height * scale)), Image.LANCZOS)
        card = bg.crop((
            (bg.width - W) // 2, (bg.height - H) // 2,
            (bg.width - W) // 2 + W, (bg.height - H) // 2 + H,
        ))

    dark = Image.new("RGB", (W, H), (4, 4, 5))
    card = Image.blend(card, dark, 0.55)

    # Extra scrim over the left column so the headline sits on near-black
    # whatever the crop lands on, while the tile side keeps some candy colour.
    ramp = Image.new("L", (W, 1))
    for x in range(W):
        ramp.putpixel((x, 0), round(225 * (1 - x / (W - 1)) ** 1.1))
    card = Image.composite(dark, card, ramp.resize((W, H)))

    def paste_contain(path: Path, box_w: int, xy: tuple[int, int]) -> int:
        with Image.open(path) as art:
            art.load()
            art = art.convert("RGBA")
            h = round(art.height * box_w / art.width)
            art = art.resize((box_w, h), Image.LANCZOS)
            card.paste(art, xy, art)
        return h

    # Winning tile on the right. Its source has no alpha, so it goes on as a
    # rounded black plate with the same gold border the grid uses.
    tile = 260
    with Image.open(OUT_SYM / f"{WINNER_SLUG}.webp") as bomb:
        bomb.load()
        plate = Image.new("RGB", (tile, tile), (0, 0, 0))
        plate.paste(bomb.convert("RGB").resize((tile, tile), Image.LANCZOS), (0, 0))
        card.paste(plate, (W - tile - 80, (H - tile) // 2))
        ImageDraw.Draw(card).rectangle(
            [W - tile - 80, (H - tile) // 2, W - 80 - 1, (H - tile) // 2 + tile - 1],
            outline=(245, 200, 66), width=4,
        )

    logo_h = paste_contain(OUT / "sb-logo-landscape.webp", 420, (80, 96))

    with tempfile.TemporaryDirectory() as tmp:
        # Pillow needs a real sfnt; fontTools can strip the woff2 wrapper.
        def ttf(weight: int, size: int) -> ImageFont.FreeTypeFont:
            path = Path(tmp) / f"firago-{weight}.ttf"
            if not path.exists():
                f = TTFont(font_source(weight))
                f.flavor = None
                f.save(path)
            return ImageFont.truetype(str(path), size)

        draw = ImageDraw.Draw(card)
        y = 96 + logo_h + 54
        draw.text((80, y), "200% BONUS", font=ttf(800, 96), fill=(255, 255, 255))
        # --tb-alert rather than --tb-accent: #d21502 is too dark to hold up
        # against a photographic backdrop in a feed thumbnail.
        draw.text((80, y + 118), "+ 150 FREE SPINS", font=ttf(700, 52), fill=(255, 69, 58))

    dst = OUT / "og-image.jpg"
    card.save(dst, "JPEG", quality=82, optimize=True)
    record(dst)


def copy_svgs() -> None:
    for src_name, dst_name in (
        ("logo_topbet.svg", "topbet-logo.svg"),
        ("favicon_topbet.svg", "favicon.svg"),
    ):
        src = SRC_LOGO / src_name
        if not src.exists():
            sys.exit(f"missing source svg: {src}")
        dst = OUT / dst_name
        shutil.copyfile(src, dst)
        record(dst)


def font_source(weight: int) -> Path:
    """The full, un-subset FiraGO woff2, downloading it if this is a fresh
    checkout (assets/fonts/_src is gitignored)."""
    FONTS_SRC.mkdir(parents=True, exist_ok=True)
    name = f"firago-latin-{weight}-normal.woff2"
    src = FONTS_SRC / name
    if not src.exists():
        print(f"downloading {name} ...")
        urllib.request.urlretrieve(FONT_CDN.format(weight=weight), src)
    return src


def build_fonts() -> None:
    for weight in FONT_WEIGHTS:
        name = f"firago-latin-{weight}-normal.woff2"
        src = font_source(weight)
        dst = FONTS / name
        pyftsubset(
            [
                str(src),
                f"--unicodes={FONT_UNICODES}",
                "--layout-features=kern,liga",
                "--flavor=woff2",
                f"--output-file={dst}",
            ]
        )
        record(dst)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for stale in FONTS.glob("*.woff2"):
        stale.unlink()

    build_symbols()
    build_winner()
    build_background()
    build_game_logo()
    copy_svgs()
    build_fonts()
    build_og_image()  # last: reuses the bomb tile and the resized game logo

    report.sort(key=lambda row: -row[1])
    total = sum(size for _, size in report)
    width = max(len(name) for name, _ in report)
    print(f"{'file':<{width}}  {'size':>9}")
    print("-" * (width + 11))
    for name, size in report:
        print(f"{name:<{width}}  {size / 1024:>8.1f}K")
    print("-" * (width + 11))
    print(f"{'TOTAL (' + str(len(report)) + ' files)':<{width}}  {total / 1024:>8.1f}K")

    if total > SIZE_BUDGET_KB * 1024:
        sys.exit(
            f"\nassets/web/ is {total / 1024:.1f}K, over the {SIZE_BUDGET_KB}K budget"
        )
    print(f"\nOK - under the {SIZE_BUDGET_KB}K budget.")


if __name__ == "__main__":
    main()
