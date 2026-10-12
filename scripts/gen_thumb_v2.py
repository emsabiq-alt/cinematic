#!/usr/bin/env python3
"""gen_thumb_v2.py — Generate 3 thumbnail v2 variants via Google Flow + PIL text.

Feedback user: lebih bagus & menarik dari v1 — satu elemen hero,
rule-of-thirds, depth berlapis, kontras maksimal, teks hook pendek.
"""
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "src"))
from flow_assets import connect_runner

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

OUT_DIR = REPO / "projects" / "sv001" / "input"
FONT = REPO / "assets" / "fonts" / "Montserrat-Black.ttf"

# (nama, prompt Flow, baris teks)
VARIANTS = [
    ("A",
     "Cinematic aerial night shot of Campi Flegrei volcanic caldera near Naples, "
     "one massive glowing lava fissure as hero element placed on right third, "
     "near-black shadows, white-hot lava highlights, layered depth with distant "
     "city lights bokeh, hard vignette, dramatic, ultra detailed, dark moody sky "
     "on left two-thirds (empty dark space for text)",
     ["RAKSASA", "DI BAWAH NAPOLI"]),
    ("B",
     "Cinematic wide shot of Naples city lights at night in lower third, massive "
     "glowing magma chamber visible as cracked earth beneath the city, one hero "
     "volcanic vent erupting embers on right third, near-black sky upper two-thirds "
     "(empty dark space for text), extreme contrast, white-hot highlights, "
     "hard vignette, dramatic scale, ultra detailed",
     ["500.000 JIWA", "DI ATAS MAGMA"]),
    ("C",
     "Cinematic underwater volcano scene, Santorini caldera, one colossal sea "
     "monster-like lava formation as hero on right third rising from dark depths, "
     "glowing orange cracks against near-black deep water, light rays from surface, "
     "upper two-thirds dark empty water (space for text), extreme contrast, "
     "hard vignette, dramatic, ultra detailed",
     ["MONSTER", "BAWAH LAUT"]),
]


def add_text(bg_path, lines, out_path):
    img = Image.open(bg_path).convert("RGB")
    # crop/resize ke 1280x720
    w, h = img.size
    target_ratio = 16 / 9
    if w / h > target_ratio:
        nw = int(h * target_ratio); x0 = (w - nw) // 2
        img = img.crop((x0, 0, x0 + nw, h))
    else:
        nh = int(w / target_ratio); y0 = (h - nh) // 2
        img = img.crop((0, y0, w, y0 + nh))
    img = img.resize((1280, 720), Image.LANCZOS)
    # sedikit boost kontras
    img = ImageEnhance.Contrast(img).enhance(1.15)

    d = ImageDraw.Draw(img)
    # ukuran font adaptif: baris terpanjang muat di ~1150px
    size = 130
    while size > 40:
        f = ImageFont.truetype(str(FONT), size)
        if max(d.textlength(l, font=f) for l in lines) <= 1150:
            break
        size -= 6
    f = ImageFont.truetype(str(FONT), size)
    # posisi: zona gelap kiri-atas (rule of thirds)
    y = 90
    for line in lines:
        # outline hitam tebal
        for ox in range(-4, 5):
            for oy in range(-4, 5):
                if ox * ox + oy * oy <= 16:
                    d.text((70 + ox, y + oy), line, font=f, fill=(0, 0, 0))
        d.text((70, y), line, font=f, fill=(255, 255, 255))
        y += size + 12
    img.save(out_path, quality=95)
    print(f"OK {out_path}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    runner = connect_runner()
    for name, prompt, lines in VARIANTS:
        bg = OUT_DIR / f"thumb-v2-{name}-bg.png"
        out = OUT_DIR / f"thumbnail-v2-{name}.png"
        print(f"[{name}] generate background via Flow...", flush=True)
        ok = runner.generate_one(prompt, str(bg), timeout=180)
        if not ok:
            print(f"[{name}] GAGAL generate, skip")
            continue
        add_text(str(bg), lines, str(out))
        time.sleep(2)
    print("Selesai.")


if __name__ == "__main__":
    main()
