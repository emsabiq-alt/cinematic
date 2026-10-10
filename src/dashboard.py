"""
dashboard.py — Dashboard Renderer Multi-Proyek (Samalas 1257 & Merapi 1006).
Server HTTP stdlib, tanpa dependensi eksternal.

Mendukung:
  - Pergantian multi-proyek dinamis (a044 Merapi 1006 & render-p404 Samalas 1257)
  - Pemantauan render paralel real-time
  - Inspektur scene, naskah TTS, VO, & subtitle
  - Quality gates otomatis
  - Pratinjau video & thumbnail Google Flow
"""
import contextlib
import json
import os
import re
import subprocess
import sys
import time
import uuid
import wave
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from cine_paths import projects_root as _projects_root, REPO_ROOT as _REPO_ROOT
except ImportError:
    _projects_root = lambda: Path('.').resolve()
    _REPO_ROOT = Path(__file__).resolve().parent.parent
from urllib.parse import urlparse, unquote, parse_qs

from factory_pipeline import next_pending_stage

PORT = 5188
REPO = "emsabiq-alt/cinematic"
HTML = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "dashboard.html")

_gh_cache = {"at": 0.0, "data": None}
_GH_TTL = 20.0
_start_time = time.time()
_active_project = "a057"  # Default: proyek contoh
_file_samples = {}


def sample_growth(path):
    """Return current size and write velocity without blocking the encoder."""
    path = Path(path)
    if not path.exists():
        return {"size": 0, "rate": 0.0, "age": None, "growing": False}
    now = time.time()
    size = path.stat().st_size
    prev = _file_samples.get(str(path))
    rate = 0.0
    if prev and now > prev[0] and size >= prev[1]:
        rate = (size - prev[1]) / (now - prev[0])
    _file_samples[str(path)] = (now, size)
    age = max(0.0, now - path.stat().st_mtime)
    return {"size": size, "rate": rate, "age": age, "growing": rate > 1024 or age < 8}


def fmt_eta_seconds(seconds):
    if seconds is None:
        return "Mengukur kecepatan..."
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"±{seconds} detik"
    return f"±{max(1, round(seconds / 60, 1))} menit"


def _duration_shots(duration):
    if "15-20" in str(duration):
        return 90
    if "3-5" in str(duration):
        return 30
    return 65


def list_available_projects(projects_root=None):
    projects_root = Path(projects_root) if projects_root else _projects_root()
    projs = []
    root = Path(projects_root)
    candidates = sorted(root.glob("a[0-9][0-9][0-9]"))
    # Single-project checkout: the root itself may be the project.
    if (root / "project.json").exists() and root not in candidates:
        candidates = [root] + candidates
    for project in candidates:
        meta_path = project / "project.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        clips_dir = project / "output" / "rendered_clips"
        clips_n = len(list(clips_dir.glob("shot_*.mp4"))) if clips_dir.exists() else 0
        total = int(meta.get("total_shots") or (75 if project.name == "a044" else _duration_shots(meta.get("duration"))))
        projs.append({
            "id": meta.get("id", project.name),
            "title": meta.get("title", project.name),
            "status": meta.get("status", "created"),
            "clips": clips_n,
            "total_shots": total,
            "base_dir": str(project).replace("\\", "/"),
            "pipeline": meta.get("pipeline", []),
            "active_stage": meta.get("active_stage"),
        })

    # Legacy Samalas workspace has no Video Factory project.json in its root.
    if root.resolve() == _projects_root().resolve():
        p_p404 = root / "render-p404"
        if p_p404.exists():
            projs.append({
                "id": "render-p404",
                "title": "SAMALAS 1257: Monster Lombok yang Mengubah IklIM DUNIA".replace("IklIM", "Iklim"),
                "status": "ready", "clips": 77, "total_shots": 77,
                "base_dir": str(p_p404).replace("\\", "/"),
            })
    return projs


def set_active_project(pid):
    global _active_project
    _active_project = pid


def _resolve_project_base(pid, projects_root):
    """Return the project directory for pid.

    Supports both layouts:
      - multi-project: <projects_root>/<pid>/  (e.g. D:/project/a057)
      - single-project checkout: <projects_root>/ itself (repo root is the project)
    """
    root = Path(projects_root).resolve()
    cand = root / str(pid)
    if (cand / "project.json").exists():
        return cand
    meta_path = root / "project.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            meta = {}
        if meta.get("id") == pid or str(pid) == root.name:
            return root
    return cand


def get_project_config(pid=None, projects_root=None):
    projects_root = Path(projects_root) if projects_root else _projects_root()
    global _active_project
    pid = pid or _active_project
    root = Path(projects_root).resolve()

    if pid == "render-p404":
        base = Path(__file__).resolve().parents[1]
        title = "SAMALAS 1257: Monster Lombok yang Mengubah Iklim Dunia"
        total, story = 77, base / "input/samalas_master_storyboard_enriched.json"
        chapter_starts = {1: 1, 17: 2, 33: 3, 49: 4, 65: 5}
        master = "SAMALAS_1257_MASTER_FILM_15MIN_P404.mp4"
        log = base / "export/local_render_m2.log"
    else:
        base = _resolve_project_base(pid, root)
        meta_path = base / "project.json"
        if not meta_path.exists():
            raise ValueError(f"Workspace tidak ditemukan: {pid}")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        title = meta.get("title", str(pid))
        total = int(meta.get("total_shots") or (75 if pid == "a044" else _duration_shots(meta.get("duration"))))
        if pid == "a044":
            story = base / "input/merapi_master_storyboard_enriched.json"
            chapter_starts = {1: 1, 16: 2, 31: 3, 46: 4, 61: 5}
            master = "MERAPI_1006_MASTER_FILM_15MIN_P404.mp4"
            log = base / "export/local_render_a044.log"
        else:
            story = base / "input/storyboard.json"
            per = max(1, total // 5)
            chapter_starts = {1 + i * per: i + 1 for i in range(5)}
            master = re.sub(r"[^A-Z0-9]+", "_", title.upper()).strip("_") + "_MASTER.mp4"
            log = base / "factory.log"

    norm = lambda p: str(p).replace("\\", "/")
    return {
        "id": str(pid), "title": title, "BASE": norm(base),
        "CLIPS": norm(base / "output/rendered_clips"),
        "AUDIO": norm(base / "output/audio_supertonic"),
        "SUBS": norm(base / "output/subtitles"),
        "EXPORT": norm(base / "export"),
        "IMAGES": norm(base / "output/flow_images"),
        "SCRIPT": norm(base / "script"), "STORY": norm(story),
        "LOG": norm(log), "THUMB_DIR": norm(base / "export/thumbnail_flow"),
        "TOTAL_SHOTS": total, "CHAPTER_STARTS": chapter_starts,
        "MASTER_NAME": master,
    }


# ── util ────────────────────────────────────────────────────────
def wav_duration(path):
    try:
        with contextlib.closing(wave.open(str(path), "rb")) as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return 0.0


def count_files(d, suffix):
    if not os.path.isdir(d):
        return 0
    return len([f for f in os.listdir(d) if f.endswith(suffix)])


def read_render_run(ctx):
    """Current rerender marker; existing output files pre-dating it do not count."""
    p = Path(ctx["EXPORT"]) / "render_run_state.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        started = float(data.get("started_at", 0))
        return data if started > 0 else None
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def count_current_run_clips(ctx, run):
    if not run or run.get("status") not in {"rendering", "assembly"}:
        return count_files(ctx["CLIPS"], ".mp4")
    started = float(run["started_at"])
    clips_dir = Path(ctx["CLIPS"])
    return sum(1 for f in clips_dir.glob("shot_*.mp4")
               if f.is_file() and f.stat().st_mtime >= started and f.stat().st_size > 300_000)


def read_log_tail(log_path, n=40):
    if not os.path.exists(log_path):
        return []
    try:
        with open(log_path, encoding="utf-8", errors="ignore") as f:
            return [l.rstrip("\n\r") for l in f if l.strip()][-n:]
    except Exception:
        return []


def phase_from_log(lines, clips_done, total=75):
    joined = "\n".join(lines)
    if "LOCAL_RENDER_ALL_DONE" in joined:
        return "selesai", "Render dan assembly selesai"
    if "ASSEMBLY GAGAL" in joined or "] FAIL" in joined:
        return "gagal", "Ada tahap yang gagal - periksa log"
    if "MULAI ASSEMBLY" in joined:
        return "assembly", "Menggabungkan klip: crossfade, musik, ketikan"
    if clips_done > 0:
        return "render", f"Merender klip {clips_done}/{total}"
    if joined:
        return "mulai", "Menyiapkan worker render"
    return "idle", "Belum ada proses berjalan"


def chapter_of(n, chapter_starts=None):
    chapter_starts = chapter_starts or {1: 1, 16: 2, 31: 3, 46: 4, 61: 5}
    ch = 1
    for start, c in sorted(chapter_starts.items()):
        if n >= start:
            ch = c
    return ch


def eta_seconds(clips_done, total=75):
    if clips_done <= 0 or clips_done >= total:
        return None
    elapsed = time.time() - _start_time
    if elapsed < 20:
        return None
    rate = clips_done / elapsed
    if rate <= 0:
        return None
    return int((total - clips_done) / rate)


# ── Video Factory ───────────────────────────────────────────────
def validate_video_request(data):
    title = (data.get("title") or "").strip()
    topic = (data.get("topic") or "").strip()
    if not title:
        return False, "Judul video wajib diisi"
    if not topic:
        return False, "Topik/ringkasan cerita wajib diisi"
    if len(title) > 140:
        return False, "Judul terlalu panjang"
    return True, ""


def next_project_dir(projects_root=None):
    projects_root = Path(projects_root) if projects_root else _projects_root()
    root = Path(projects_root)
    root.mkdir(parents=True, exist_ok=True)
    nums = []
    for p in root.iterdir():
        if p.is_dir() and re.fullmatch(r"a\d{3}", p.name):
            nums.append(int(p.name[1:]))
    return root / f"a{(max(nums) + 1 if nums else 1):03d}"


def create_video_job(data, projects_root=None):
    projects_root = Path(projects_root) if projects_root else _projects_root()
    ok, err = validate_video_request(data)
    if not ok:
        raise ValueError(err)

    project = next_project_dir(projects_root)
    project.mkdir(parents=True, exist_ok=False)
    job_id = time.strftime("vf_%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]
    pipeline = [
        {"key": "outline", "label": "Outline", "status": "pending"},
        {"key": "script", "label": "Script", "status": "waiting"},
        {"key": "storyboard", "label": "Storyboard", "status": "waiting"},
        {"key": "assets", "label": "Visual Assets", "status": "waiting"},
        {"key": "tts", "label": "TTS + Subtitle", "status": "waiting"},
        {"key": "render", "label": "Local + Cloud Render", "status": "waiting"},
    ]
    cfg = {
        "job_id": job_id,
        "title": data["title"].strip(),
        "topic": data["topic"].strip(),
        "style": data.get("style") or "project404",
        "duration": data.get("duration") or "8-12 menit",
        "voice": data.get("voice") or "M2",
        "mode": data.get("mode") or "step",
        "output": data.get("output") or "local+cloud",
        "status": "created",
        "project_dir": str(project).replace("\\", "/"),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pipeline": pipeline,
    }
    (project / "project.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (project / "factory.log").write_text(
        f"[{cfg['created_at']}] created {job_id}\n"
        f"title: {cfg['title']}\nstyle: {cfg['style']}\nmode: {cfg['mode']}\n",
        encoding="utf-8",
    )
    return cfg


def factory_state(pid=None, projects_root=None):
    projects_root = Path(projects_root) if projects_root else _projects_root()
    pid = pid or _active_project
    if pid == "render-p404":
        return {"pipeline": [], "next_stage": None, "button_label": "Proyek legacy", "can_generate": False, "status": "ready"}
    project = _resolve_project_base(pid, projects_root)
    cfg_path = project / "project.json"
    if not cfg_path.exists():
        return {"pipeline": [], "next_stage": None, "button_label": "Workspace belum siap", "can_generate": False, "status": "missing"}
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    nxt = next_pending_stage(cfg)
    active = cfg.get("active_stage")
    if active == "completed":
        active = None
    labels = {"outline": "Outline", "script": "Script", "storyboard": "Storyboard", "assets": "Visual Assets", "tts": "TTS + Subtitle", "render": "Render"}
    activities = {
        "outline": "Menyusun struktur riset lima babak",
        "script": "Menyusun naskah voice-over",
        "storyboard": "Memecah naskah menjadi shot visual",
        "assets": "Menghasilkan aset visual",
        "tts": "Menghasilkan narasi dan subtitle",
        "render": "Merender dan merakit master film",
    }
    pipeline = cfg.get("pipeline", [])
    total_shots = int(cfg.get("total_shots") or _duration_shots(cfg.get("duration")))

    # Granular sub-stage progress calculation
    active_sub_pct = 0.0
    for item in pipeline:
        st = item.get("status")
        k = item.get("key")
        if st == "completed":
            item["percent"] = 100
            item["detail"] = "Selesai"
        elif st == "in_progress" or (k == active):
            if k == "assets":
                cnt = len(list((project / "output" / "flow_images").glob("shot_*.png")))
                pct = min(100, round(cnt / total_shots * 100)) if total_shots else 0
                item["percent"] = pct
                item["detail"] = f"{cnt}/{total_shots} gambar ({pct}%)"
                active_sub_pct = pct
            elif k == "tts":
                cnt = len(list((project / "output" / "audio_supertonic").glob("shot_*.wav")))
                pct = min(100, round(cnt / total_shots * 100)) if total_shots else 0
                item["percent"] = pct
                item["detail"] = f"{cnt}/{total_shots} audio & subtitle ({pct}%)"
                active_sub_pct = pct
            elif k == "render":
                cnt = len(list((project / "output" / "rendered_clips").glob("shot_*.mp4")))
                pct = min(100, round(cnt / total_shots * 100)) if total_shots else 0
                item["percent"] = pct
                item["detail"] = f"{cnt}/{total_shots} klip terender ({pct}%)"
                active_sub_pct = pct
            else:
                item["percent"] = None
                item["detail"] = "Sedang diproses..."
                active_sub_pct = 0.0
        else:
            item["percent"] = 0
            item["detail"] = st

    completed = sum(x.get("status") == "completed" for x in pipeline)
    total = len(pipeline)
    outputs = []
    for stage, rel in (("outline", "input/outline.md"), ("script", "input/script.md"), ("storyboard", "input/storyboard.json")):
        output = project / rel
        if output.exists():
            outputs.append({
                "stage": stage, "name": output.name,
                "path": str(output).replace("\\", "/"), "bytes": output.stat().st_size,
            })
    started = float(cfg.get("stage_started_at") or 0)
    elapsed = max(0, int(time.time() - started)) if active and started else 0
    automated = nxt in {"outline", "script", "storyboard", "assets", "tts", "render"}
    render_mode = cfg.get("output", "Local 4-Worker Only")

    if active:
        button = f"Sedang Generate {labels.get(active, active)}..."
    elif nxt == "render":
        if "Cloud" in render_mode:
            button = "▶ Mulai Cloud Render Matrix"
        elif "Hybrid" in render_mode:
            button = "▶ Mulai Render Hybrid"
        else:
            button = "▶ Mulai Render Lokal (4 Worker)"
    elif nxt and automated:
        button = f"Generate {labels.get(nxt, nxt)}"
    elif nxt:
        button = f"{labels.get(nxt, nxt)} belum otomatis"
    else:
        button = "Pipeline selesai"

    # Smooth overall progress blending completed stages + active sub-progress
    blended_prog = (completed + (active_sub_pct / 100.0)) / total * 100.0 if total else 0.0

    return {
        "pipeline": pipeline, "next_stage": nxt,
        "active_stage": active, "button_label": button,
        "can_generate": bool(nxt and not active and automated),
        "status": cfg.get("status", "created"),
        "last_error": cfg.get("last_error"),
        "project_dir": str(project).replace("\\", "/"),
        "completed_stages": completed, "total_stages": total,
        "progress_percent": round(blended_prog),
        "elapsed_seconds": elapsed,
        "activity": activities.get(active) if active else ("Siap menjalankan " + labels.get(nxt, nxt) if nxt else "Semua tahap selesai"),
        "outputs": outputs,
        "render_mode": render_mode,
    }


def recent_video_jobs(projects_root=None, limit=10):
    projects_root = Path(projects_root) if projects_root else _projects_root()
    jobs = []
    root = Path(projects_root)
    if root.exists():
        for p in root.glob("a[0-9][0-9][0-9]/project.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                if "title" in d and "pipeline" in d:
                    d.setdefault("project_dir", str(p.parent).replace("\\", "/"))
                    jobs.append(d)
            except Exception:
                pass
    jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return jobs[:limit]


# ── Thumbnail Studio ────────────────────────────────────────────
def thumbnail_pack(thumb_dir=None):
    ctx = get_project_config()
    td = Path(thumb_dir or ctx["THUMB_DIR"])
    meta = td / "thumbnail_flow_pack.json"
    if not meta.exists():
        return {
            "method": "Google Flow via CDP/MCP (Waiting for pack)",
            "titles": [], "thumbnails": [], "description": "", "chapters": [], "music_credit": [],
            "metadata_path": str(meta).replace("\\", "/"),
        }
    data = json.loads(meta.read_text(encoding="utf-8"))
    data["metadata_path"] = str(meta).replace("\\", "/")
    return data


# ── data per-scene ──────────────────────────────────────────────
def load_narrations(story_path=None):
    ctx = get_project_config()
    sp = story_path or ctx["STORY"]
    out = {}
    try:
        with open(sp, encoding="utf-8") as f:
            for s in json.load(f)["shots"]:
                out[s["id"]] = s.get("narration", "")
    except Exception:
        pass
    return out


def load_visual_prompts(story_path=None):
    ctx = get_project_config()
    sp = story_path or ctx["STORY"]
    out = {}
    try:
        with open(sp, encoding="utf-8") as f:
            for s in json.load(f)["shots"]:
                out[s["id"]] = s.get("visual_prompt", "")
    except Exception:
        pass
    return out


def parse_srt(path):
    items = []
    try:
        raw = open(path, encoding="utf-8").read().strip()
    except Exception:
        return items
    for block in re.split(r"\n\s*\n", raw):
        lines = [l for l in block.strip().split("\n") if l.strip()]
        if len(lines) < 3:
            continue
        m = re.match(r"([\d:,]+)\s*-->\s*([\d:,]+)", lines[1])
        if not m:
            continue
        items.append({"start": m.group(1), "end": m.group(2),
                      "text": " ".join(lines[2:]), "lines": len(lines) - 2})
    return items


def scene_rows(ctx=None):
    ctx = ctx or get_project_config()
    total = ctx["TOTAL_SHOTS"]
    rows = []
    for i in range(1, total + 1):
        sid = f"shot_{i:03d}"
        wav = os.path.join(ctx["AUDIO"], sid + ".wav")
        srt = os.path.join(ctx["SUBS"], sid + ".srt")
        mp4 = os.path.join(ctx["CLIPS"], sid + ".mp4")
        txt = os.path.join(ctx["SCRIPT"], sid + ".txt")
        has_clip = os.path.isfile(mp4)
        png = os.path.join(ctx.get("IMAGES", ""), sid + ".png")
        size = os.path.getsize(mp4) if has_clip else 0
        rows.append({
            "n": i, "id": sid, "chapter": chapter_of(i, ctx["CHAPTER_STARTS"]),
            "vo": os.path.isfile(wav),
            "sub": os.path.isfile(srt),
            "script": os.path.isfile(txt),
            "image": os.path.isfile(png),
            "clip": has_clip,
            "clip_mb": round(size / 1048576, 1) if has_clip else 0,
            "dur": round(wav_duration(wav), 1) if os.path.isfile(wav) else 0,
            "chapter_head": i in ctx["CHAPTER_STARTS"],
        })
    return rows


def scene_detail(n, ctx=None):
    ctx = ctx or get_project_config()
    sid = f"shot_{n:03d}"
    wav = os.path.join(ctx["AUDIO"], sid + ".wav")
    srt = os.path.join(ctx["SUBS"], sid + ".srt")
    mp4 = os.path.join(ctx["CLIPS"], sid + ".mp4")
    txt = os.path.join(ctx["SCRIPT"], sid + ".txt")
    narr = load_narrations(ctx["STORY"]).get(sid, "")
    png = os.path.join(ctx.get("IMAGES", ""), sid + ".png")
    prompt = load_visual_prompts(ctx["STORY"]).get(sid, "")
    script_text = ""
    if os.path.isfile(txt):
        script_text = open(txt, encoding="utf-8").read().strip()
    return {
        "n": n, "id": sid, "chapter": chapter_of(n, ctx["CHAPTER_STARTS"]),
        "narration": narr,
        "visual_prompt": prompt,
        "has_image": os.path.isfile(png),
        "image_mtime": int(os.path.getmtime(png)) if os.path.isfile(png) else 0,
        "script": script_text,
        "subtitles": parse_srt(srt),
        "vo_dur": round(wav_duration(wav), 2) if os.path.isfile(wav) else 0,
        "has_vo": os.path.isfile(wav),
        "has_clip": os.path.isfile(mp4),
        "clip_mb": round(os.path.getsize(mp4) / 1048576, 1) if os.path.isfile(mp4) else 0,
    }


# ── QA otomatis ─────────────────────────────────────────────────
def run_qa(ctx=None):
    ctx = ctx or get_project_config()
    total = ctx["TOTAL_SHOTS"]
    issues = []

    bad_num = []
    if os.path.isdir(ctx["SCRIPT"]):
        for i in range(1, total + 1):
            p = os.path.join(ctx["SCRIPT"], f"shot_{i:03d}.txt")
            if not os.path.isfile(p):
                continue
            t = open(p, encoding="utf-8").read()
            if any(c.isdigit() for c in t):
                bad_num.append(i)
    issues.append({
        "key": "angka", "label": "Angka mentah di naskah TTS",
        "ok": not bad_num, "count": len(bad_num), "shots": bad_num[:12],
        "hint": "Angka harus dieja kata (1006 -> seribu enam)",
    })

    bad_dash = []
    if os.path.isdir(ctx["SCRIPT"]):
        for i in range(1, total + 1):
            p = os.path.join(ctx["SCRIPT"], f"shot_{i:03d}.txt")
            if os.path.isfile(p) and "\u2014" in open(p, encoding="utf-8").read():
                bad_dash.append(i)
    issues.append({
        "key": "dash", "label": "Em-dash di naskah TTS",
        "ok": not bad_dash, "count": len(bad_dash), "shots": bad_dash[:12],
        "hint": "Em-dash harus jadi koma agar dibaca jeda",
    })

    lonely = []
    if os.path.isdir(ctx["SUBS"]):
        for i in range(1, total + 1):
            p = os.path.join(ctx["SUBS"], f"shot_{i:03d}.srt")
            if not os.path.isfile(p):
                continue
            for it in parse_srt(p):
                if len(it["text"].split()) <= 2:
                    lonely.append(i)
                    break
    issues.append({
        "key": "lonely", "label": "Frasa subtitle kesepian (<=2 kata)",
        "ok": not lonely, "count": len(lonely), "shots": lonely[:12],
        "hint": "Minimal 3 kata per baris agar tidak berkedip",
    })

    tiny = []
    if os.path.isdir(ctx["CLIPS"]):
        for i in range(1, total + 1):
            p = os.path.join(ctx["CLIPS"], f"shot_{i:03d}.mp4")
            if os.path.isfile(p) and os.path.getsize(p) < 300 * 1024:
                tiny.append(i)
    issues.append({
        "key": "tiny", "label": "Klip rusak / terlalu kecil",
        "ok": not tiny, "count": len(tiny), "shots": tiny[:12],
        "hint": "Klip < 300 KB kemungkinan gagal render",
    })

    need = {
        "musik utama": os.path.join(ctx["BASE"], "assets/music/bg_main_dark_cinematic.mp3"),
        "suara ketikan": os.path.join(ctx["BASE"], "assets/sfx/typewriter_burst.wav"),
        "watermark": os.path.join(ctx["BASE"], "assets/watermark_clean_no_stroke.png"),
        "font Poppins": os.path.join(ctx["BASE"], "assets/fonts/Poppins-Bold.ttf"),
    }
    missing = [k for k, p in need.items() if not os.path.isfile(p)]
    issues.append({
        "key": "assets", "label": "Aset produksi proyek",
        "ok": not missing, "count": len(missing), "shots": [],
        "hint": "Kurang: " + ", ".join(missing) if missing else "Semua aset siap",
    })

    return issues


# ── GitHub ──────────────────────────────────────────────────────
def gh_runs():
    now = time.time()
    if _gh_cache["data"] is not None and now - _gh_cache["at"] < _GH_TTL:
        return _gh_cache["data"]
    out = []
    try:
        r = subprocess.run(
            ["gh", "run", "list", "-R", REPO, "--limit", "5",
             "--json", "databaseId,status,conclusion,displayTitle,workflowName,createdAt"],
            capture_output=True, text=True, timeout=25)
        if r.returncode == 0 and r.stdout.strip():
            for it in json.loads(r.stdout):
                out.append({
                    "id": it.get("databaseId"),
                    "status": it.get("status"),
                    "conclusion": it.get("conclusion") or "",
                    "title": (it.get("displayTitle") or "")[:70],
                    "workflow": it.get("workflowName") or "",
                    "created": it.get("createdAt") or "",
                    "url": f"https://github.com/{REPO}/actions/runs/{it.get('databaseId')}",
                })
    except Exception:
        pass
    _gh_cache["at"] = now
    _gh_cache["data"] = out
    return out


def list_videos(export_dir=None):
    ctx = get_project_config()
    exp = export_dir or ctx["EXPORT"]
    vids = []
    if os.path.isdir(exp):
        for f in sorted(os.listdir(exp)):
            if f.endswith(".mp4"):
                p = os.path.join(exp, f)
                vids.append({"name": f,
                             "size_mb": round(os.path.getsize(p) / 1048576, 1),
                             "mtime": os.path.getmtime(p)})
    vids.sort(key=lambda v: -v["mtime"])
    return vids


def get_assembly_breakdown(ctx, run=None):
    temp = Path(ctx["EXPORT"]) / "temp_assembly"
    pid = ctx["id"]
    run_started = (float(run.get("started_at", 0))
                   if run and run.get("status") in {"rendering", "assembly"} else 0)

    def is_current(path, min_size=1):
        # Windows file timestamps can equal the run marker within one clock tick;
        # require a small lead so pre-existing outputs never count as current.
        return (path.exists() and path.stat().st_size >= min_size
                and path.stat().st_mtime > run_started + (0.5 if run_started else 0))
    if pid == "a044":
        chapters = [
            {"num": 1, "title": "Babak I · Misteri Candi Sambisari (Shot 01–15)", "file": "g0_final.mp4", "shots": "g0_shots.mp4"},
            {"num": 2, "title": "Babak II · Jejak Geologi Bemmelen (Shot 16–30)", "file": "g1_final.mp4", "shots": "g1_shots.mp4"},
            {"num": 3, "title": "Babak III · Anatomi Erupsi Katastropik (Shot 31–45)", "file": "g2_final.mp4", "shots": "g2_shots.mp4"},
            {"num": 4, "title": "Babak IV · Pralaya Medang & Eksodus (Shot 46–60)", "file": "g3_final.mp4", "shots": "g3_shots.mp4"},
            {"num": 5, "title": "Babak V · Kapsul Waktu Lahar Merapi (Shot 61–75)", "file": "g4_final.mp4", "shots": "g4_shots.mp4"},
        ]
    elif pid == "a045":
        chapters = [
            {"num": 1, "title": "Babak I · Danau Kawah & Tanda Awal (Shot 01–23)", "file": "g0_final.mp4", "shots": "g0_shots.mp4"},
            {"num": 2, "title": "Babak II · Malam Petaka 19 Mei 1919 (Shot 24–36)", "file": "g1_final.mp4", "shots": "g1_shots.mp4"},
            {"num": 3, "title": "Babak III · Gelombang Lahar Panas (Shot 37–50)", "file": "g2_final.mp4", "shots": "g2_shots.mp4"},
            {"num": 4, "title": "Babak IV · Evakuasi & Dampak Kemanusiaan (Shot 51–65)", "file": "g3_final.mp4", "shots": "g3_shots.mp4"},
            {"num": 5, "title": "Babak V · Terowongan Drainase Taverne (Shot 66–90)", "file": "g4_final.mp4", "shots": "g4_shots.mp4"},
        ]
    else:
        chapters = [
            {"num": 1, "title": "Babak I · Misteri Abu Vulkanik 1257 (Shot 01–16)", "file": "g0_final.mp4", "shots": "g0_shots.mp4"},
            {"num": 2, "title": "Babak II · Ekspedisi Danau Segara Anak (Shot 17–32)", "file": "g1_final.mp4", "shots": "g1_shots.mp4"},
            {"num": 3, "title": "Babak III · Ledakan Kaldera Ultra-Plinian (Shot 33–48)", "file": "g2_final.mp4", "shots": "g2_shots.mp4"},
            {"num": 4, "title": "Babak IV · Zaman Es Kecil & Kelaparan Global (Shot 49–64)", "file": "g3_final.mp4", "shots": "g3_shots.mp4"},
            {"num": 5, "title": "Babak V · Warisan Geologi Samalas (Shot 65–77)", "file": "g4_final.mp4", "shots": "g4_shots.mp4"},
        ]

    master_path = Path(ctx["EXPORT"]) / ctx["MASTER_NAME"]
    narr_m = temp / "narration_master.mp4"
    has_master = is_current(master_path, 10 * 1024 * 1024) and (
        not run or run.get("status") not in {"rendering", "assembly"}
    )

    chapter_files = []
    for c in chapters:
        chapter_files.append((temp / c["file"], temp / c["shots"]))

    res = []
    for idx, c in enumerate(chapters):
        f_final, f_shots = chapter_files[idx]
        later_started = any(
            is_current(p) for pair in chapter_files[idx + 1:] for p in pair
        ) or is_current(narr_m) or is_current(master_path)

        if has_master or (is_current(f_final, 1024 * 1024) and later_started):
            growth = sample_growth(f_final)
            row = {
                "status": "done", "percent": 100,
                "size_mb": round(growth["size"] / 1048576, 1),
                "activity": "Babak selesai dan terkunci",
                "detail": "Crossfade seluruh shot dan kartu bab telah tervalidasi.",
                "eta": "Selesai", "eta_seconds": 0,
                "next": "Dilanjutkan ke babak berikutnya",
                "rate_mbps": 0, "active": False,
            }
        elif is_current(f_final):
            growth = sample_growth(f_final)
            row = {
                "status": "encoding", "percent": 96,
                "size_mb": round(growth["size"] / 1048576, 1),
                "activity": "Memasang kartu bab + hard cut",
                "detail": "File masih ditulis; 100% hanya muncul setelah tahap berikutnya dimulai.",
                "eta": "±1 menit", "eta_seconds": 60,
                "next": "Validasi babak lalu mulai babak berikutnya",
                "rate_mbps": round(growth["rate"] / 1048576, 1), "active": True,
            }
        elif is_current(f_shots):
            growth = sample_growth(f_shots)
            completed_targets = [p.stat().st_size for p, _ in chapter_files[:idx] if is_current(p, 1024 * 1024)]
            target = (sum(completed_targets) / len(completed_targets)) if completed_targets else 165 * 1048576
            raw = growth["size"] / max(target, 1)
            pct = min(92, max(8, int(raw * 88)))
            eta_sec = ((target - growth["size"]) / growth["rate"] + 55) if growth["rate"] > 1024 and growth["size"] < target else None
            row = {
                "status": "encoding", "percent": pct,
                "size_mb": round(growth["size"] / 1048576, 1),
                "activity": "Melebur 15 shot (crossfade + audio)",
                "detail": "Ukuran bergerak berarti FFmpeg masih menulis frame ke babak ini.",
                "eta": fmt_eta_seconds(eta_sec), "eta_seconds": int(eta_sec) if eta_sec is not None else None,
                "next": "Pasang kartu bab dan hard cut",
                "rate_mbps": round(growth["rate"] / 1048576, 1), "active": True,
            }
        else:
            row = {
                "status": "waiting", "percent": 0, "size_mb": 0,
                "activity": "Menunggu antrean",
                "detail": "Babak sebelumnya harus selesai lebih dahulu.",
                "eta": "Menunggu", "eta_seconds": None, "next": "Crossfade 15 shot",
                "rate_mbps": 0, "active": False,
            }
        res.append({"num": c["num"], "title": c["title"], **row})

    outro_path = Path(ctx["BASE"]) / "output/outro/outro_conclusion_card.mp4"
    outro_exists = outro_path.exists()
    res.append({
        "num": "outro", "title": "Outro · Epilog Refleksi Sejarah & Mesin Tik",
        "status": "done" if outro_exists else "waiting",
        "size_mb": round(outro_path.stat().st_size / 1048576, 1) if outro_exists else 0,
        "percent": 100 if outro_exists else 0,
        "activity": "Aset outro siap" if outro_exists else "Menunggu aset outro",
        "detail": "Animasi huruf dan klik mesin tik sudah sinkron." if outro_exists else "Outro belum tersedia.",
        "eta": "Selesai" if outro_exists else "Menunggu", "eta_seconds": 0 if outro_exists else None,
        "next": "Masuk setelah Babak V", "rate_mbps": 0, "active": False,
    })

    if has_master:
        growth = sample_growth(master_path)
        final = {
            "status": "done", "percent": 100,
            "size_mb": round(growth["size"] / 1048576, 1),
            "activity": "Master selesai dan siap diputar",
            "detail": "Concat, backsong, ducking, AAC, dan validasi output selesai.",
            "eta": "Selesai", "eta_seconds": 0, "next": "Quality check / pemutaran",
            "rate_mbps": 0, "active": False,
        }
    elif is_current(master_path):
        growth = sample_growth(master_path)
        final = {
            "status": "encoding", "percent": 98,
            "size_mb": round(growth["size"] / 1048576, 1),
            "activity": "Mixing backsong + sidechain ducking",
            "detail": "Video disalin; audio akhir sedang dicampur dan ditulis ke master.",
            "eta": fmt_eta_seconds(45 if growth["growing"] else None),
            "eta_seconds": 45 if growth["growing"] else None,
            "next": "Validasi durasi, resolusi, dan integritas MP4",
            "rate_mbps": round(growth["rate"] / 1048576, 1), "active": True,
        }
    elif is_current(narr_m):
        growth = sample_growth(narr_m)
        target = 780 * 1048576
        pct = min(96, max(8, int((growth["size"] / target) * 94)))
        eta_sec = ((target - growth["size"]) / growth["rate"] + 50) if growth["rate"] > 1024 and growth["size"] < target else None
        final = {
            "status": "encoding", "percent": pct,
            "size_mb": round(growth["size"] / 1048576, 1),
            "activity": "Menggabungkan 5 babak + outro",
            "detail": "Membuat narration master sebelum musik dan ducking ditambahkan.",
            "eta": fmt_eta_seconds(eta_sec), "eta_seconds": int(eta_sec) if eta_sec is not None else None,
            "next": "Mixing backsong + sidechain ducking",
            "rate_mbps": round(growth["rate"] / 1048576, 1), "active": True,
        }
    elif all(r["status"] == "done" for r in res if isinstance(r["num"], int)):
        final = {
            "status": "encoding", "percent": 4, "size_mb": 0,
            "activity": "Menyiapkan concat master",
            "detail": "Menyusun urutan lima babak dan outro.",
            "eta": "Mengukur kecepatan...", "eta_seconds": None, "next": "Encode narration master",
            "rate_mbps": 0, "active": True,
        }
    else:
        final = {
            "status": "waiting", "percent": 0, "size_mb": 0,
            "activity": "Menunggu seluruh babak",
            "detail": "Master baru dimulai setelah lima babak selesai.",
            "eta": "Menunggu", "eta_seconds": None, "next": "Concat lima babak + outro",
            "rate_mbps": 0, "active": False,
        }

    res.append({
        "num": "final",
        "title": f"Master Assembly · Concat + Backsong Ducking ({ctx['MASTER_NAME']})",
        **final,
    })
    return res


def build_state(pid=None):
    ctx = get_project_config(pid)
    total = ctx["TOTAL_SHOTS"]
    run = read_render_run(ctx)
    clips = count_current_run_clips(ctx, run)
    vo = count_files(ctx["AUDIO"], ".wav")
    subs = count_files(ctx["SUBS"], ".srt")
    log = read_log_tail(ctx["LOG"])
    phase, phase_text = phase_from_log(log, clips, total)
    if run and run.get("status") == "rendering" and "MULAI ASSEMBLY" not in "\n".join(log):
        phase, phase_text = "render", f"Render ulang klip {clips}/{total}"
    elif run and run.get("status") == "assembly":
        phase = "assembly"

    vo_total = 0.0
    if os.path.isdir(ctx["AUDIO"]):
        for f in os.listdir(ctx["AUDIO"]):
            if f.endswith(".wav"):
                vo_total += wav_duration(os.path.join(ctx["AUDIO"], f))

    batches = []
    for line in log:
        m = re.match(r"\[batch (\d+)-(\d+)\] (\w+) in (\d+)s", line)
        if m:
            batches.append({"range": f"{m.group(1)}-{m.group(2)}",
                            "ok": m.group(3) == "OK", "secs": int(m.group(4))})

    breakdown = get_assembly_breakdown(ctx, run)
    ch_done = sum(1 for b in breakdown if isinstance(b.get("num"), int) and b.get("status") == "done")
    ch_total = 5
    has_master = any(b.get("num") == "final" and b.get("status") == "done" for b in breakdown)
    active_step = next((b for b in breakdown if b.get("active")), None)
    waiting_step = next((b for b in breakdown if b.get("status") == "waiting"), None)
    current_step = active_step or (breakdown[-1] if has_master else waiting_step)

    if has_master:
        phase = "selesai"
        overall_pct = 100
        overall_eta = "Selesai — master sebelumnya tetap siap diputar"
        phase_text = ("Render ulang dibatalkan · master sebelumnya tetap aman"
                      if run and run.get("status") == "cancelled"
                      else "Master selesai · menunggu quality check")
    elif phase == "assembly":
        active_pct = int((current_step or {}).get("percent", 0))
        overall_pct = min(99, 75 + int(((ch_done + active_pct / 100) / 6.0) * 24))
        step_eta = (current_step or {}).get("eta_seconds")
        waiting_chapters = sum(1 for b in breakdown if isinstance(b.get("num"), int) and b.get("status") == "waiting")
        final_row = next((b for b in breakdown if b.get("num") == "final"), {})
        future_sec = waiting_chapters * 390 + (420 if final_row.get("status") == "waiting" else 0)
        total_eta = (step_eta + future_sec) if step_eta is not None else None
        overall_eta = (f"Tahap ini {(current_step or {}).get('eta')} · total ±{round(total_eta/60, 1)} menit"
                       if total_eta is not None else "Mengukur ETA tahap aktif...")
        activity = (current_step or {}).get("activity", "Assembly berjalan")
        phase_text = f"{activity} · berikutnya: {(current_step or {}).get('next', 'validasi')}"
    elif clips < total:
        overall_pct = int((clips / total) * 75)
        eta_s = eta_seconds(clips, total)
        overall_eta = f"±{max(1, round(eta_s / 60, 1))} menit tersisa" if eta_s else "menghitung estimasi..."
    else:
        overall_pct = 75
        overall_eta = "Memulai perakitan assembly..."

    qa = run_qa(ctx)
    return {
        "active_project": ctx["id"],
        "project_title": ctx["title"],
        "projects": list_available_projects(),
        "phase": phase, "phase_text": phase_text,
        "clips": clips, "clips_total": total,
        "vo": vo, "subs": subs,
        "vo_minutes": round(vo_total / 60, 1),
        "eta": eta_seconds(clips, total),
        "overall_percent": overall_pct,
        "overall_eta": overall_eta,
        "assembly_done_chapters": ch_done,
        "assembly_total_chapters": ch_total,
        "batches": batches,
        "assembly_breakdown": breakdown,
        "log": log[-14:],
        "gh": gh_runs(),
        "videos": list_videos(ctx["EXPORT"]),
        "video_jobs": recent_video_jobs(),
        "factory": factory_state(ctx["id"]),
        "thumbnail_pack": thumbnail_pack(ctx["THUMB_DIR"]),
        "scenes": scene_rows(ctx),
        "qa": qa,
        "qa_ok": sum(1 for q in qa if q["ok"]),
        "qa_total": len(qa),
        "now": time.strftime("%H:%M:%S"),
    }


# ── HTTP ────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            return  # Browser refreshed/cancelled polling; not a server failure.

    def _serve_media(self, folder, name, mime, exts):
        safe = os.path.basename(unquote(name))
        if not safe.endswith(exts):
            self.send_error(404)
            return
        path = os.path.join(folder, safe)
        if not os.path.isfile(path):
            self.send_error(404)
            return
        size = os.path.getsize(path)
        rng = self.headers.get("Range")
        start, end, code = 0, size - 1, 200
        if rng:
            m = re.match(r"bytes=(\d*)-(\d*)", rng)
            if m:
                if m.group(1):
                    start = int(m.group(1))
                if m.group(2):
                    end = int(m.group(2))
                end = min(end, size - 1)
                start = min(start, end)
                code = 206
        length = end - start + 1
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        if code == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        remaining = length
        with open(path, "rb") as f:
            f.seek(start)
            while remaining > 0:
                chunk = f.read(min(262144, remaining))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                    return  # Seeking/refreshing cancels the old byte-range request.
                remaining -= len(chunk)

    def do_GET(self):
        u = urlparse(self.path)
        p, q = u.path, parse_qs(u.query)
        ctx = get_project_config()

        if p in ("/", "/dashboard.html"):
            try:
                body = open(HTML, "rb").read()
            except FileNotFoundError:
                self.send_error(404, "dashboard.html tidak ditemukan di repo root")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return

        if p == "/api/projects":
            self._json({"projects": list_available_projects(), "active": _active_project})
            return

        if p == "/api/switch-project":
            pid = q.get("p", ["a044"])[0]
            set_active_project(pid)
            self._json({"ok": True, "active": _active_project})
            return

        if p == "/api/state":
            pid = q.get("p", [None])[0]
            self._json(build_state(pid))
            return

        if p == "/api/scene":
            try:
                n = int(q.get("n", ["1"])[0])
            except ValueError:
                n = 1
            n = max(1, min(ctx["TOTAL_SHOTS"], n))
            self._json(scene_detail(n, ctx))
            return

        if p == "/api/qa":
            self._json({"qa": run_qa(ctx)})
            return

        if p == "/api/video-jobs":
            self._json({"jobs": recent_video_jobs()})
            return

        if p == "/api/thumbnails":
            self._json(thumbnail_pack(ctx["THUMB_DIR"]))
            return

        if p.startswith("/thumbnail/"):
            self._serve_media(ctx["THUMB_DIR"], p[len("/thumbnail/"):], "image/png", (".png",))
            return

        if p.startswith("/image/"):
            self._serve_media(ctx["IMAGES"], p[len("/image/"):], "image/png", (".png",))
            return

        if p.startswith("/preview/"):
            self._serve_media(os.path.join(ctx["EXPORT"], "preview_subtitles"), p[len("/preview/"):], "image/jpeg", (".jpg", ".jpeg", ".png"))
            return

        if p.startswith("/video/"):
            self._serve_media(ctx["EXPORT"], p[len("/video/"):], "video/mp4", (".mp4",))
            return

        if p.startswith("/clip/"):
            self._serve_media(ctx["CLIPS"], p[len("/clip/"):], "video/mp4", (".mp4",))
            return

        if p.startswith("/vo/"):
            self._serve_media(ctx["AUDIO"], p[len("/vo/"):], "audio/wav", (".wav",))
            return

        if p == "/api/open-folder":
            target = q.get("d", ["export"])[0]
            folder = {
                "export": ctx["EXPORT"],
                "clips": ctx["CLIPS"],
                "audio": ctx["AUDIO"],
                "subs": ctx["SUBS"]
            }.get(target, ctx["EXPORT"])
            try:
                os.startfile(folder)  # noqa: S606
                self._json({"ok": True})
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 500)
            return

        self.send_error(404)

    def do_POST(self):
        p = urlparse(self.path).path
        ctx = get_project_config()

        if p in ("/api/thumbnails/regenerate", "/api/youtube/generate"):
            try:
                from youtube_packaging import build_youtube_pack
                pack = build_youtube_pack(ctx["BASE"], generate_flow=False)
                worker = str(Path(__file__).with_name("youtube_packaging.py"))
                try:
                    log_f = open(Path(ctx["BASE"]) / "factory.log", "a", encoding="utf-8")
                    subprocess.Popen([sys.executable, "-u", worker, ctx["BASE"], "--flow"],
                                     cwd=ctx["BASE"], stdout=log_f, stderr=subprocess.STDOUT)
                except Exception:
                    pass
                self._json({"ok": True, "message": "Paket YouTube (Judul, Deskripsi & Thumbnail) berhasil dibuat!", "pack": pack})
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 500)
            return

        if p == "/api/factory/render-mode":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                mode = body.get("mode") or body.get("render_mode")
                if not mode:
                    self._json({"ok": False, "error": "Mode render tidak valid"}, 400)
                    return
                cfg_path = Path(ctx["BASE"]) / "project.json"
                if cfg_path.exists():
                    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                    cfg["output"] = mode
                    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
                self._json({"ok": True, "render_mode": mode, "factory": factory_state(ctx["id"])})
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 500)
            return

        if p == "/api/factory/generate":
            fs = factory_state(ctx["id"])
            if not fs.get("can_generate"):
                self._json({"ok": False, "error": fs.get("button_label", "Tahap belum dapat dijalankan")}, 400)
                return
            worker = str(Path(__file__).with_name("factory_pipeline.py"))
            log_path = Path(ctx["BASE"]) / "factory.log"
            try:
                log_f = open(log_path, "a", encoding="utf-8")
                subprocess.Popen(
                    [sys.executable, "-u", worker, ctx["BASE"], "--stage", fs["next_stage"]],
                    cwd=ctx["BASE"], stdout=log_f, stderr=subprocess.STDOUT,
                )
                self._json({"ok": True, "message": f"Generate {fs['next_stage']} dimulai", "stage": fs["next_stage"]})
            except Exception as exc:
                self._json({"ok": False, "error": str(exc)}, 500)
            return

        if p == "/api/scene/regenerate":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                n = int(body.get("n", 0))
            except (ValueError, TypeError, json.JSONDecodeError):
                self._json({"ok": False, "error": "Nomor shot tidak valid"}, 400)
                return
            if factory_state(ctx["id"]).get("active_stage") == "assets":
                self._json({"ok": False, "error": "Batch Visual Assets sedang berjalan; tunggu selesai."}, 409)
                return
            if not 1 <= n <= ctx["TOTAL_SHOTS"]:
                self._json({"ok": False, "error": f"Shot di luar rentang 1-{ctx['TOTAL_SHOTS']}"}, 400)
                return
            worker = str(Path(__file__).with_name("regen_one.py"))
            try:
                log_f = open(Path(ctx["BASE"]) / "factory.log", "a", encoding="utf-8")
                subprocess.Popen([sys.executable, "-u", worker, ctx["BASE"], str(n)],
                                 cwd=ctx["BASE"], stdout=log_f, stderr=subprocess.STDOUT)
                self._json({"ok": True, "message": f"Regenerate shot_{n:03d} dimulai", "n": n})
            except Exception as exc:
                self._json({"ok": False, "error": str(exc)}, 500)
            return

        if p == "/api/render/start":
            pid = ctx["id"]
            clips_done = count_files(ctx["CLIPS"], ".mp4")
            master_file = os.path.join(ctx["EXPORT"], ctx["MASTER_NAME"])
            if clips_done >= ctx["TOTAL_SHOTS"] and os.path.exists(master_file):
                self._json({"ok": True, "message": "Semua klip dan master film sudah siap!"})
                return

            script_name = "render_local_parallel_a044.py" if pid == "a044" else "render_local_parallel.py"
            script_path = os.path.join(ctx["BASE"], "src", script_name)
            if os.path.exists(script_path):
                cmd = [sys.executable, "-u", script_path]
            else:
                render_py = str(Path(__file__).with_name("render_pipeline.py"))
                cfg_p = Path(ctx["BASE"]) / "project.json"
                mode = "Local 4-Worker Only"
                if cfg_p.exists():
                    try:
                        mode = json.loads(cfg_p.read_text(encoding="utf-8")).get("output", mode)
                    except Exception:
                        pass
                cmd = [sys.executable, "-u", render_py, ctx["BASE"], "--mode", mode]

            try:
                log_f = open(ctx["LOG"], "a", encoding="utf-8")
                subprocess.Popen(cmd, cwd=ctx["BASE"], stdout=log_f, stderr=subprocess.STDOUT)
                self._json({"ok": True, "message": f"Render dimulai untuk {pid} ({mode if not os.path.exists(script_path) else 'script proyek'})"})
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 500)
            return

        if p == "/api/video-jobs":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                job = create_video_job(data)
                set_active_project(Path(job["project_dir"]).name)
                self._json({"ok": True, "job": job}, 201)
            except ValueError as e:
                self._json({"ok": False, "error": str(e)}, 400)
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 500)
            return
        self.send_error(404)


class QuietThreadingHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        exc = sys.exc_info()[1]
        if isinstance(exc, (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)):
            return  # Normal browser disconnect during refresh/seek.
        super().handle_error(request, client_address)


def self_check():
    assert phase_from_log([], 0, 75)[0] == "idle"
    assert phase_from_log(["=== RENDER LOKAL PARALEL"], 5, 75)[0] == "render"
    assert phase_from_log(["LOCAL_RENDER_ALL_DONE"], 75, 75)[0] == "selesai"

    m = re.match(r"bytes=(\d*)-(\d*)", "bytes=100-199")
    assert m and m.group(1) == "100" and m.group(2) == "199"

    # Project-dependent checks: only run when those workspaces exist.
    for pid in ("a044", "render-p404"):
        try:
            c = get_project_config(pid)
        except ValueError:
            print(f"dashboard self-check: skip {pid} (workspace tidak ada)")
            continue
        assert c["TOTAL_SHOTS"] > 0, pid

    print("dashboard self-check: passed all assertions")


if __name__ == "__main__":
    self_check()
    srv = QuietThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Dashboard render: http://127.0.0.1:{PORT}/")
    print("Ctrl+C untuk berhenti.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard dihentikan.")
