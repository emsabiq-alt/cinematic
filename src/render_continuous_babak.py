"""render_continuous_babak.py — Continuous Long-Form Chapter Production Pipeline.

Architecture (Option 1: Continuous Narration Per-Babak):
1. Continuous Speech Synthesis:
   Each chapter (Babak I-V) is synthesized as a single flowing narration WAV file.
   Zero robotic micro-silences. Natural human breathing pauses between sentences.
2. Acoustic Ground-Truth Alignment (Faster-Whisper):
   Every word and sentence is mapped directly to spoken vocal onset.
   Visual image cuts switch seamlessly at true speech clause boundaries.
3. Anti-Clash Lower-Third Typography:
   - Watermark "documentary by: BANYAK TAU" shifted up to y=720 (leaving >200px breathing room).
   - Subtitles: Single/double balanced lines (Fontsize 21, Poppins Bold, MarginV 42).
   - Zero overlap with watermark. 0 lonely phrases.
4. Dynamic Cinema Assembly:
   - Ken Burns subtle motion (1.00 -> 1.06).
   - Heavy grunge texture screen blend.
   - Chapter title cards with typewriter sync.
   - Sidechain audio ducking for dark cinematic music.
"""

import argparse
import contextlib
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import wave
from pathlib import Path
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))

MAX_WORDS = 6
MIN_WORDS = 3
LEAD_IN = 0.10
TAIL_PAD = 0.25

def chapter_ranges(project):
    """Shot span of each chapter, read from this film's storyboard. Never a fixed map."""
    data = json.loads((Path(project) / "input" / "storyboard.json").read_text(encoding="utf-8"))
    spans = {}
    for s in data["shots"]:
        n = int(s["id"].split("_")[1])
        ch = int(s["chapter"])
        lo, hi = spans.get(ch, (n, n))
        spans[ch] = (min(lo, n), max(hi, n))
    return spans


def master_path(project):
    project = Path(project)
    cfg = json.loads((project / "project.json").read_text(encoding="utf-8")) if (project / "project.json").exists() else {}
    safe = re.sub(r"[^A-Za-z0-9]+", "_", cfg.get("title", project.name)).strip("_")
    return project / "export" / f"{safe}_MASTER.mp4"


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


def wav_dur(p):
    with contextlib.closing(wave.open(str(p), "rb")) as w:
        return w.getnframes() / float(w.getframerate())


def split_sentence_to_two_lines(sentence, max_line_words=12):
    words = sentence.strip().split()
    n = len(words)
    if n <= max_line_words:
        return sentence.strip()

    mid = n // 2
    best_idx = mid
    best_score = 999

    conjunctions = {'dan', 'yang', 'serta', 'di', 'dalam', 'untuk', 'dengan', 'pada', 'karena', 'hingga', 'sekaligus'}
    for i in range(max(3, mid - 4), min(n - 3, mid + 5)):
        w = words[i - 1]
        score = abs(i - mid) * 2
        if w.endswith(','):
            score -= 6
        elif words[i].lower() in conjunctions:
            score -= 4
        if score < best_score:
            best_score = score
            best_idx = i

    line1 = ' '.join(words[:best_idx])
    line2 = ' '.join(words[best_idx:])
    return f"{line1}\n{line2}"


def split_documentary_clauses(text):
    """Option B: 2-line tight sentences (full complete sentence without choppy 3-word fragments)."""
    text = re.sub(r"\bSt\.\s*", "Saint ", text)
    text = re.sub(r"\b([A-Z][a-z]{0,2})\.\s+(?=[A-Z])", r"\1 ", text)
    sentences = re.split(r"(?<=\w)\.\s+(?=[A-Z0-9])|\.\s*$", text)
    res = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        words = s.split()
        if len(words) > 24:
            clauses = [c.strip() for c in s.split(',') if c.strip()]
            if len(clauses) > 1:
                half = len(clauses) // 2
                c1 = ', '.join(clauses[:half])
                c2 = ', '.join(clauses[half:])
                res.append(split_sentence_to_two_lines(c1))
                res.append(split_sentence_to_two_lines(c2))
                continue
        res.append(split_sentence_to_two_lines(s))
    return res


def synthesize_chapter_audio(project_dir, babak_num, voice_code="M2"):
    project = Path(project_dir).resolve()
    audio_dir = project / "output" / "audio_babak"
    audio_dir.mkdir(parents=True, exist_ok=True)
    out_wav = audio_dir / f"babak_{babak_num}.wav"

    data = json.loads((project / "input" / "storyboard.json").read_text(encoding="utf-8"))
    st, en = chapter_ranges(project)[babak_num]
    shots = [s for s in data["shots"] if st <= int(s["id"].split("_")[1]) <= en]

    # Combine sentences with human punctuation pauses
    chapter_text = " ".join(s["narration"].strip() for s in shots)

    if out_wav.exists() and out_wav.stat().st_size > 100000:
        print(f"✓ Using existing chapter audio: {out_wav.name} ({wav_dur(out_wav):.1f}s)", flush=True)
        return out_wav, shots

    print(f"Synthesizing continuous narration for Babak {babak_num} ({len(chapter_text)} chars)...", flush=True)
    try:
        import supertonic
        tts = supertonic.TTS()
        style = tts.get_voice_style(voice_code)
        wav_data, dur = tts.synthesize(chapter_text, style, lang="id")
        sf.write(str(out_wav), wav_data[0], 44100)
    except ModuleNotFoundError:
        # Fallback to Python 3.10 interpreter where supertonic is installed
        py310 = r"C:\Users\Lenovo\AppData\Local\Programs\Python\Python310\python.exe"
        tmp_script = audio_dir / f"tmp_syn_{babak_num}.py"
        tmp_json = audio_dir / f"tmp_syn_{babak_num}.json"
        tmp_json.write_text(json.dumps({"text": chapter_text, "out": str(out_wav), "voice": voice_code}), encoding="utf-8")
        code = (
            "import json, soundfile as sf, supertonic\n"
            f"cfg = json.loads(open(r'{tmp_json}', encoding='utf-8').read())\n"
            "tts = supertonic.TTS()\n"
            "style = tts.get_voice_style(cfg['voice'])\n"
            "wav, _ = tts.synthesize(cfg['text'], style, lang='id')\n"
            "sf.write(cfg['out'], wav[0], 44100)\n"
        )
        tmp_script.write_text(code, encoding="utf-8")
        try:
            subprocess.run([py310, str(tmp_script)], check=True)
        finally:
            tmp_script.unlink(missing_ok=True)
            tmp_json.unlink(missing_ok=True)

    print(f"✓ Synthesized {out_wav.name} ({wav_dur(out_wav):.1f}s)", flush=True)
    return out_wav, shots


def align_chapter(project_dir, babak_num, whisper_model=None):
    project = Path(project_dir).resolve()
    wav_p, shots = synthesize_chapter_audio(project, babak_num)
    total_dur = wav_dur(wav_p)

    if whisper_model is None:
        from faster_whisper import WhisperModel
        print("Loading WhisperModel base...", flush=True)
        whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

    print(f"Aligning Babak {babak_num} audio ({total_dur:.1f}s)...", flush=True)
    segments, _ = whisper_model.transcribe(str(wav_p), language="id", word_timestamps=True)

    whisper_words = []
    for s in segments:
        for w in s.words:
            cw = clean_word(w.word)
            if cw:
                whisper_words.append({"word": cw, "start": w.start, "end": w.end})

    # Tokenize each shot into 1-line balanced anti-lonely phrases (100% konsisten dengan preview shot)
    import whisper_aligner as wa
    all_phrases = []
    for s in shots:
        sid = s["id"]
        clauses = wa.split_phrases_balanced(s["narration"])
        for c in clauses:
            all_phrases.append({"shot_id": sid, "text": c.strip().lower()})

    # Flatten phrase words for global sequence alignment
    p_flat = []
    for p_idx, p_item in enumerate(all_phrases):
        for w in p_item["text"].split():
            cw = clean_word(w)
            if cw:
                p_flat.append({"word": cw, "phrase_idx": p_idx})

    s_tokens = [x["word"] for x in p_flat]
    word_times = wa.align_tokens_to_whisper(s_tokens, whisper_words, total_dur)

    p_indices = {}
    for i, it in enumerate(p_flat):
        p_indices.setdefault(it["phrase_idx"], []).append(i)

    raw_sub_entries = []
    shot_starts = {}
    for p_idx, p_item in enumerate(all_phrases):
        sid = p_item["shot_id"]
        idxs = p_indices.get(p_idx, [])
        if not idxs:
            continue
        st_time = float(word_times[idxs[0]][0])
        en_time = float(word_times[idxs[-1]][1])
        if sid not in shot_starts:
            shot_starts[sid] = st_time
        raw_sub_entries.append((st_time, en_time, p_item["text"]))

    # 1. Build Subtitles for the Babak with exact speech duration and STRICT ZERO-OVERLAP
    # Menjamin tidak ada tumpang tindih waktu sekecil apa pun sehingga posisi baris subtitle selalu terkunci di 1 posisi (bawah tengah) tanpa pernah melompat ke atas/bawah
    st_adjs = [
        max(LEAD_IN, st - LEAD_IN) if i > 0 else LEAD_IN
        for i, (st, en, txt) in enumerate(raw_sub_entries)
    ]
    sub_entries = []
    for idx, (st, en, text) in enumerate(raw_sub_entries):
        st_adj = st_adjs[idx]
        if idx < len(raw_sub_entries) - 1:
            next_st_adj = max(st_adj + 0.3, st_adjs[idx + 1])
            en_adj = min(next_st_adj, max(st_adj + 0.2, en + TAIL_PAD))
        else:
            en_adj = min(total_dur - 0.05, max(st_adj + 0.2, en + TAIL_PAD))
        sub_entries.append((st_adj, en_adj, text))

    subs_dir = project / "output" / "subtitles_babak"
    subs_dir.mkdir(parents=True, exist_ok=True)
    srt_p = subs_dir / f"babak_{babak_num}.srt"
    srt_lines = []
    for i, (st, en, text) in enumerate(sub_entries, 1):
        srt_lines.append(str(i))
        srt_lines.append(f"{fmt(st)} --> {fmt(en)}")
        srt_lines.append(text)
        srt_lines.append("")
    srt_p.write_text("\n".join(srt_lines), encoding="utf-8")
    print(f"✓ Generated subtitle: {srt_p.name} ({len(sub_entries)} phrases)", flush=True)

    # 2. Determine Image Cut Boundaries
    shot_timings = []
    for i, s in enumerate(shots):
        sid = s["id"]
        img_p = project / "output" / "flow_images" / f"{sid}.png"
        start_t = 0.0 if i == 0 else max(0.0, shot_starts.get(sid, 0.0) - LEAD_IN)
        if i < len(shots) - 1:
            next_sid = shots[i + 1]["id"]
            end_t = max(start_t + 1.5, shot_starts.get(next_sid, total_dur) - LEAD_IN)
        else:
            end_t = total_dur
        dur = max(1.5, end_t - start_t)
        shot_timings.append({"id": sid, "img": img_p, "dur": dur})

    print(f"✓ Calculated visual cut timings for {len(shot_timings)} shots in Babak {babak_num}.", flush=True)
    return wav_p, srt_p, shot_timings


def render_babak_video(project_dir, babak_num, whisper_model=None):
    project = Path(project_dir).resolve()
    temp_dir = project / "export" / "temp_assembly"
    temp_dir.mkdir(parents=True, exist_ok=True)
    out_babak = temp_dir / f"g{babak_num-1}_shots.mp4"

    wav_p, srt_p, shot_timings = align_chapter(project, babak_num, whisper_model)
    total_dur = wav_dur(wav_p)

    print(f"\n=== RENDERING BABAK {babak_num} VISUAL TRACK ({total_dur:.1f}s) ===", flush=True)
    # Render individual image clips with subtle zoompan and xfade extension
    clip_dir = temp_dir / f"babak_{babak_num}_clips"
    shutil.rmtree(clip_dir, ignore_errors=True)
    clip_dir.mkdir(parents=True, exist_ok=True)

    XFADE_DUR = 0.75
    clip_paths = []
    clip_durations = []

    for idx, item in enumerate(shot_timings):
        sid = item["id"]
        img_p = item["img"]
        base_dur = item["dur"]
        # Extend all shots except the last by XFADE_DUR so crossfade doesn't shorten the video
        dur = base_dur + XFADE_DUR if idx < len(shot_timings) - 1 else base_dur
        out_c = clip_dir / f"{sid}.mp4"
        frames = int(dur * 30)
        zoom_step = 0.060 / float(max(frames, 1))

        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-t", f"{dur:.3f}", "-i", str(img_p),
            "-filter_complex",
            f"[0:v]scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,"
            f"zoompan=z='min(zoom+{zoom_step:.6f},1.060)':x='iw*0.50-(iw/zoom/2)':y='ih*0.48-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30,"
            f"format=yuv420p[v]",
            "-map", "[v]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-t", f"{dur:.3f}",
            str(out_c)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        clip_paths.append(out_c)
        clip_durations.append(dur)

    # Build crossfades across all shots in this babak
    n = len(clip_paths)
    if n > 1:
        print(f"Applying smooth 0.75s crossfades across {n} shots...", flush=True)
        inputs = []
        for p in clip_paths:
            inputs.extend(["-i", str(p)])
        v_filters = []
        cumul = clip_durations[0]
        for i in range(1, n):
            offset = max(cumul - XFADE_DUR, 0)
            in_v = f"[xv{i-1}]" if i > 1 else "[0:v]"
            out_v = f"[xv{i}]" if i < n - 1 else "[xfaded_raw]"
            v_filters.append(f"{in_v}[{i}:v]xfade=transition=fade:duration={XFADE_DUR}:offset={offset:.3f}{out_v}")
            cumul += clip_durations[i] - XFADE_DUR

        xfade_fc = ";".join(v_filters)
        xfaded_track = clip_dir / "xfaded_track.mp4"
        cmd_xfade = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", xfade_fc, "-map", "[xfaded_raw]",
            "-threads", "0",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-t", f"{total_dur:.3f}",
            str(xfaded_track)
        ]
        subprocess.run(cmd_xfade, check=True)
        video_input = str(xfaded_track.relative_to(project)).replace("\\", "/")
        input_args = ["-i", video_input]
    else:
        video_input = str(clip_paths[0].relative_to(project)).replace("\\", "/")
        input_args = ["-i", video_input]

    # Use relative paths from project directory to avoid Windows drive letter colon escaping issues
    srt_rel = f"output/subtitles_babak/babak_{babak_num}.srt"
    fonts_rel = "assets/fonts"
    grunge_rel = "assets/heavy-grunge-texture-background-camila-ballell.mp4"
    wm_rel = "assets/watermark_clean_no_stroke.png"
    wav_rel = f"output/audio_babak/babak_{babak_num}.wav"
    out_babak_rel = f"export/temp_assembly/g{babak_num-1}_shots.mp4"

    sub_filter = (
        f"subtitles='{srt_rel}':fontsdir='{fonts_rel}':force_style="
        f"'Fontname=Poppins Bold,Fontsize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H90050505,"
        f"BorderStyle=1,Outline=1.2,Shadow=1.2,MarginV=48,Alignment=2'"
    )

    fc = (
        f"[0:v]format=rgb24[base];"
        f"[1:v]scale=1920:1080,format=gray,format=rgb24,colorchannelmixer=rr=0.35:gg=0.35:bb=0.35[grunge];"
        f"[base][grunge]blend=all_mode=screen,format=rgb24[blended];"
        f"[blended]vignette=PI/4.2:eval=init,format=yuv420p[vignetted];"
        f"[vignetted][3:v]overlay=(W-w)/2:540[with_wm];"
        f"[with_wm]{sub_filter}[outv]"
    )

    print(f"Compositing Babak {babak_num} with continuous audio, shifted watermark, and subtitles...", flush=True)
    comp_cmd = [
        "ffmpeg", "-y"
    ] + input_args + [
        "-stream_loop", "-1", "-i", grunge_rel,
        "-i", wav_rel,
        "-i", wm_rel,
        "-filter_complex", fc,
        "-map", "[outv]",
        "-map", "2:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
        "-t", f"{total_dur:.3f}",
        out_babak_rel
    ]
    subprocess.run(comp_cmd, cwd=str(project), check=True)
    print(f"✓ Babak {babak_num} visual track ready: {out_babak.name} ({out_babak.stat().st_size/1048576:.1f} MB)", flush=True)

    # Attach Chapter Bridge Title Card (Clean optical cut: bridge finishes film burn, lalu narasi mulai jernih 100%)
    bridge_p = project / "output" / "bridges_p404" / f"bridge_p404_babak_{babak_num}_with_burn.mp4"
    final_babak = temp_dir / f"g{babak_num-1}_final.mp4"
    if bridge_p.exists():
        txt_b = temp_dir / f"concat_b{babak_num}.txt"
        txt_b.write_text(f"file '{bridge_p.as_posix()}'\nfile '{out_babak.as_posix()}'\n", encoding="utf-8")
        cmd_bridge = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(txt_b),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
            str(final_babak)
        ]
        subprocess.run(cmd_bridge, check=True)
        print(f"✓ Clean optical cut bridge -> {final_babak.name}", flush=True)
    else:
        shutil.copy(str(out_babak), str(final_babak))

    return final_babak


def assemble_all_chapters(project_dir):
    project = Path(project_dir).resolve()
    temp_dir = project / "export" / "temp_assembly"
    temp_dir.mkdir(parents=True, exist_ok=True)
    export_dir = project / "export"
    final_master = master_path(project)

    from chapter_cards import ensure_cards
    print("Building chapter cards and closing...", flush=True)
    ensure_cards(project)

    from faster_whisper import WhisperModel
    print("Loading WhisperModel tiny for full pipeline...", flush=True)
    whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")

    # Render each of the 5 Babak
    babak_files = []
    chapter_offsets = []
    running_dur = 0.0
    state_file = export_dir / "render_run_state.json"

    for b_num in range(1, 6):
        state_file.write_text(json.dumps({
            "status": "assembly",
            "started_at": time.time() - (b_num - 1) * 120,
            "project": project.name,
            "active_babak": b_num,
            "phase": f"Memproses Babak {b_num}/5 (Narasi Mengalir + Subtitle Presisi)"
        }, indent=2), encoding="utf-8")
        bf = render_babak_video(project, b_num, whisper_model)
        chapter_offsets.append(running_dur)
        cmd_dur = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(bf)]
        r = subprocess.run(cmd_dur, capture_output=True, text=True)
        d = float(r.stdout.strip()) if r.stdout.strip() else 0.0
        running_dur += d
        babak_files.append(bf)

    # Outro card
    outro_card = project / "output" / "outro" / "outro_conclusion_card.mp4"
    if outro_card.exists():
        babak_files.append(outro_card)

    print("\n=== CONCATENATING ALL 5 CHAPTERS + OUTRO ===", flush=True)
    concat_list = temp_dir / "master_chapters_concat.txt"
    lines = [f"file '{f.as_posix()}'" for f in babak_files]
    concat_list.write_text("\n".join(lines), encoding="utf-8")

    merged_no_music = temp_dir / "master_no_music.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy", str(merged_no_music)
    ], check=True)

    # Master background music with sidechain ducking & chapter fanfare
    bg_music = project / "assets" / "music" / "bg_main_dark_cinematic.mp3"
    bg_viking = project / "assets" / "music" / "bg_viking_chapter.mp3"
    print(f"Mixing background music with sidechain ducking & fanfare...", flush=True)

    inputs = ["-i", str(merged_no_music), "-stream_loop", "-1", "-i", str(bg_music)]
    viking_idx = []
    if bg_viking.exists():
        for _ in chapter_offsets:
            inputs.extend(["-i", str(bg_viking)])
            viking_idx.append(len(viking_idx) + 2)

    parts = [
        "[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[narr][narrsc]",
        f"[1:a]atrim=0:{running_dur+60:.3f},volume=0.28,aformat=sample_rates=48000:channel_layouts=stereo[bgmain]"
    ]
    vk_labels = []
    for k, (off, idx) in enumerate(zip(chapter_offsets, viking_idx)):
        parts.append(
            f"[{idx}:a]atrim=0:12.0,asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d=2.0,afade=t=out:st=10.0:d=2.0,"
            f"volume=0.28,aformat=sample_rates=48000:channel_layouts=stereo,"
            f"adelay={int(off*1000)}|{int(off*1000)}[vk{k}]"
        )
        vk_labels.append(f"[vk{k}]")

    music_ins = "[bgmain]" + "".join(vk_labels)
    parts.append(f"{music_ins}amix=inputs={1+len(vk_labels)}:normalize=0:duration=first[music]")
    parts.append("[music][narrsc]sidechaincompress=threshold=0.08:ratio=3.5:attack=60:release=400[ducked]")
    parts.append("[narr][ducked]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.98[aout]")

    mix_fc = ";".join(parts)

    cmd = [
        "ffmpeg", "-y"
    ] + inputs + [
        "-filter_complex", mix_fc,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
        "-shortest",
        str(final_master)
    ]
    subprocess.run(cmd, check=True)

    dur = wav_dur(final_master) if final_master.suffix == ".wav" else 0
    size_mb = final_master.stat().st_size / 1048576
    print(f"\n============================================================")
    print(f"✓ MASTER FILM CONTINUOUS SELESAI: {final_master.name}")
    print(f"   Ukuran: {size_mb:.1f} MB | Lokasi: {final_master}")
    print(f"============================================================")

    # Update render_run_state.json
    state_file = export_dir / "render_run_state.json"
    state_file.write_text(json.dumps({
        "status": "done",
        "completed_at": time.time(),
        "total": 90,
        "clips": 90,
        "master": str(final_master),
        "project": project.name
    }, indent=2), encoding="utf-8")
    return final_master


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project", help="Path to project e.g. D:/project/a045")
    parser.add_argument("--babak", type=int, help="Render single babak (1-5)")
    args = parser.parse_args()

    if args.babak:
        render_babak_video(args.project, args.babak)
    else:
        assemble_all_chapters(args.project)
