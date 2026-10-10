"""factory_pipeline — stage orchestration for the cinematic documentary tool.

The dashboard imports :func:`next_pending_stage`; it is also the CLI worker
the dashboard spawns::

    python factory_pipeline.py <project_dir> --stage <stage>

Stage order: outline -> script -> storyboard -> assets -> tts -> render.

``outline`` and ``script`` are editorial (LLM-assisted) stages and are not
auto-runnable; the worker reports guidance for them. ``storyboard`` rebuilds
the bundled example storyboard. ``assets`` / ``tts`` / ``render`` run the
generic per-project scripts against ``<project_dir>``.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

STAGES = ["outline", "script", "storyboard", "assets", "tts", "render"]

STAGE_SCRIPTS = {
    # stage: [scripts to run in order, each receiving the project dir]
    "storyboard": ["build_storyboard.py"],
    "assets": ["flow_assets.py"],
    "tts": ["tts_subtitles.py", "whisper_aligner.py"],
    "render": ["render_continuous_babak.py"],
}

NON_AUTOMATED = {
    "outline": "Tahap outline bersifat editorial — susun input/outline.md (5 babak, kronologi, angle investigasi).",
    "script": "Tahap script bersifat editorial — susun input/script.md (naskah narasi per shot).",
}


def next_pending_stage(cfg: dict) -> str | None:
    """First stage in STAGES whose pipeline entry is not 'completed'."""
    status = {item.get("key"): item.get("status") for item in cfg.get("pipeline", [])}
    for stage in STAGES:
        if status.get(stage) != "completed":
            return stage
    return None


def _run(script: str, project: Path, src_dir: Path) -> int:
    cmd = [sys.executable, "-u", str(src_dir / script), str(project)]
    print(f"$ {' '.join(cmd)}", flush=True)
    proc = subprocess.Popen(cmd, cwd=str(src_dir))
    return proc.wait()


def run_stage(stage: str, project: Path) -> int:
    src_dir = Path(__file__).resolve().parent
    if stage in NON_AUTOMATED:
        print(NON_AUTOMATED[stage])
        print("Setelah berkas input siap, tandai stage completed di project.json lalu lanjutkan.")
        return 2
    scripts = STAGE_SCRIPTS.get(stage)
    if not scripts:
        print(f"Stage tidak dikenal: {stage} (pilihan: {', '.join(STAGES)})")
        return 2
    for script in scripts:
        rc = _run(script, project, src_dir)
        if rc != 0:
            print(f"Stage '{stage}' berhenti di {script} (exit {rc})")
            return rc
    _mark_completed(project, stage)
    print(f"✓ Stage '{stage}' selesai.")
    return 0


def _mark_completed(project: Path, stage: str) -> None:
    cfg_path = project / "project.json"
    if not cfg_path.exists():
        return
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    for item in cfg.get("pipeline", []):
        if item.get("key") == stage:
            item["status"] = "completed"
    cfg["active_stage"] = stage
    cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Cinematic pipeline stage worker")
    ap.add_argument("project", help="Project directory")
    ap.add_argument("--stage", required=True, choices=STAGES, help="Stage to run")
    ap.add_argument("--next", action="store_true",
                    help="Run the next pending stage from project.json instead")
    args = ap.parse_args()
    project = Path(args.project).resolve()
    stage = args.stage
    if args.next:
        cfg_path = project / "project.json"
        if not cfg_path.exists():
            print("project.json tidak ditemukan.")
            return 2
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        stage = next_pending_stage(cfg)
        if not stage:
            print("Semua stage sudah completed.")
            return 0
        print(f"Next pending stage: {stage}")
    return run_stage(stage, project)


if __name__ == "__main__":
    sys.exit(main())
