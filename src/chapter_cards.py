"""Chapter title cards and the closing card for any Project 404 film.

Reads the storyboard and project.json. Nothing here is named after one volcano.
The assembler calls ensure_cards() before it stitches the master, so a new film
gets its chapter cards and closing without a hand-copied script.

Closing type speed is deliberately slow (8 characters a second) and the face is
large (48px). Both live here, not in a per-film script, so the next film keeps them.
"""
import json
import random
import re
import subprocess
import wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Slow on purpose. The old per-film card typed at 19 chars/sec and read as a rush.
CLOSING_CHARS_PER_SEC = 8.0
CLOSING_FONT_PX = 48
CLOSING_HOLD_SEC = 6.0

ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}


def _font(project, px):
    path = Path(project) / "assets" / "fonts" / "CourierPrime-Bold.ttf"
    return ImageFont.truetype(str(path), px)


def _synth_hit(rate=48000, seconds=0.12):
    """Sintesis bunyi ketikan typewriter (klik perkusif + resonansi redam).

    Dipakai sebagai fallback bila file SFX tidak ada/rusak, supaya render
    tidak pernah gagal hanya karena satu file efek suara hilang.
    """
    n = int(seconds * rate)
    rng = np.random.default_rng(7)
    t = np.arange(n) / rate
    click = rng.standard_normal(n) * np.exp(-t * 220.0)
    body = (np.sin(2 * np.pi * 1750 * t) * 0.5
            + np.sin(2 * np.pi * 320 * t) * 0.35) * np.exp(-t * 55.0)
    samples = 0.6 * click + 0.4 * body
    peak = np.max(np.abs(samples))
    if peak > 0:
        samples = samples * (0.9 / peak)
    return (samples * 32767.0).astype(np.int16)


def _hit(project):
    p = Path(project) / "assets" / "sfx" / "typewriter_hit.wav"
    try:
        with wave.open(str(p), "rb") as w:
            return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    except Exception as e:
        print(f"[chapter_cards] SFX {p} tidak bisa dibaca ({e}); memakai sintesis fallback.", flush=True)
        return _synth_hit()


def _write_wav(path, samples, rate=48000):
    peak = np.max(np.abs(samples))
    if peak > 0.95:
        samples = samples * (0.95 / peak)
    pcm = (samples * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())


def _strikes(buffer, hit, times, rate, seed):
    random.seed(seed)
    last = 0
    for t_sec, ch in times:
        if ch in (" ", "\n"):
            continue
        i = int(t_sec * rate)
        if i + len(hit) < len(buffer):
            buffer[i:i + len(hit)] += (hit.astype(np.float32) / 32768.0) * random.uniform(0.62, 0.85)
            last = i + len(hit)
    buffer[last:] = 0.0
    return last


def _mux(avi, wav, out, seconds):
    fc = (
        "[1:a]adelay=40|40,volume=0.85[type];"
        f"anoisesrc=d={seconds:.2f}:c=brown:r=48000:a=0.030,lowpass=f=120[rumble];"
        "[type][rumble]amix=inputs=2:normalize=0:duration=first,"
        f"afade=t=out:st={max(seconds - 2.0, 0):.2f}:d=2.0[aout]"
    )
    subprocess.run([
        "ffmpeg", "-y", "-i", str(avi), "-i", str(wav),
        "-filter_complex", fc, "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
        "-t", f"{seconds:.2f}", str(out),
    ], check=True, capture_output=True)


def _year(title):
    m = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", title or "")
    return m.group(1) if m else ""


def _short_label(sentence):
    """A card title: the first few words of the chapter, cut on a word, never mid-word."""
    words = sentence.strip(" .").split()
    label, count = [], 0
    for w in words:
        if count and count + len(w) > 26:
            break
        label.append(w)
        count += len(w) + 1
        if len(label) == 5:
            break
    return " ".join(label).upper()


def chapter_plan(project):
    """Five cards. Titles live in the project's own chapter_titles.json, never in this file."""
    project = Path(project)
    cfg = json.loads((project / "project.json").read_text(encoding="utf-8"))
    titles = json.loads((project / "input" / "chapter_titles.json").read_text(encoding="utf-8"))
    year = _year(cfg.get("title", ""))
    plan = []
    for n in range(1, 6):
        row = titles[n - 1]
        tag = f"// {year} // BABAK {ROMAN[n]} //" if year else f"// BABAK {ROMAN[n]} //"
        plan.append((n, tag, row["title"].upper(), row["theme"].upper()))
    return plan


def _bridge_canvas():
    im = Image.new("RGB", (1920, 1080), (10, 10, 12))
    d = ImageDraw.Draw(im)
    for x in range(0, 1920, 48):
        d.line([(x, 0), (x, 1080)], fill=(20, 20, 24))
    for y in range(0, 1080, 48):
        d.line([(0, y), (1920, y)], fill=(20, 20, 24))
    return im


def _get_babak_bg(project, babak_num):
    """Ambil gambar shot babak, beri gradasi gelap sinematik & grid arsip; aman dengan fallback."""
    project = Path(project)
    total_shots = 90
    sb_p = project / "input" / "storyboard.json"
    if sb_p.exists():
        try:
            sb = json.loads(sb_p.read_text(encoding="utf-8"))
            total_shots = len(sb.get("shots", [])) or 90
        except Exception:
            pass

    per = max(1, total_shots // 5)
    shot_id = 1 + (babak_num - 1) * per
    candidates = [
        project / "output" / "flow_images" / f"shot_{shot_id:03d}.png",
        project / "output" / "flow_images" / "shot_001.png",
    ]
    chosen = None
    for c in candidates:
        if c.exists() and c.stat().st_size > 10000:
            chosen = c
            break

    if not chosen:
        flow_dir = project / "output" / "flow_images"
        if flow_dir.exists():
            pngs = sorted(flow_dir.glob("shot_*.png"))
            if pngs:
                chosen = pngs[0]

    if not chosen:
        return _bridge_canvas()

    try:
        from PIL import ImageEnhance, ImageFilter
        im = Image.open(chosen).convert("RGB")
        im_ratio = im.width / im.height
        target_ratio = 1920 / 1080
        if im_ratio > target_ratio:
            new_h = 1080
            new_w = int(new_h * im_ratio)
        else:
            new_w = 1920
            new_h = int(new_w / im_ratio)

        im = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = (new_w - 1920) // 2
        top = (new_h - 1080) // 2
        im = im.crop((left, top, left + 1920, top + 1080))
        im = ImageEnhance.Brightness(im).enhance(0.28)
        im = ImageEnhance.Contrast(im).enhance(1.15)
        im = im.filter(ImageFilter.GaussianBlur(radius=2))

        arr = np.array(im, dtype=np.float32)
        Y, X = np.ogrid[:1080, :1920]
        dist_x = (X - 960) / 960.0
        dist_y = (Y - 540) / 540.0
        rad = np.sqrt(dist_x**2 + dist_y**2)
        vignette = np.clip(1.0 - rad * 0.65, 0.15, 1.0)
        vert = 1.0 - (np.abs(Y - 540) / 540.0)**1.8 * 0.65
        scrim_mask = np.clip(np.abs(Y - 480) / 180.0, 0.4, 1.0)
        final_mask = np.clip(vignette * vert * scrim_mask, 0.12, 0.95)[:, :, np.newaxis]
        arr = (arr * final_mask).astype(np.uint8)
        bg = Image.fromarray(arr)

        d = ImageDraw.Draw(bg)
        for x in range(0, 1920, 60):
            d.line([(x, 0), (x, 1080)], fill=(22, 22, 26))
        for y in range(0, 1080, 60):
            d.line([(0, y), (1920, y)], fill=(22, 22, 26))
        return bg
    except Exception as e:
        print(f"  [WARN] Fallback canvas for bridge {babak_num}: {e}", flush=True)
        return _bridge_canvas()


def _apply_glitch(bgr, intensity=0.5, seed=42):
    """Efek sinematik analog-digital glitch: chromatic aberration & horizontal slice displacement."""
    if intensity <= 0.05:
        return bgr
    h, w, c = bgr.shape
    out = bgr.copy()
    rng = np.random.default_rng(seed)

    shift = max(2, int(intensity * 12))
    b, g, r = cv2.split(out)
    r_shifted = np.roll(r, -shift, axis=1)
    b_shifted = np.roll(b, shift, axis=1)
    out = cv2.merge([b_shifted, g, r_shifted])

    num_slices = rng.integers(2, 5)
    for _ in range(num_slices):
        y1 = rng.integers(0, h - 35)
        band_h = rng.integers(8, 30)
        y2 = min(h, y1 + band_h)
        x_shift = rng.integers(-int(intensity * 25), int(intensity * 25) + 1)
        if x_shift != 0:
            out[y1:y2, :, :] = np.roll(out[y1:y2, :, :], x_shift, axis=1)
            if rng.random() > 0.4:
                out[y1:y2, :, :] = np.clip(out[y1:y2, :, :] * 1.12, 0, 255).astype(np.uint8)
    return out


def _load_film_burn_frames(project, W=1920, H=1080):
    """Muat aset film burn otentik untuk efek overlay light leak saat masuk dan keluar babak."""
    from cine_paths import ASSETS_DIR
    burn_path = Path(project) / "assets" / "transitions" / "film_burn_4k_22vk.mp4"
    if not burn_path.exists():
        burn_path = ASSETS_DIR / "transitions" / "film_burn_4k_22vk.mp4"
    if not burn_path.exists():
        return [], []
    try:
        cap = cv2.VideoCapture(str(burn_path))
        raw = []
        for _ in range(70):
            ret, frame = cap.read()
            if not ret:
                break
            raw.append(frame)
        cap.release()
        if len(raw) < 55:
            return [], []
        entry_burn = [cv2.resize(raw[i], (W, H), interpolation=cv2.INTER_LINEAR) for i in range(0, min(22, len(raw)))]
        exit_burn = [cv2.resize(raw[i], (W, H), interpolation=cv2.INTER_LINEAR) for i in range(38, min(60, len(raw)))]
        return entry_burn, exit_burn
    except Exception as e:
        print(f"  [WARN] Failed to load film burn: {e}", flush=True)
        return [], []


def render_bridge(project, babak_num, tag, title, theme):
    project = Path(project)
    out_dir = project / "output" / "bridges_p404"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"bridge_p404_babak_{babak_num}_with_burn.mp4"
    avi, wav = out_dir / f"_b{babak_num}.avi", out_dir / f"_b{babak_num}.wav"
    W, H, fps, seconds = 1920, 1080, 30, 6.4
    total_frames = int(seconds * fps)
    f_tag, f_title, f_theme = _font(project, 28), _font(project, 48), _font(project, 24)
    base = _get_babak_bg(project, babak_num)
    entry_burn, exit_burn = _load_film_burn_frames(project, W, H)
    hit = _hit(project)
    rate = 48000
    buf = np.zeros(int(seconds * rate), dtype=np.float32)
    times = []
    for i, ch in enumerate(title):
        times.append((0.6 + i * 0.075, ch))
    theme_at = 0.6 + len(title) * 0.075 + 0.35
    for i, ch in enumerate(theme):
        times.append((theme_at + i * 0.045, ch))
    _strikes(buf, hit, times, rate, babak_num)
    _write_wav(wav, buf, rate)

    writer = cv2.VideoWriter(str(avi), cv2.VideoWriter_fourcc(*"MJPG"), fps, (W, H))
    for f in range(total_frames):
        t = f / fps
        im = base.copy()
        d = ImageDraw.Draw(im)

        # Tag centered
        if t >= 0.15:
            bb_tag = d.textbbox((0, 0), tag, font=f_tag)
            tw = bb_tag[2] - bb_tag[0]
            d.text(((1920 - tw) // 2, 390), tag, font=f_tag, fill=(212, 168, 67))

        # Title centered
        shown_title = title[:max(0, int((t - 0.6) / 0.075))]
        if 0.6 <= t < 0.6 + len(title) * 0.075 or int(t * 3) % 2 == 0:
            shown_title += "_"
        if shown_title:
            bb_ti = d.textbbox((0, 0), shown_title, font=f_title)
            ti_w = bb_ti[2] - bb_ti[0]
            ti_x = (1920 - ti_w) // 2
            d.text((ti_x, 455), shown_title, font=f_title, fill=(235, 230, 220))

        # Divider line
        if t >= 0.6 + len(title) * 0.075 * 0.75:
            bb_full = d.textbbox((0, 0), title, font=f_title)
            fw = bb_full[2] - bb_full[0]
            fx = (1920 - fw) // 2
            d.line([(fx - 30, 535), (fx + fw + 30, 535)], fill=(60, 55, 50), width=1)

        # Theme centered
        shown_theme = theme[:max(0, int((t - theme_at) / 0.045))]
        if shown_theme:
            bb_th = d.textbbox((0, 0), shown_theme, font=f_theme)
            th_w = bb_th[2] - bb_th[0]
            d.text(((1920 - th_w) // 2, 560), shown_theme, font=f_theme, fill=(165, 165, 175))

        bgr = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)

        # Glitch schedule
        glitch_intensity = 0.0
        if 0.15 <= t <= 0.25:
            glitch_intensity = 0.55
        elif 0.60 <= t <= 0.70:
            glitch_intensity = 0.65
        elif 2.10 <= t <= 2.22:
            glitch_intensity = 0.75
        elif abs(t - theme_at) <= 0.10:
            glitch_intensity = 0.50
        elif (seconds - 0.45) <= t <= (seconds - 0.15):
            glitch_intensity = 0.80
        elif (f % 43 == 0 or f % 71 == 0):
            glitch_intensity = 0.25

        bgr_glitched = _apply_glitch(bgr, intensity=glitch_intensity, seed=f * 7 + babak_num)

        # Overlay light (Film burn / light leak) saat Masuk Babak & Keluar Babak
        if entry_burn and f < len(entry_burn):
            burn = entry_burn[f]
            base_f = bgr_glitched.astype(np.float32) / 255.0
            burn_f = (burn.astype(np.float32) / 255.0) * 0.90
            blended = 1.0 - (1.0 - base_f) * (1.0 - burn_f)
            bgr_glitched = np.clip(blended * 255.0, 0, 255).astype(np.uint8)
        elif exit_burn and f >= (total_frames - len(exit_burn)):
            exit_idx = f - (total_frames - len(exit_burn))
            if exit_idx < len(exit_burn):
                burn = exit_burn[exit_idx]
                base_f = bgr_glitched.astype(np.float32) / 255.0
                ramp = min(1.0, (exit_idx + 1) / float(len(exit_burn)))
                burn_f = (burn.astype(np.float32) / 255.0) * ramp * 0.95
                blended = 1.0 - (1.0 - base_f) * (1.0 - burn_f)
                bgr_glitched = np.clip(blended * 255.0, 0, 255).astype(np.uint8)

        writer.write(bgr_glitched)

    writer.release()
    _mux(avi, wav, out, seconds)
    avi.unlink(missing_ok=True)
    wav.unlink(missing_ok=True)
    print(f"BRIDGE_OK babak {babak_num} {out.name} (centered + bg + glitch + overlay light in/out)", flush=True)
    return out


def closing_text(project):
    cfg = json.loads((Path(project) / "project.json").read_text(encoding="utf-8"))
    data = json.loads((Path(project) / "input" / "storyboard.json").read_text(encoding="utf-8"))
    last = data["shots"][-1]["narration"].strip()
    title = cfg.get("title", "").strip()
    return f"{title}\n\n{last}"


def _wrap(text, width=50):
    lines = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        words, cur = para.split(), ""
        for w in words:
            cur = f"{cur} {w}".strip() if len(cur) + len(w) + 1 <= width else (lines.append(cur) or w)
        lines.append(cur)
    return "\n".join(lines)


def render_closing(project):
    project = Path(project)
    out_dir = project / "output" / "outro"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "outro_conclusion_card.mp4"
    avi, wav = out_dir / "_outro.avi", out_dir / "_outro.wav"
    text = _wrap(closing_text(project), width=50)
    fps, rate = 30, 48000
    # Typing speed dinamis agar durasi outro selalu seimbang ~30-38s (tidak terlalu cepat, tidak 1.5 menit jika teks panjang)
    typing_speed = max(10.0, min(22.0, len(text) / 28.0))
    seconds = len(text) / typing_speed + CLOSING_HOLD_SEC

    # Auto-fit font size agar tidak keluar dari frame kanvas 1920x1080 (aman batas semua arah)
    fsize = 32
    spacing = 14
    im_probe = Image.new("RGB", (1920, 1080))
    d_probe = ImageDraw.Draw(im_probe)
    font = _font(project, fsize)
    box = d_probe.multiline_textbbox((0, 0), text, font=font, spacing=spacing)
    bw, bh = box[2] - box[0], box[3] - box[1]
    while (bw > 1600 or bh > 820) and fsize > 18:
        fsize -= 2
        spacing = max(10, int(fsize * 0.45))
        font = _font(project, fsize)
        box = d_probe.multiline_textbbox((0, 0), text, font=font, spacing=spacing)
        bw, bh = box[2] - box[0], box[3] - box[1]

    hit = _hit(project)
    buf = np.zeros(int(seconds * rate), dtype=np.float32)
    _strikes(buf, hit, [(i / typing_speed, c) for i, c in enumerate(text)], rate, 7)
    _write_wav(wav, buf, rate)

    bg = Image.new("RGB", (1920, 1080), (8, 8, 8))
    writer = cv2.VideoWriter(str(avi), cv2.VideoWriter_fourcc(*"MJPG"), fps, (1920, 1080))
    x_pos = (1920 - bw) // 2
    y_pos = (1080 - bh) // 2
    cached_key = None
    cached_bgr = None

    for f in range(int(seconds * fps)):
        t = f / fps
        c_idx = min(int(t * typing_speed), len(text))
        cursor = "_" if (c_idx < len(text) or int(t * 2) % 2 == 0) else ""
        key = (c_idx, cursor)
        if key != cached_key:
            im = bg.copy()
            d = ImageDraw.Draw(im)
            d.multiline_text(
                (x_pos, y_pos),
                text[:c_idx] + cursor, font=font, fill=(234, 230, 222), spacing=spacing,
            )
            cached_bgr = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)
            cached_key = key
        writer.write(cached_bgr)
    writer.release()
    _mux(avi, wav, out, seconds)
    avi.unlink(missing_ok=True)
    wav.unlink(missing_ok=True)
    print(f"CLOSING_OK {out.name} {seconds:.1f}s font {fsize}px box={bw}x{bh} pad=({x_pos},{y_pos}) @ {typing_speed:.1f}/s", flush=True)
    return out


def ensure_cards(project, force=False):
    """Build the five chapter cards and the closing. Skip any card already rendered."""
    project = Path(project)
    for n, tag, title, theme in chapter_plan(project):
        out = project / "output" / "bridges_p404" / f"bridge_p404_babak_{n}_with_burn.mp4"
        if force or not out.exists():
            render_bridge(project, n, tag, title, theme)
        else:
            print(f"BRIDGE_KEEP babak {n}", flush=True)
    closing = project / "output" / "outro" / "outro_conclusion_card.mp4"
    if force or not closing.exists():
        return render_closing(project)
    print("CLOSING_KEEP", flush=True)
    return closing


if __name__ == "__main__":
    import sys
    ensure_cards(sys.argv[1])
