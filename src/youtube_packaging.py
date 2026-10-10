"""youtube_packaging.py — Automated YouTube distribution packaging generator.

Generates:
1. 3 Viral Titles (<= 55 characters, all-caps, mobile-safe honest clickbait).
2. 3 Thumbnail Hooks & Hyper-detailed Google Flow Gothic prompts (Grenze Gotisch Black,
   monochrome warm sepia intaglio, 16:9 full-bleed zero-margin).
3. Accurate Chapter Timestamps calculated directly from rendered clips and outro.
4. Formatted YouTube Description with synopsis, chapters, music credits (Kevin MacLeod CC-BY),
   production credits, and tags.
5. Saves export/thumbnail_flow/thumbnail_flow_pack.json and generates thumbnail PNGs via
   Google Flow CDP runner (with deterministic fallback).
"""
import contextlib
import json
import math
import os
import re
import subprocess
import time
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from style_lock import PALETTE, MEDIUM


def get_clip_duration(clip_path):
    clip_path = Path(clip_path)
    if not clip_path.exists():
        return 8.0
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(clip_path)],
        capture_output=True, text=True
    )
    try:
        return float(r.stdout.strip())
    except Exception:
        return 8.0


def format_ts(seconds):
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _fit_title(prefix, base, limit=55):
    """Gabung prefix + judul tanpa memotong di tengah kata.

    Potong per-kata dari ekor sampai muat; kalau prefix saja sudah kepanjangan,
    kembalikan judul asli (dipotong per-kata) tanpa prefix.
    """
    base = base.strip()
    if len(prefix) + len(base) <= limit:
        return f"{prefix}{base}".upper()
    room = limit - len(prefix)
    if room >= len(base.split()[0]):
        words, out = base.split(), []
        for w in words:
            cand = " ".join(out + [w])
            if len(cand) > room:
                break
            out.append(w)
        if out:
            return f"{prefix}{' '.join(out)}".upper()
    # prefix tidak muat — pakai judul saja, potong per-kata
    words, out = base.split(), []
    for w in words:
        cand = " ".join(out + [w])
        if len(cand) > limit:
            break
        out.append(w)
    return (" ".join(out) or base[:limit]).upper()


def calculate_chapters(project_dir):
    project = Path(project_dir).resolve()
    story_p = project / "input" / "storyboard.json"
    clips_dir = project / "output" / "rendered_clips"
    audio_dir = project / "output" / "audio_supertonic"

    shots = []
    if story_p.exists():
        try:
            shots = json.loads(story_p.read_text(encoding="utf-8")).get("shots", [])
        except Exception:
            shots = []

    # Map chapter boundaries
    ch_starts = {}
    # Judul babak: per-proyek, dibaca dari input/chapters.json bila ada.
    # ponytail: file JSON opsional, bukan auto-generate dari narasi.
    # Upgrade: turunkan label dari narasi shot pertama tiap babak kalau file tak ada.
    ch_titles = {
        "1": "PROLOG & BABAK I — AWAL MULA & ANATOMI DANAU KAWAH",
        "2": "BABAK II — MALAM PETAKA LETUSAN",
        "3": "BABAK III — GELOMBANG LAHAR PANAS MENELAN KORBAN",
        "4": "BABAK IV — EVAKUASI & DAMPAK KEMANUSIAAN",
        "5": "BABAK V — REKAYASA SISTEM TEROWONGAN KAWAH TAVERNE",
    }
    ch_file = project / "input" / "chapters.json"
    if ch_file.exists():
        try:
            ch_titles = {str(k): v for k, v in
                         json.loads(ch_file.read_text(encoding="utf-8")).items()}
        except Exception:
            pass
    elif "a044" in project.name:
        ch_titles = {
            "1": "BABAK 1 — MISTERI CANDI SAMBISARI",
            "2": "BABAK 2 — JEJAK GEOLOGI BEMMELEN",
            "3": "BABAK 3 — ANATOMI ERUPSI KATATROPIK",
            "4": "BABAK 4 — PRALAYA MEDANG & EKSODUS",
            "5": "BABAK 5 — KAPSUL WAKTU LAHAR MERAPI",
        }


    for idx, s in enumerate(shots, 1):
        c = str(s.get("chapter", 1))
        if c not in ch_starts:
            ch_starts[c] = idx

    if not ch_starts:
        ch_starts = {"1": 1, "2": 20, "3": 40, "4": 60, "5": 75}

    running_sec = 0.0
    chapters = []
    seen_chapters = set()

    # Pre-calculate shot durations
    shot_durations = {}
    total_shots_count = len(shots) if shots else 90
    for i in range(1, total_shots_count + 1):
        sid = f"shot_{i:03d}"
        clip_f = clips_dir / f"{sid}.mp4"
        audio_f = audio_dir / f"{sid}.wav"
        if clip_f.exists():
            d = get_clip_duration(clip_f)
        elif audio_f.exists():
            d = get_clip_duration(audio_f) + 0.8
        else:
            d = 8.0
        shot_durations[i] = d

    sorted_ch_keys = sorted(ch_starts.keys(), key=lambda x: int(x) if x.isdigit() else 99)
    for ch_key in sorted_ch_keys:
        start_idx = ch_starts[ch_key]
        # Sum duration from 1 up to start_idx - 1
        t_at_start = sum(shot_durations.get(k, 8.0) for k in range(1, start_idx))
        if ch_key == "1":
            t_at_start = 0.0
        label = ch_titles.get(ch_key, f"BABAK {ch_key}")
        chapters.append({
            "time": format_ts(t_at_start),
            "title": label,
        })

    # Outro timestamp
    total_clips_duration = sum(shot_durations.values())
    chapters.append({
        "time": format_ts(total_clips_duration),
        "title": "PENUTUP & KESIMPULAN",
    })

    return chapters


def generate_youtube_metadata(project_dir):
    project = Path(project_dir).resolve()
    cfg_p = project / "project.json"
    cfg = json.loads(cfg_p.read_text(encoding="utf-8")) if cfg_p.exists() else {}

    raw_title = cfg.get("title", project.name).strip()
    clean_title = re.sub(r"^[a-zA-Z0-9_-]+\s*[-—:]\s*", "", raw_title)

    # 3 Viral Titles (<= 55 characters, all caps)
    title_1 = clean_title.upper()
    if len(title_1) > 55:
        title_1 = title_1[:52].rstrip() + "..."

    # Extract keywords
    is_kelud = "kelud" in clean_title.lower()
    is_merapi = "merapi" in clean_title.lower()
    custom_meta_p = project / "input" / "youtube_meta.json"

    if custom_meta_p.exists():
        cdata = json.loads(custom_meta_p.read_text(encoding="utf-8"))
        title_1 = cdata.get("title_1", title_1)
        title_2 = cdata.get("title_2", "")
        title_3 = cdata.get("title_3", "")
        hooks = cdata.get("hooks", [])
        scene_1 = cdata.get("scene_1", "")
        scene_2 = cdata.get("scene_2", "")
        scene_3 = cdata.get("scene_3", "")
        synopsis = cdata.get("synopsis", "")
        tags = cdata.get("tags", "")
    elif is_kelud:
        title_2 = "KIAMAT LAHAR KELUD 1919: 5.100 JIWA TERTELAN"
        title_3 = "TEROWONGAN KELUD: MONUMEN REKAYASA MITIGASI 1923"
        hooks = [
            "LAHAR MAUT KELUD 1919",
            "5.100 JIWA TERTELAN",
            "TEROWONGAN BAWAH TANAH",
        ]
        scene_1 = (
            "A colossal apocalyptic nocturnal eruption of Mount Kelud volcano in 1919. "
            "Titanic vertical ash column rising into the night sky, violent volcanic lightning bolts, "
            "glowing molten magma fissures along the crater rim, and the boiling crater lake violently "
            "ejecting tens of millions of cubic meters of scalding water and mud down the mountain flank."
        )
        scene_2 = (
            "Dramatic forensic historical catastrophe scene in 1919: a monstrous primary boiling lahar surge "
            "of dark mud, volcanic boulders, and steam sweeping through the fertile sugarcane plantations and villages "
            "of Kediri and Blitar in the dead of night. Silhouettes of colonial brick sugar mills and thatched village "
            "dwellings being overwhelmed by the catastrophic sediment torrent."
        )
        scene_3 = (
            "Engineering and historical geological recovery scene in 1923: construction of the world-famous "
            "Kelud crater lake drainage tunnel system. Dutch colonial engineers and Javanese miners excavating "
            "a massive horizontal drainage adit through solid volcanic bedrock and basalt formations, with surveyor "
            "instruments, lanterns, wooden timber shoring, and draining lake waters."
        )
        synopsis = (
            "Pada malam 19 Mei 1919, Gunung Kelud di Jawa Timur memuntahkan isi danau kawahnya dalam salah satu "
            "bencana vulkanik paling mematikan dalam sejarah modern Indonesia. Hampir empat puluh juta meter kubik air kawah "
            "mendidih bercampur piroklastik membentuk lahar letusan primer yang menyapu puluhan desa di Kediri dan Blitar, "
            "menewaskan lebih dari 5.100 jiwa dalam hitungan menit.\n\n"
            "Tragedi kelam ini mendorong lahirnya terobosan rekayasa geologi sipil tertua di dunia: sistem terowongan "
            "drainase kawah Taverne pada tahun 1923 untuk menguras volume danau kawah dan mencegah bencana serupa terulang."
        )
        tags = "#Kelud1919 #GunungKelud #LaharKelud #BencanaVulkanik #SejarahNusantara #Geologi #DokumenterIndonesia #Project404"
    elif is_merapi:
        title_2 = "MISTERI CANDI KUNO YANG TERTELAN ABU VULKANIK"
        title_3 = "PRALAYA MERAPI: ALASAN IBU KOTA MATARAM PINDAH"
        hooks = [
            "MERAPI 1006: MATARAM HANCUR",
            "TERKUBUR 6 METER LAHAR",
            "PRALAYA KIAMAT MEDANG",
        ]
        scene_1 = "A colossal apocalyptic eruption of ancient Mount Merapi towering over the lush volcanic plains of Central Java."
        scene_2 = "Dramatic archaeological discovery scene: an ancient classical Hindu temple standing completely intact inside an enormous excavated pit."
        scene_3 = "Cataclysmic historical catastrophe scene: the ancient royal capital of Medang being engulfed by pyroclastic surge."
        synopsis = (
            "MERAPI 1006 Masehi mengungkap salah satu misteri terbesar dalam sejarah peradaban Nusantara: mengapa "
            "Kerajaan Mataram Kuno yang membangun kemegahan Borobudur dan Prambanan tiba-tiba meninggalkan Jawa Tengah "
            "dan memindahkan pusat kerajaannya ke Jawa Timur?"
        )
        tags = "#Merapi1006 #MataramKuno #CandiSambisari #SejarahNusantara #Geologi #DokumenterIndonesia #Project404"
    else:
        title_2 = _fit_title("KIAMAT TOTAL: ", clean_title)
        title_3 = _fit_title("JEJAK SEJARAH: ", clean_title)
        hooks = [
            _fit_title("", clean_title, 24),
            "BENCANA MAHA DAHSYAT",
            "JEJAK YANG TERTELAN",
        ]
        scene_1 = f"Dramatic cinematic documentary establishing scene of {clean_title}, atmospheric historical disaster environment."
        scene_2 = f"Forensic geological and archival historical exploration scene examining evidence of {clean_title}."
        scene_3 = f"Monumental scientific discovery and reconstruction scene chronicling the aftermath and legacy of {clean_title}."
        synopsis = cfg.get("topic", f"Dokumenter investigatif mendalam mengenai {clean_title}.")
        tags = f"#{clean_title.replace(' ', '')} #SejarahNusantara #Geologi #DokumenterIndonesia #Project404"

    # Enforce mobile safe limit <= 55 chars without cutting words mid-word
    title_1 = _fit_title("", title_1, 55)
    title_2 = _fit_title("", title_2, 55)
    title_3 = _fit_title("", title_3, 55)
    titles = [title_1, title_2, title_3]
    assert all(len(t) <= 55 for t in titles), titles
    assert not any(t.rstrip().endswith((" M", " MALAM EMPAT M")) for t in titles[1:]), \
        f"judul terpotong di tengah kata: {titles}"

    # Calculate chapters
    chapters = calculate_chapters(project)
    ch_text = "\n".join(f"{c['time']} {c['title']}" for c in chapters)

    # Kredit musik: per-proyek dari assets/music/CREDITS.json bila ada.
    music_credit = [
        "Ossuary 5 - Rest by Kevin MacLeod (incompetech.com), CC BY 4.0",
        "Prelude and Action by Kevin MacLeod (incompetech.com), CC BY 4.0",
    ]
    cred_f = project / "assets" / "music" / "CREDITS.json"
    if cred_f.exists():
        try:
            loaded = json.loads(cred_f.read_text(encoding="utf-8"))
            if isinstance(loaded, list) and loaded:
                music_credit = loaded
        except Exception:
            pass
    music_text = "\n".join(
        f"- {c}\n  Licensed under Creative Commons: By Attribution 4.0 License"
        f"\n  http://creativecommons.org/licenses/by/4.0/"
        for c in music_credit
    )

    # YouTube Description
    description = f"""{synopsis.strip()}

CHAPTERS
{ch_text}

CREDIT MUSIK
{music_text}

CREDIT PRODUKSI
Production: Banyak Tau Studio
Voice Over: Supertonic v3 ({cfg.get('voice', 'M2')})
Visual Architecture: {MEDIUM} (Project 404 Style)
Master Film: 1920x1080 30fps Full-Bleed Borderless

{tags}"""

    # Build 3 Gothic Ornamental Prompts
    prompts = []
    scenes = [scene_1, scene_2, scene_3]
    for idx, (h_text, sc_text) in enumerate(zip(hooks, scenes)):
        p = f"""Edge-to-edge panoramic 16:9 cinematic shot, completely filling the entire widescreen canvas from corner to corner with zero margins and zero border.
{sc_text}
Visual style: dark historical documentary aesthetic, monochromatic warm sepia tone, rich charcoal-black ink shadows (#0A0705), glowing amber lava rim highlights (#FF8C00), and warm ivory highlights (#EBD8B1), fine 19th-century intaglio linework texture applied directly to the environment.
Framing: full-frame 16:9 camera view. The sky and landscape extend all the way to the top and side borders, the ground extends to the bottom border.

At the bottom center of the composition, place one monumental cinematic documentary headline reading exactly:
"{h_text}"
Typography specifications: render the headline specifically in the visual letterform style of GRENZE GOTISCH BLACK (the Google Fonts blackletter display family), NOT merely a generic font labelled Gothic. Massive uppercase Gothic Revival blackletter display lettering inspired by pointed cathedral arches, medieval carved-stone capitals, and Victorian Gothic title engravings. Thick wide letterforms with strong readable proportions, unmistakably angular crowns, clustered vertical stems, sharp chiseled medieval terminals, subtle decorative spurs, and restrained cathedral-window tracery and engraved filigree patterns carved INSIDE the main strokes of each letter. The ornament must visibly belong to the letterforms themselves, not become a border around the text. Cinematic and colossal, like the title of a historical disaster epic.
Render the headline in warm weathered ivory (#F4E7C8) with subtle antique-gold engraved highlights (#C69A52), deep charcoal-black dimensional outline, restrained inner shadow, and a faint amber rim glow. Use at most two centered lines, large mobile-readable characters, generous tracking, balanced kerning, and perfectly accurate spelling. Position the complete text block higher within the lower third: its lowest decorative serif, shadow, and flourish must remain at least 9% of the canvas height above the bottom edge, with at least 7% clear space from the left and right edges. No part of any letter may enter this bottom safe zone.
Absolute typography constraints: NOT Bebas Neue, not condensed sans-serif, not modern geometric sans-serif, not plain block font, not minimalist typography, NOT Western saloon lettering, NOT circus poster lettering, NOT Roman monumental capitals, NOT slab-serif, not thin blackletter, not illegible calligraphy. The silhouette must unmistakably read as Gothic Revival display lettering: angular pointed crowns, chiseled medieval terminals, clustered vertical strokes, and visible engraved tracery inside the thick letter bodies. No excessive swashes crossing other letters, no separate ornamental frame, no curved baseline, no warped text, no extra words.

Absolute negative constraints: no picture frame, no decorative border, no outer paper margins, no white border, no matting, no passe-partout, no vignette border, not an illustration inside a page, not a book plate, pure full-bleed image filling 100% of the frame, no text other than the headline, no watermark."""
        prompts.append(p)

    return {
        "titles": titles,
        "hooks": hooks,
        "chapters": chapters,
        "description": description.strip(),
        "thumbnail_prompts": prompts,
        "music_credit": music_credit,
    }


def create_fallback_thumbnail(png_path, hook_text, title_text, variant_num=1):
    w, h = 1920, 1080
    bg = Image.new("RGB", (w, h), (18, 12, 8))
    draw = ImageDraw.Draw(bg)

    # Draw etched grid lines
    for x in range(0, w, 48):
        draw.line([(x, 0), (x, h)], fill=(32, 22, 16), width=1)
    for y in range(0, h, 48):
        draw.line([(0, y), (w, y)], fill=(32, 22, 16), width=1)

    # Crosshatching & atmospheric glow
    for x in range(-100, w, 24):
        draw.line([(x, h), (x + 350, 0)], fill=(45, 30, 20), width=1)

    # Volcanic silhouette
    points = [
        (0, h),
        (300, 750),
        (w // 2 - 120, 360 + variant_num * 25),
        (w // 2 + 120, 390),
        (w - 280, 680),
        (w, h),
    ]
    draw.polygon(points, fill=(28, 18, 12), outline=(14, 9, 6))

    # Try font loading: repo assets first, then system fonts
    from cine_paths import find_font
    font_paths = [
        find_font("CourierPrime-Bold.ttf"),
        find_font("Georgia-Bold.ttf", "georgiab.ttf"),
        find_font("Poppins-Bold.ttf", "arialbd.ttf"),
    ]
    font_hook = None
    for fp in font_paths:
        if fp:
            try:
                font_hook = ImageFont.truetype(str(fp), 68)
                break
            except Exception:
                pass
    if not font_hook:
        font_hook = ImageFont.load_default()

    # Draw headline
    bbox = draw.textbbox((0, 0), hook_text, font=font_hook)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (w - tw) // 2
    ty = h - th - 120

    # Glow & outline
    for ox in (-3, 0, 3):
        for oy in (-3, 0, 3):
            draw.text((tx + ox, ty + oy), hook_text, font=font_hook, fill=(5, 3, 2))
    draw.text((tx, ty), hook_text, font=font_hook, fill=(244, 231, 200))

    png_path = Path(png_path)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    bg.save(str(png_path), format="PNG")
    return str(png_path)


_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"


def _assert_real_png(path):
    """Pastikan file adalah gambar asli (PNG/JPEG), bukan halaman login HTML.

    Jika Flow mengembalikan JPEG, konversi langsung menjadi PNG bersih.
    """
    p = Path(path)
    if not p.exists():
        raise ValueError(f"{p.name}: file tidak dibuat")
    head = p.open("rb").read(8)
    if head[:3] == _JPEG_MAGIC:
        try:
            from PIL import Image
            im = Image.open(p)
            im.save(p, format="PNG")
            return
        except Exception:
            pass
    if head != _PNG_MAGIC:
        snippet = head.decode("utf-8", "replace").strip()
        p.unlink(missing_ok=True)
        raise ValueError(
            f"{p.name}: bukan gambar asli (awalan {snippet!r}) — "
            "kemungkinan halaman login Flow, file dihapus"
        )
    if p.stat().st_size < 10000:
        raise ValueError(f"{p.name}: gambar terlalu kecil ({p.stat().st_size} byte)")


def build_youtube_pack(project_dir, generate_flow=True, delay=14):
    project = Path(project_dir).resolve()
    thumb_dir = project / "export" / "thumbnail_flow"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    meta_path = thumb_dir / "thumbnail_flow_pack.json"

    metadata = generate_youtube_metadata(project)

    thumbnails_data = []
    runner = None
    if generate_flow:
        try:
            from flow_assets import connect_runner
            runner = connect_runner()
        except Exception as exc:
            print(f"Flow runner tidak tersedia ({exc}); menggunakan fallback PNG berkualitas tinggi.", flush=True)

    try:
        for idx in range(3):
            variant_name = f"A/B {idx + 1}"
            hook = metadata["hooks"][idx]
            title = metadata["titles"][idx]
            prompt = metadata["thumbnail_prompts"][idx]
            png_name = f"thumbnail_FLOW_AB_{idx + 1}.png"
            png_file = thumb_dir / png_name

            if runner:
                try:
                    print(f"Generating Flow Thumbnail {variant_name}: {hook}...", flush=True)
                    runner.generate_one(prompt, png_file)
                    _assert_real_png(png_file)
                    print(f"✓ Saved Flow Thumbnail: {png_file}", flush=True)
                    if delay and idx < 2:
                        time.sleep(delay)
                except Exception as exc:
                    print(f"✗ Gagal generate Flow ({exc}); membuat fallback...", flush=True)
                    create_fallback_thumbnail(png_file, hook, title, variant_num=idx + 1)
            else:
                if not png_file.exists() or png_file.stat().st_size < 10000:
                    create_fallback_thumbnail(png_file, hook, title, variant_num=idx + 1)

            thumbnails_data.append({
                "variant": variant_name,
                "hook": hook,
                "title": title,
                "path": str(png_file).replace("\\", "/"),
                "prompt": prompt,
            })
    finally:
        if runner:
            try:
                runner.close()
            except Exception:
                pass

    pack = {
        "method": "Google Flow via CDP (Gothic Ornamental Display & Full-Bleed Etching)",
        "titles": metadata["titles"],
        "hooks": metadata["hooks"],
        "thumbnails": thumbnails_data,
        "description": metadata["description"],
        "chapters": metadata["chapters"],
        "music_credit": metadata["music_credit"],
        "metadata_path": str(meta_path).replace("\\", "/"),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    meta_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ YouTube distribution packaging saved: {meta_path}", flush=True)
    return pack


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--flow", action="store_true", default=False)
    args = ap.parse_args()
    res = build_youtube_pack(args.project, generate_flow=args.flow)
    print(f"DONE YouTube pack for {args.project}: {len(res['titles'])} titles, {len(res['thumbnails'])} thumbnails")
