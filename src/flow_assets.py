"""Visual assets stage: drive Google Flow (CDP) for any Video Factory workspace.

Reuses the proven runner from a044 instead of reimplementing CDP plumbing.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

try:
    from flow_batch_generator import GoogleFlowRunner  # noqa: E402
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from flow_batch_generator import GoogleFlowRunner  # noqa: E402

MIN_IMAGE_BYTES = 50000

from style_lock import CONFLICTS as _CONFLICTS  # noqa: E402
from style_lock import STYLE_LOCK, STYLE_PREFIXES  # noqa: E402

# Flow project URLs carry an optional /u/N/ account segment when several
# Google accounts are signed in; match both shapes.
_FLOW_PROJECT_RE = re.compile(r"^https://flow\.google\.com/(u/\d+/)?project/")


def is_flow_project_url(url):
    return bool(_FLOW_PROJECT_RE.match(url or ""))


def connect_runner():
    """GoogleFlowRunner bound to whichever Flow project tab is open."""
    import urllib.request
    import websocket

    with urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=6) as r:
        tabs = json.loads(r.read().decode())
    tab = next((t for t in tabs if is_flow_project_url(t.get("url", ""))), None)
    if not tab:
        raise RuntimeError(
            "Tab project Google Flow tidak ditemukan di CDP 9222. "
            "Buka project Flow (flow.google.com/.../project/...) lalu ulangi."
        )
    runner = GoogleFlowRunner()
    runner.ws = websocket.create_connection(
        tab["webSocketDebuggerUrl"], suppress_origin=True, timeout=30)
    print(f"✓ Terhubung ke Flow: {tab.get('url', '')[:70]}", flush=True)
    return runner

def build_prompt(visual_prompt, story_data=None):
    """Content from the storyboard + one locked style clause.
    If the project specifies a modern/cinematic 35mm style, use it directly without forcing sepia etching.
    """
    text = (visual_prompt or "").strip()
    if text.startswith("Cinematic 35mm film still") or (story_data and "cinematic" in str(story_data.get("style", "")).lower()):
        return text

    low = text.lower()
    for phrase in _CONFLICTS:
        idx = low.find(phrase)
        while idx != -1:
            text = text[:idx] + text[idx + len(phrase):]
            low = text.lower()
            idx = low.find(phrase)
    # Drop style boilerplate the model already wrote; the lock replaces it.
    for phrase in STYLE_PREFIXES:
        if low.startswith(phrase):
            text = text[len(phrase):].lstrip(" ,:-")
            break
    text = " ".join(text.split())
    text = text.lstrip(" ,:-")
    if text[:3].lower() == "of ":
        text = text[3:]
    text = text.lstrip(" ,:-")
    if text:
        text = text[0].upper() + text[1:]
    if text and not text.endswith((".", "!", "?")):
        text += "."
    return text + STYLE_LOCK


def _paths(project):
    project = Path(project).resolve()
    return project, project / "input" / "storyboard.json", project / "output" / "flow_images"


def pending_shots(project):
    """Shots whose image is missing or too small to be a real render."""
    _, story_path, flow_dir = _paths(project)
    shots = json.loads(story_path.read_text(encoding="utf-8"))["shots"]
    out = []
    for s in shots:
        png = flow_dir / f"{s['id']}.png"
        if not png.exists() or png.stat().st_size <= MIN_IMAGE_BYTES:
            out.append(s)
    return out


def regenerate_shot(project, n):
    """Force-regenerate one shot with the locked style, overwriting the old PNG."""
    project, story_path, flow_dir = _paths(project)
    flow_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(story_path.read_text(encoding="utf-8"))
    shots = data["shots"]
    if not isinstance(n, int) or n < 1 or n > len(shots):
        raise ValueError(f"Nomor shot di luar rentang 1-{len(shots)}: {n}")

    shot = shots[n - 1]
    png = flow_dir / f"{shot['id']}.png"
    runner = connect_runner()
    try:
        runner.generate_one(build_prompt(shot["visual_prompt"], data), png)
    finally:
        runner.close()
    _write_mapping(project, data, shots, flow_dir)
    size = png.stat().st_size if png.exists() else 0
    print(f"REGEN_OK {shot['id']} {size} bytes", flush=True)
    return {"shot_id": shot["id"], "bytes": size}


def run_assets(project, delay=14, limit=None):
    project, story_path, flow_dir = _paths(project)
    flow_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(story_path.read_text(encoding="utf-8"))
    shots = data["shots"]
    todo = pending_shots(project)
    if limit:
        todo = todo[:limit]

    generated, failed = 0, []
    if not todo:
        _write_mapping(project, data, shots, flow_dir)
        return {"generated": 0, "failed": [], "total": len(shots)}

    runner = connect_runner()
    try:
        for i, s in enumerate(todo):
            png = flow_dir / f"{s['id']}.png"
            # Satu koneksi WS tidak selamat untuk 90 shot: Flow/Chromium memutus
            # setelah puluhan menit (WinError 10053) dan dulu SEMUA shot sisanya
            # gagal berurutan. Sambung ulang lalu ulangi shot yang sama.
            for attempt in range(3):
                try:
                    runner.generate_one(build_prompt(s["visual_prompt"], data), png)
                    generated += 1
                    print(f"ASSET_OK {s['id']} {png.stat().st_size} bytes", flush=True)
                    break
                except Exception as exc:
                    if attempt == 2:
                        failed.append(s["id"])
                        print(f"ASSET_FAIL {s['id']}: {exc}", flush=True)
                        break
                    print(f"ASSET_RETRY {s['id']} ({exc}); menyambung ulang ke Flow...",
                          flush=True)
                    try:
                        runner.close()
                    except Exception:
                        pass
                    time.sleep(5 * (attempt + 1))
                    try:
                        runner = connect_runner()
                    except Exception as reconn:
                        print(f"  reconnect gagal: {reconn}", flush=True)
                        time.sleep(15)
            _write_mapping(project, data, shots, flow_dir)
            if delay and i < len(todo) - 1:
                time.sleep(delay)
    finally:
        try:
            runner.close()
        except Exception:
            pass

    if failed:
        raise RuntimeError(f"{len(failed)} shot gagal digenerate: {', '.join(failed[:5])}")
    return {"generated": generated, "failed": failed, "total": len(shots)}


def _write_mapping(project, data, shots, flow_dir):
    records = []
    for s in shots:
        png = flow_dir / f"{s['id']}.png"
        ready = png.exists() and png.stat().st_size > MIN_IMAGE_BYTES
        records.append({
            "shot_id": s["id"], "chapter": s.get("chapter"),
            "narration": s.get("narration", ""),
            "image_file": str(png).replace("\\", "/"),
            "status": "ready" if ready else "pending",
        })
    (Path(project) / "output" / "flow_mapping.json").write_text(
        json.dumps({"title": data.get("title", ""), "total_shots": len(shots), "records": records},
                   ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--delay", type=int, default=14)
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    r = run_assets(a.project, a.delay, a.limit)
    print(f"ASSETS_DONE generated={r['generated']} total={r['total']}", flush=True)
