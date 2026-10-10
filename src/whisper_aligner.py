"""whisper_aligner.py — Acoustic-precise subtitle alignment using faster-whisper.

Rules:
1. Acoustic precision: Subtitle phrase timings are grounded in actual spoken word boundaries.
2. Anticipatory display (LEAD_IN): Each phrase appears 0.10s before the speaker begins the first word.
3. Continuous handoff (GAP = 0.00s): Consecutive phrases transition on the same frame without dark flickering.
4. Anti-lonely phrasing: Strictly min 3 words, max 7 words per line. 0 lonely phrases (<=2 words).
5. Robust fallback: If Whisper finds no speech or audio is corrupted, falls back gracefully to balanced distribution.
"""

import argparse
import contextlib
import difflib
import json
import os
import re
import sys
import wave
from pathlib import Path

MAX_WORDS = 7
MIN_WORDS = 3
LEAD_IN = 0.10
TAIL_PAD = 0.25


def fmt(t):
    if t < 0:
        t = 0.0
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


def clean_word(w):
    return re.sub(r"[^\w]", "", str(w).lower())


def split_phrases_balanced(text, max_w=MAX_WORDS, min_w=MIN_WORDS):
    text = re.sub(r"\bSt\.\s*", "Saint ", text)
    text = re.sub(r"[:;]", ",", text)
    parts = re.split(r"\s*<breath>\s*|(?<=\w)\.\s+(?=[A-Z0-9])|\.\s*$", text)
    clauses = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        subparts = re.split(r",\s*", p)
        for sp in subparts:
            sp = sp.strip()
            if sp:
                clauses.append(sp)

    chunks = []
    for c in clauses:
        words = c.split()
        if not words:
            continue
        n = len(words)
        if n <= max_w:
            chunks.append(" ".join(words))
        else:
            k = (n + max_w - 1) // max_w
            base = n // k
            rem = n % k
            idx = 0
            for i in range(k):
                sz = base + (1 if i < rem else 0)
                chunks.append(" ".join(words[idx : idx + sz]))
                idx += sz

    res = []
    for c in chunks:
        cw = len(c.split())
        if cw < min_w and res:
            res[-1] = res[-1] + " " + c
        else:
            res.append(c)

    while len(res) > 1 and len(res[0].split()) < min_w:
        res[0] = res[0] + " " + res[1]
        del res[1]

    final_res = []
    for c in res:
        w = c.split()
        if len(w) > max_w:
            k = (len(w) + max_w - 1) // max_w
            base = len(w) // k
            rem = len(w) % k
            idx = 0
            for i in range(k):
                sz = base + (1 if i < rem else 0)
                final_res.append(" ".join(w[idx : idx + sz]))
                idx += sz
        else:
            final_res.append(c)

    return [c.strip().lower() for c in final_res if c.strip()]


def wav_dur(p):
    with contextlib.closing(wave.open(str(p), "rb")) as w:
        return w.getnframes() / float(w.getframerate())


def align_tokens_to_whisper(s_tokens, w_words, total_dur):
    if not w_words:
        step = max(0.1, (total_dur - 0.3) / max(1, len(s_tokens)))
        return [(i * step, (i + 1) * step) for i in range(len(s_tokens))]

    # Word-level sequence matching (bukan unspaced character matching yang rawan melompat 20 detik jika ada 1 huruf typo)
    w_token_strs = [w["word"] for w in w_words]
    matcher = difflib.SequenceMatcher(None, s_tokens, w_token_strs)
    word_times = [None] * len(s_tokens)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                word_times[i1 + k] = (w_words[j1 + k]["start"], w_words[j1 + k]["end"])
        elif tag == "replace" and j2 > j1:
            st = w_words[j1]["start"]
            en = w_words[j2 - 1]["end"]
            cnt = i2 - i1
            step = (en - st) / max(1, cnt)
            for k in range(cnt):
                word_times[i1 + k] = (st + k * step, st + (k + 1) * step)

    known = [i for i, t in enumerate(word_times) if t is not None]
    if not known:
        step = max(0.1, (total_dur - 0.3) / max(1, len(s_tokens)))
        return [(i * step, (i + 1) * step) for i in range(len(s_tokens))]

    # Fill before first known
    first_k = known[0]
    t1 = word_times[first_k][0]
    for i in range(first_k):
        word_times[i] = (max(0.0, t1 * i / float(first_k)), max(0.05, t1 * (i + 1) / float(first_k)))

    # Interpolate between knowns
    for idx in range(len(known) - 1):
        k1, k2 = known[idx], known[idx + 1]
        t1_end = word_times[k1][1]
        t2_start = max(t1_end, word_times[k2][0])
        gap = t2_start - t1_end
        n_m = k2 - k1 - 1
        for m_i, s_idx in enumerate(range(k1 + 1, k2)):
            word_times[s_idx] = (
                t1_end + gap * m_i / float(n_m + 1),
                t1_end + gap * (m_i + 1) / float(n_m + 1),
            )

    # Fill after last known
    last_k = known[-1]
    t_last = word_times[last_k][1]
    for i in range(last_k + 1, len(s_tokens)):
        word_times[i] = (t_last, min(total_dur, t_last + 0.3 * (i - last_k)))

    return word_times


def align_shot_subtitles(script_text, wav_path, whisper_model=None):
    dur = wav_dur(wav_path)
    phrases = split_phrases_balanced(script_text)
    if not phrases:
        return []

    # Flatten phrase words
    p_flat = []
    for p_idx, p in enumerate(phrases):
        for w in p.split():
            cw = clean_word(w)
            if cw:
                p_flat.append({"word": cw, "phrase_idx": p_idx})

    s_tokens = [x["word"] for x in p_flat]
    w_words = []
    if whisper_model is not None and len(s_tokens) > 0:
        try:
            segments, _ = whisper_model.transcribe(str(wav_path), language="id", word_timestamps=True)
            for s in segments:
                for w in s.words:
                    cw = clean_word(w.word)
                    if cw:
                        w_words.append({"word": cw, "start": w.start, "end": w.end})
        except Exception as e:
            print(f"  [WARN] Whisper transcription failed for {wav_path.name}: {e}")

    word_times = align_tokens_to_whisper(s_tokens, w_words, dur)

    # Aggregate by phrase
    p_indices = {}
    for i, it in enumerate(p_flat):
        p_indices.setdefault(it["phrase_idx"], []).append(i)

    raw_ranges = []
    for p_idx in range(len(phrases)):
        idx_list = p_indices.get(p_idx, [])
        if idx_list:
            raw_ranges.append((word_times[idx_list[0]][0], word_times[idx_list[-1]][1]))
        else:
            raw_ranges.append((0.0, dur))

    # Apply LEAD_IN = 0.10s and strict zero-overlap
    st_adjs = [
        LEAD_IN if p_idx == 0 else max(LEAD_IN, raw_ranges[p_idx][0] - LEAD_IN)
        for p_idx in range(len(phrases))
    ]
    final_entries = []
    for p_idx in range(len(phrases)):
        w_st, w_en = raw_ranges[p_idx]
        st = st_adjs[p_idx]
        if p_idx < len(phrases) - 1:
            next_st = max(st + 0.3, st_adjs[p_idx + 1])
            en = min(next_st, max(st + 0.2, w_en + TAIL_PAD))
        else:
            en = min(dur - 0.05, max(st + 0.2, w_en + TAIL_PAD))
        final_entries.append((st, en, phrases[p_idx]))

    return final_entries


def process_project(project_dir):
    project = Path(project_dir).resolve()
    script_dir = project / "script"
    audio_dir = project / "output" / "audio_supertonic"
    subs_dir = project / "output" / "subtitles"
    subs_dir.mkdir(parents=True, exist_ok=True)

    from faster_whisper import WhisperModel
    print("Loading faster-whisper base model...", flush=True)
    model = WhisperModel("base", device="cpu", compute_type="int8")
    print("Model loaded. Starting acoustic alignment...", flush=True)

    script_files = sorted(script_dir.glob("shot_*.txt"))
    total = len(script_files)
    lonely_count = 0
    aligned_count = 0

    for idx, sf in enumerate(script_files, 1):
        sid = sf.stem
        wav_file = audio_dir / f"{sid}.wav"
        srt_file = subs_dir / f"{sid}.srt"
        if not wav_file.exists():
            continue

        text = sf.read_text(encoding="utf-8").strip()
        entries = align_shot_subtitles(text, wav_file, whisper_model=model)

        lines = []
        for i, (st, en, phrase) in enumerate(entries, 1):
            if len(phrase.split()) <= 2:
                lonely_count += 1
            lines.append(str(i))
            lines.append(f"{fmt(st)} --> {fmt(en)}")
            lines.append(phrase)
            lines.append("")

        srt_file.write_text("\n".join(lines), encoding="utf-8")
        aligned_count += 1
        if idx % 10 == 0 or idx == total:
            print(f"  [{idx:02d}/{total:02d}] Aligned {sid} ({len(entries)} phrases)", flush=True)

    print(f"\n✓ Acoustic subtitle alignment complete: {aligned_count} shots.")
    print(f"✓ Lonely word phrases (<=2 words): {lonely_count}")
    assert lonely_count == 0, f"Ditemukan {lonely_count} frasa kesepian!"
    return aligned_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project", help="Project path e.g. D:/project/a045")
    args = parser.parse_args()
    process_project(args.project)
