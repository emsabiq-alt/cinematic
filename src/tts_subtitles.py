"""tts_subtitles.py — Automated TTS (Supertonic) and anti-lonely subtitle pipeline.

Standard:
- Supertonic TTS: Indonesian male/female voices (default M2).
- Subtitles: 1-line balanced phrasing, min 3 words (anti-lonely), max 7 words.
- Timing: LEAD_IN = 0.10s, GAP = 0.00s (continuous handoff).
"""
import contextlib
import json
import os
import re
import sys
import wave
from pathlib import Path
import soundfile as sf

MAX_WORDS = 7
MIN_WORDS = 3
GAP = 0.00
LEAD_IN = 0.10
BREATH_EXTRA = 0.20


def fmt(t):
    if t < 0:
        t = 0
    h = int(t // 3600)
    t -= h * 3600
    m = int(t // 60)
    t -= m * 60
    s = int(t)
    ms = int(round((t - s) * 1000))
    if ms >= 1000:
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _smart_chunk_words(words, max_w=MAX_WORDS, min_w=MIN_WORDS):
    n = len(words)
    if n <= max_w:
        return [" ".join(words)]
    k = (n + max_w - 1) // max_w
    while k > 1 and (n // k) < min_w:
        k -= 1
    base = n // k
    rem = n % k
    chunks = []
    idx = 0
    for i in range(k):
        size = base + (1 if i < rem else 0)
        chunks.append(" ".join(words[idx : idx + size]))
        idx += size
    return chunks


def split_phrases_balanced(text, max_w=MAX_WORDS, min_w=MIN_WORDS):
    text = re.sub(r"\bSt\.\s*", "Saint ", text)
    text = re.sub(r"[:;]", ",", text)
    parts = re.split(r"\s*<breath>\s*|(?<=\w)\.\s+(?=[A-Z0-9])|\.\s*$", text)
    chunks = []

    for part in parts:
        part = part.strip()
        if not part:
            continue
        clauses = [c.strip() for c in part.split(",") if c.strip()]
        for c in clauses:
            w = c.split()
            if w:
                chunks.extend(_smart_chunk_words(w, max_w=max_w, min_w=min_w))

    res = []
    for c in chunks:
        cw = len(c.split())
        if cw < min_w and res:
            combined = res[-1].split() + c.split()
            res[-1:] = _smart_chunk_words(combined, max_w=max_w, min_w=min_w)
        else:
            res.append(c)

    while len(res) > 1 and len(res[0].split()) < min_w:
        combined = res[0].split() + res[1].split()
        res[:2] = _smart_chunk_words(combined, max_w=max_w, min_w=min_w)

    return [c.strip().lower() for c in res if c.strip()]


def wav_dur(p):
    with contextlib.closing(wave.open(str(p), "rb")) as w:
        return w.getnframes() / float(w.getframerate())


def generate_subtitles_from_audio(wav_path, text, srt_path):
    dur = wav_dur(wav_path)
    phrases = split_phrases_balanced(text)
    if not phrases:
        phrases = [text.strip().lower()]

    weights = [len(p.split()) for p in phrases]
    tot_weight = sum(weights) or 1

    net_dur = max(dur - LEAD_IN - BREATH_EXTRA, 0.5)

    entries = []
    curr = LEAD_IN

    for idx, (phrase, w) in enumerate(zip(phrases, weights)):
        is_last = (idx == len(phrases) - 1)
        target_len = (w / tot_weight) * net_dur
        target_len = max(target_len, 0.8)

        end_t = dur - 0.05 if is_last else curr + target_len
        if end_t <= curr:
            end_t = curr + 0.5

        entries.append((curr, end_t, phrase))
        curr = end_t + GAP

    # Write SRT
    lines = []
    for i, (st, en, txt) in enumerate(entries, 1):
        lines.append(str(i))
        lines.append(f"{fmt(st)} --> {fmt(en)}")
        lines.append(txt)
        lines.append("")

    srt_path = Path(srt_path)
    srt_path.parent.mkdir(parents=True, exist_ok=True)
    srt_path.write_text("\n".join(lines), encoding="utf-8")
    return entries


def extract_shot_scripts(project):
    project = Path(project).resolve()
    story_path = project / "input" / "storyboard.json"
    script_dir = project / "script"
    script_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(story_path.read_text(encoding="utf-8"))
    files = []
    for s in data["shots"]:
        sid = s["id"]
        txt = s.get("narration", "").strip()
        # Normalisasi otomatis: em-dash / en-dash menjadi koma agar dibaca jeda alami & lolos QA dashboard
        txt = re.sub(r"[\u2013\u2014]", ", ", txt)
        txt = re.sub(r"\s+", " ", txt).strip()
        f = script_dir / f"{sid}.txt"
        f.write_text(txt + "\n", encoding="utf-8")
        files.append(f)
    return files


def get_tts_instance():
    import supertonic
    return supertonic.TTS()


def parse_voice_code(voice_str):
    if not voice_str:
        return "M2"
    m = re.search(r"\b([MF]\d)\b", str(voice_str))
    return m.group(1) if m else "M2"


def run_tts_subtitles(project, voice=None):
    project = Path(project).resolve()
    cfg_path = project / "project.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}

    voice_code = parse_voice_code(voice or cfg.get("voice"))
    audio_dir = project / "output" / "audio_supertonic"
    subs_dir = project / "output" / "subtitles"
    audio_dir.mkdir(parents=True, exist_ok=True)
    subs_dir.mkdir(parents=True, exist_ok=True)

    script_files = extract_shot_scripts(project)

    tts = get_tts_instance()
    style = tts.get_voice_style(voice_code)

    wav_count, srt_count = 0, 0
    total_dur = 0.0

    for idx, f in enumerate(script_files, 1):
        sid = f.stem
        out_wav = audio_dir / f"{sid}.wav"
        out_srt = subs_dir / f"{sid}.srt"
        text = f.read_text(encoding="utf-8").strip()

        # Generate audio if missing or too small
        if not out_wav.exists() or out_wav.stat().st_size < 5000:
            wav_data, sr = tts.synthesize(text, style, lang="id")
            sf.write(str(out_wav), wav_data[0], 44100)
            print(f"TTS_OK {sid} -> {out_wav.name}", flush=True)

        d = wav_dur(out_wav)
        total_dur += d
        wav_count += 1

        # Generate subtitle fallback
        generate_subtitles_from_audio(out_wav, text, out_srt)
        srt_count += 1

    # Apply acoustic Whisper alignment across all generated WAV files
    try:
        import subprocess
        base_dir = Path(__file__).resolve().parents[1]
        align_script = base_dir / "src" / "whisper_aligner.py"
        if align_script.exists():
            cmd = ["uv", "run", "--with", "faster-whisper", "--with", "av<14", "python", str(align_script), str(project)]
            res = subprocess.run(cmd, cwd=str(base_dir), capture_output=True, text=True)
            if res.returncode == 0:
                print("✓ Applied acoustic Whisper subtitle alignment across project!", flush=True)
            else:
                print(f"  [WARN] Whisper aligner stderr: {res.stderr[:200]}", flush=True)
    except Exception as e:
        print(f"  [WARN] Failed to trigger whisper aligner: {e}", flush=True)

    return {
        "wav_count": wav_count,
        "srt_count": srt_count,
        "total_duration": total_dur,
        "voice": voice_code,
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?", help="Project directory (or CINEMATIC_PROJECT_DIR)")
    ap.add_argument("--voice")
    args = ap.parse_args()
    _proj = args.project or os.environ.get("CINEMATIC_PROJECT_DIR")
    if not _proj:
        ap.error("project directory required (arg or CINEMATIC_PROJECT_DIR)")
    r = run_tts_subtitles(_proj, args.voice)
    print(f"TTS_SUBTITLES_DONE wav={r['wav_count']} srt={r['srt_count']} dur={r['total_duration']:.1f}s", flush=True)
