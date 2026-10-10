"""cine_paths — central, portable path resolution for the cinematic pipeline.

Every script resolves locations through this module instead of hardcoding
machine-specific paths (e.g. ``D:/project/...``).

Resolution order:
  1. ``CINEMATIC_PROJECT_DIR`` env var — the active documentary project dir.
  2. The repository root itself (single-project checkout layout).

For multi-project dashboards:
  - ``CINEMATIC_PROJECTS_ROOT`` env var, else the repo's parent directory.
"""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
ASSETS_DIR = REPO_ROOT / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
MUSIC_DIR = ASSETS_DIR / "music"
INPUT_DIR = REPO_ROOT / "input"
OUTPUT_DIR = REPO_ROOT / "output"
SCRIPT_DIR = REPO_ROOT / "script"
EXPORT_DIR = REPO_ROOT / "export"


def project_dir() -> Path:
    """Active project directory (defaults to the repo root)."""
    return Path(os.environ.get("CINEMATIC_PROJECT_DIR", str(REPO_ROOT))).resolve()


def projects_root() -> Path:
    """Root containing multiple project directories (for the dashboard)."""
    return Path(os.environ.get("CINEMATIC_PROJECTS_ROOT",
                               str(REPO_ROOT.parent))).resolve()


def ensure_layout(project: Path | None = None) -> Path:
    """Create the standard project directory layout. Returns the project dir."""
    p = (project or project_dir()).resolve()
    for sub in ("input", "output", "output/flow_images", "output/audio_supertonic",
                "output/subtitles", "output/rendered_clips", "script", "export"):
        (p / sub).mkdir(parents=True, exist_ok=True)
    return p


def find_font(*names: str) -> Path | None:
    """First existing font: repo assets/fonts, then common system locations."""
    candidates = [FONTS_DIR / n for n in names]
    candidates += [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return None
