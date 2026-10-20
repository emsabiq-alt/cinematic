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


# ---------------------------------------------------------------------------
# Normalisasi angka untuk TTS (perbaikan 20 Okt 2026, atas keluhan user soal
# penyebutan angka). Bukti uji Whisper atas audio Supertonic F2:
# - "seribu tujuh ratus empat puluh enam" TANPA jeda terdengar jadi "740,6"
#   (angka hancur); dengan koma kelompok ratusan terdengar benar "1.700, 46".
# - Tahun ejaan penuh "seribu sembilan ratus delapan puluh enam" terdengar
#   kacau ("986"); bentuk pasangan "sembilan belas delapan enam" terdengar
#   bersih ("19.86"). Angka pendek (<=4 kata) dan skala ribu/juta aman.
# Transformasi ini HANYA diterapkan pada string yang masuk synthesize();
# file script dan teks subtitle tetap memakai bentuk tertulis asli.
# ---------------------------------------------------------------------------
_SATUAN = ["nol", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh",
           "delapan", "sembilan", "sepuluh", "sebelas"]
_WORD2NUM = {w: i for i, w in enumerate(_SATUAN)}
_SCALES = [(10 ** 12, "triliun"), (10 ** 9, "miliar"), (10 ** 6, "juta"), (10 ** 3, "ribu")]
_NUMWORDS = set(_SATUAN) | {"seratus", "seribu", "puluh", "belas", "ratus",
                            "ribu", "juta", "miliar", "triliun", "koma"}
_MONTHS = {"januari", "februari", "maret", "april", "mei", "juni", "juli",
           "agustus", "september", "oktober", "november", "desember"}


def _below_1000_words(n):
    if n < 12:
        return _SATUAN[n]
    if n < 20:
        return _SATUAN[n - 10] + " belas"
    if n < 100:
        s = _SATUAN[n // 10] + " puluh"
        return s + (" " + _SATUAN[n % 10] if n % 10 else "")
    s = "seratus" if n < 200 else _SATUAN[n // 100] + " ratus"
    return s + (" " + _below_1000_words(n % 100) if n % 100 else "")


def _terbilang(n):
    n = int(n)
    if n < 0:
        return "minus " + _terbilang(-n)
    if n < 1000:
        return _below_1000_words(n)
    if n < 2000:
        return "seribu" + (" " + _below_1000_words(n % 1000) if n % 1000 else "")
    for skala, nama in _SCALES:
        if n >= skala:
            head, rest = n // skala, n % skala
            s = _terbilang(head) + " " + nama
            return s + (" " + _terbilang(rest) if rest else "")
    return str(n)


def _below_1000_value(words):
    val = 0
    i = 0
    while i < len(words):
        w = words[i]
        if w == "seratus":
            val += 100
            i += 1
            continue
        if w not in _WORD2NUM:
            return None
        v = _WORD2NUM[w]
        nxt = words[i + 1] if i + 1 < len(words) else None
        if nxt == "ratus":
            val += v * 100
            i += 2
        elif nxt == "puluh":
            val += v * 10
            i += 2
            if i < len(words) and words[i] in _WORD2NUM and _WORD2NUM[words[i]] < 10:
                val += _WORD2NUM[words[i]]
                i += 1
        elif nxt == "belas":
            val += 10 + v
            i += 2
        else:
            val += v
            i += 1
    return val


def _words_to_value(words):
    if not words:
        return None
    total = 0
    seg = []
    scale_map = {nama: skala for skala, nama in _SCALES}
    for w in words:
        if w == "seribu":
            total += 1000
            seg = []
        elif w in scale_map:
            v = _below_1000_value(seg) if seg else 1
            if v is None:
                return None
            total += v * scale_map[w]
            seg = []
        else:
            seg.append(w)
    if seg:
        v = _below_1000_value(seg)
        if v is None:
            return None
        total += v
    return total


def _pair_year_words(val):
    hi, lo = val // 100, val % 100
    s = _terbilang(hi)
    if lo == 0:
        return s
    if lo < 10:
        return s + " nol " + _SATUAN[lo]
    s += " " + _SATUAN[lo // 10]
    s += " " + (_SATUAN[lo % 10] if lo % 10 else "nol")
    return s


def _digit_token_to_words(tok):
    pct = tok.endswith("%")
    if pct:
        tok = tok[:-1]
    m = re.fullmatch(r"(\d{1,3}(?:\.\d{3})+|\d+),(\d{1,2})", tok)
    if m:
        whole = m.group(1).replace(".", "")
        dec = " ".join(_SATUAN[int(c)] for c in m.group(2))
        s = _terbilang(int(whole)) + " koma " + dec
    elif re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", tok):
        s = _terbilang(int(re.sub(r"[.,]", "", tok)))
    elif re.fullmatch(r"\d+", tok):
        s = _terbilang(int(tok))
    else:
        return None
    return s + (" persen" if pct else "")


def normalize_numbers_for_tts(text):
    """Bentuk teks yang diucapkan Supertonic paling jelas (lihat catatan di atas).

    1) Digit apa pun -> kata terbilang (+ "persen" untuk %).
    2) Tahun 19xx ejaan penuh -> bentuk pasangan bila konteks tanggal/tahun.
    3) Rantai angka ejaan >=5 kata -> koma sesudah kelompok ratusan.
    """
    def _rep(m):
        w = _digit_token_to_words(m.group(0))
        return w if w is not None else m.group(0)

    text = re.sub(r"\d[\d.,]*%?", _rep, text)

    tokens = text.split(" ")
    cores = [re.sub(r"[^a-z]", "", t.lower()) for t in tokens]
    runs = []
    i = 0
    while i < len(tokens):
        if cores[i] in _NUMWORDS:
            j = i
            while j + 1 < len(tokens) and cores[j + 1] in _NUMWORDS:
                j += 1
            runs.append((i, j))
            i = j + 1
        else:
            i += 1

    out = list(tokens)
    for a, b in runs:
        words = cores[a:b + 1]
        if "koma" in words:
            continue
        val = _words_to_value(words)
        if val is not None and 1900 <= val <= 1999:
            prev = [c for c in cores[max(0, a - 3):a] if c]
            if any(p in _MONTHS or p in ("tahun", "tanggal") for p in prev):
                new = _pair_year_words(val).split(" ")
                tail = tokens[b][len(cores[b]):] if cores[b] else ""
                out[a:b + 1] = new[:-1] + [new[-1] + tail]
                continue
        if len(words) >= 5 and "ratus" in words:
            k = words.index("ratus")
            after = words[k + 1:]
            if len(after) >= 2 and after[0] not in ("ribu", "juta", "miliar", "triliun"):
                out[a + k] = out[a + k] + ","
    return " ".join(out)


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


def _split_tts_clauses(text):
    """Pecah teks menjadi klausa untuk sintesis per-klausa.

    Satu panggilan synthesize untuk satu shot utuh terbukti membuat angka
    bocor/berulang antar-angka dalam kalimat yang sama (uji 2026-10-20:
    "meletus tahun dua ribu dua dan kembali meletus tahun dua ribu dua
    puluh satu" terdengar "2021 ... 2021"). Sintesis per-klausa
    mengisolasi tiap angka ke panggilannya sendiri.
    """
    parts = re.split(r"(?<=[,;:])\s+|(?<=[.!?])\s+", text)
    parts = [p.strip() for p in parts if p.strip()]
    conj = ("dan", "yang", "lalu", "tetapi", "namun", "hingga", "atau")
    out = []
    for p in parts:
        while len(p.split()) > 13:
            words = p.split()
            mid = len(words) // 2
            cut = -1
            for d in range(0, 7):
                for j in (mid - d, mid + d):
                    if 0 < j < len(words) and words[j].lower() in conj:
                        cut = j
                        break
                if cut > 0:
                    break
            if cut <= 0:
                break
            out.append(" ".join(words[:cut]).strip())
            p = " ".join(words[cut:]).strip()
        out.append(p)
    merged = []
    for p in out:
        if merged and len(p.split()) < 3:
            merged[-1] = merged[-1] + " " + p
        else:
            merged.append(p)
    return merged


def synthesize_speech(tts, style, text):
    """Sintesis satu shot: normalisasi angka, lalu per-klausa, digabung
    dengan jeda 90 ms antar-klausa. Mengembalikan (wav_data, sr) dengan
    konvensi yang sama seperti tts.synthesize()."""
    import numpy as np

    text = normalize_numbers_for_tts(text)
    chunks = _split_tts_clauses(text)
    if len(chunks) <= 1:
        return tts.synthesize(text, style, lang="id")
    pieces = []
    sr = 44100
    for c in chunks:
        wav_data, sr = tts.synthesize(c, style, lang="id")
        pieces.append(np.asarray(wav_data[0], dtype=np.float32))
    gap = np.zeros(int(0.09 * sr), dtype=np.float32)
    joined = []
    for i, p in enumerate(pieces):
        if i:
            joined.append(gap)
        joined.append(p)
    return [np.concatenate(joined)], sr


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
            # Angka dinormalisasi + sintesis per-klausa khusus untuk
            # pengucapan; teks asli untuk subtitle.
            wav_data, sr = synthesize_speech(tts, style, text)
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
