# 🎬 Cinematic — Documentary Film Pipeline Tool

Tool pipeline untuk memproduksi film dokumenter sinematik 90-shot secara otomatis:
**TTS Supertonic** (narasi Bahasa Indonesia) → **Faster-Whisper** (subtitle word-level)
→ **Google Flow** (aset visual via Chrome CDP) → **FFmpeg** (render master 1080p).

Repo ini adalah **tool**, bukan judul film. Proyek contoh `a057`
("Kontroversi Ijazah Gibran") disertakan sebagai referensi end-to-end.

## Struktur Proyek

```
cinematic/
├── src/                        # Pipeline scripts
│   ├── cine_paths.py           # Resolusi path portable (SINGLE SOURCE OF TRUTH)
│   ├── factory_pipeline.py     # Orkestrasi stage + dipakai dashboard
│   ├── whisper_compat.py       # Shim av>=14 untuk faster-whisper (otomatis)
│   ├── build_storyboard.py     # Storyboard proyek contoh (90 shot)
│   ├── flow_assets.py          # Generate gambar via Google Flow (Chrome CDP :9222)
│   ├── flow_batch_generator.py # CDP runner (GoogleFlowRunner)
│   ├── flow_thumbnail_generator.py
│   ├── tts_subtitles.py        # Supertonic TTS + subtitle anti-lonely
│   ├── whisper_aligner.py      # Alignment word-level
│   ├── render_continuous_babak.py  # Render master 5 babak + assembly
│   ├── chapter_cards.py        # Kartu babak
│   ├── youtube_packaging.py    # Metadata + thumbnail YouTube
│   ├── style_lock.py           # Style lock visual
│   ├── dashboard.py            # Dashboard HTTP (stdlib, port 5188)
│   └── run_auto_pipeline.py    # Runner end-to-end
├── dashboard.html              # UI dashboard (disajikan dashboard.py)
├── input/                      # outline.md, script.md, storyboard.json, ...
├── script/                     # naskah per-shot (shot_001.txt ...)
├── output/                     # flow_images/, audio_supertonic/, subtitles/, ...
├── assets/                     # fonts, music
├── export/                     # master film, thumbnail, youtube meta
├── project.json                # Konfigurasi + status pipeline proyek
└── requirements.txt
```

## Setup

```bash
# 1. System
sudo apt install ffmpeg

# 2. Python
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# 3. (Opsional) arahkan ke direktori proyek lain
export CINEMATIC_PROJECT_DIR=/path/ke/proyek
export CINEMATIC_PROJECTS_ROOT=/path/ke/kumpulan-proyek  # untuk dashboard
```

Tanpa env var, semua script memakai **repo root** sebagai direktori proyek.

## Menjalankan Pipeline

```bash
cd src

# Per stage (direkomendasikan untuk proyek baru)
python factory_pipeline.py /path/proyek --stage storyboard
python factory_pipeline.py /path/proyek --stage assets      # butuh Chrome CDP :9222 + login Flow
python factory_pipeline.py /path/proyek --stage tts
python factory_pipeline.py /path/proyek --stage render

# Atau otomatis penuh:
python run_auto_pipeline.py /path/proyek

# Atau stage berikutnya sesuai project.json:
python factory_pipeline.py /path/proyek --stage storyboard --next
```

Urutan stage: `outline → script → storyboard → assets → tts → render`.
`outline`/`script` bersifat editorial (susun `input/outline.md`, `input/script.md`).

### Google Flow (aset visual)

`flow_assets.py` terhubung ke tab proyek Flow lewat **Chrome DevTools Protocol**
di `127.0.0.1:9222` (env `CHROME_CDP_PORT`). Buka `flow.google.com/<project>`
di Chrome yang sudah login, lalu jalankan script — generasi dieksekusi di dalam
tab yang terautentikasi (tanpa export cookie).

### Dashboard

```bash
cd src && python dashboard.py   # http://localhost:5188
```

## Catatan Portabilitas

- Semua path mesin-spesifik (`D:/project/...`) sudah diganti `src/cine_paths.py`.
- Kompatibilitas `faster-whisper` + `av>=14` ditangani otomatis oleh
  `src/whisper_compat.py` (tanpa patch site-packages manual).
- Berjalan di Linux dan GitHub Actions (`ubuntu-latest`, CPU-only).
  Render 1080p penuh di CPU lambat — untuk produksi, render di GH Actions.

## Proyek Contoh (a057)

Direktori ini berisi proyek dokumenter yang sudah selesai sebagai contoh
lengkap: `input/`, `script/` (90 shot), `output/subtitles/` (90 SRT),
`project.json`, `STATE.md`. Aset besar (audio WAV, 90 gambar Flow, master MP4)
tidak ikut di-commit — generate ulang dengan pipeline di atas.
