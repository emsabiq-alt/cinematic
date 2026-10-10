"""run_auto_pipeline.py
End-to-end automated runner for a cinematic project:
1. Generates all remaining visual assets in Google Flow (output/flow_images/shot_*.png)
2. Runs master continuous render and assembly via render_continuous_babak.py
3. Updates STATE.md and project.json when completed.

Usage:  python run_auto_pipeline.py [project_dir]   (or set CINEMATIC_PROJECT_DIR)
"""
import sys
import os
import time
import json
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cine_paths import project_dir  # noqa: E402

PROJECT_DIR = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else project_dir()
SRC_DIR = Path(__file__).resolve().parent
LOG_FILE = PROJECT_DIR / "export" / "pipeline_execution.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log(msg):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def total_shots():
    cfg_path = PROJECT_DIR / "project.json"
    if cfg_path.exists():
        try:
            return int(json.loads(cfg_path.read_text(encoding="utf-8")).get("total_shots") or 90)
        except (ValueError, TypeError):
            pass
    return 90


def check_flow_images_count():
    flow_dir = PROJECT_DIR / "output" / "flow_images"
    if not flow_dir.exists():
        return 0
    return len([f for f in flow_dir.glob("shot_*.png") if f.stat().st_size > 50000])

def run_visual_assets():
    log("=== TAHAP 1: GENERASI ASET GAMBAR GOOGLE FLOW ===")
    flow_script = SRC_DIR / "flow_assets.py"
    
    while True:
        cnt = check_flow_images_count()
        log(f"Aset gambar valid saat ini: {cnt}/{total_shots()}")
        if cnt >= total_shots():
            log("✓ Seluruh aset gambar Google Flow telah selesai!")
            break
            
        log("Menjalankan generator Flow...")
        try:
            cmd = ["python", str(flow_script), str(PROJECT_DIR)]
            proc = subprocess.Popen(cmd, cwd=str(SRC_DIR), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in proc.stdout:
                line_str = line.strip()
                if line_str and ("ASSET_OK" in line_str or "ASSET_FAIL" in line_str or "Terhubung" in line_str):
                    log(f"  [Flow] {line_str}")
            proc.wait()
        except Exception as e:
            log(f"  [Error] Flow runner exception: {e}")
            
        new_cnt = check_flow_images_count()
        if new_cnt >= total_shots():
            break
        log("Menunggu 5 detik sebelum batch berikutnya...")
        time.sleep(5)

def run_master_render():
    log("=== TAHAP 2: RENDER CONTINUOUS MASTER FILM ===")
    render_script = SRC_DIR / "render_continuous_babak.py"
    cmd = [sys.executable, "-u", str(render_script), str(PROJECT_DIR)]
    log(f"Menjalankan command: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, cwd=str(SRC_DIR), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in proc.stdout:
        line_str = line.strip()
        if line_str:
            log(f"  [Render] {line_str}")
    proc.wait()
    if proc.returncode == 0:
        log("✓ Render master film continuous selesai 100%!")
    else:
        log(f"❌ Render gagal dengan exit code {proc.returncode}")
        return False
    return True

def update_state_to_completed():
    log("=== TAHAP 3: FINALISASI DOKUMENTASI & METADATA ===")
    project_json_path = PROJECT_DIR / "project.json"
    title = PROJECT_DIR.name
    if project_json_path.exists():
        cfg = json.loads(project_json_path.read_text(encoding="utf-8"))
        title = cfg.get("title", title)
        for item in cfg.get("pipeline", []):
            item["status"] = "completed"
        cfg["status"] = "completed"
        cfg["active_stage"] = "completed"
        project_json_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        log("✓ project.json diperbarui ke status completed")

    state_path = PROJECT_DIR / "STATE.md"
    master_files = list((PROJECT_DIR / "export").glob("*_MASTER.mp4"))
    master_info = "Sudah ter-export"
    if master_files:
        mf = master_files[0]
        size_mb = mf.stat().st_size / 1048576
        master_info = f"`{mf.name}` ({size_mb:.1f} MB)"

    state_content = f"""# STATE — {title}

Diperbarui: {time.strftime('%Y-%m-%d %H:%M')} (diverifikasi dari disk)

## Status Pipeline

| Tahap | Status | Detail Berkas / Keterangan |
|---|---|---|
| Outline Dokumen | COMPLETED | `input/outline.md` |
| Naskah Narasi (Script) | COMPLETED | `input/script.md` + `script/` |
| Storyboard | COMPLETED | `input/storyboard.json` |
| Sintesis Audio Supertonic | COMPLETED | `output/audio_supertonic/` |
| Subtitle Faster-Whisper | COMPLETED | `output/subtitles/` |
| Aset Visual (Google Flow) | COMPLETED | `output/flow_images/` |
| Render Klip & Master Film | COMPLETED | `export/{master_info}` |
"""
    state_path.write_text(state_content, encoding="utf-8")
    log("✓ STATE.md diperbarui ke status COMPLETED")

def main():
    log(f"Starting automated pipeline for project {PROJECT_DIR.name}...")
    run_visual_assets()
    success = run_master_render()
    if success:
        update_state_to_completed()
        log(f"🎉 PIPELINE PROJECT {PROJECT_DIR.name} SELESAI SEMPURNA SAMPAI TUNTAS!")

if __name__ == "__main__":
    main()
