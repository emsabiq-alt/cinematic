"""flow_video_generator.py — Google Flow batch VIDEO generator (via Chrome CDP).

Pendamping flow_batch_generator.py untuk format hybrid (sv011+): shot yang
ditandai media="video" di storyboard digenerate sebagai klip video Flow
(720p, 16:9, 10 detik) lewat UI Flow yang sama (Chrome khusus port 9222).

Model: Omni 1.1 Flash (15 kredit/klip). DIPILIH 2026-10-19 setelah uji
banding: Veo 3.1 - Fast di UI Flow terkunci 8 detik (radio resolusi/durasi
tidak ada di panelnya) dan frame-nya penuh border film-strip; Omni memberi
durasi 10 detik PERSIS seperti permintaan user, kualitas setara/lebih
bersih, dan lebih murah (Veo Fast 20 kredit/8 dtk).

Pelajaran penting dari pembangunan 2026-10-19:
- Pilihan model HARUS diklik dengan mouse event CDP asli; el.click() DOM
  tidak memicu handler Angular Flow (menu model tidak bereaksi).
- Urutan setelan berpengaruh: atur model dulu, durasi TERAKHIR, lalu
  verifikasi ringkasan panel ("Video · 720p · 10 dtk") sebelum generate.
- Klip selesai ditandai poster flow-content baru; URL MP4 didapat dengan
  membuka kartu aset lalu membaca <video>.currentSrc di viewer.
- Generate video LAMA (1-3 menit). Instruksi user: tunggu tiap video sampai
  benar-benar selesai; timeout per video 420 detik, jangan di-skip.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cine_paths import project_dir  # noqa: E402
from flow_batch_generator import GoogleFlowRunner  # noqa: E402

BASE = project_dir()
VIDEO_DIR = BASE / "output" / "flow_videos"
STORY_PATH = BASE / "input" / "storyboard.json"
LOG_FILE = BASE / "flow_video_generator.log"

VIDEO_DIR.mkdir(parents=True, exist_ok=True)
(BASE / "output").mkdir(parents=True, exist_ok=True)

MODEL_LABEL = "Omni 1.1 Flash"
DURATION_LABEL = "10 dtk"
GEN_TIMEOUT = 420  # detik; user: tunggu, jangan buru-buru


def _verify_video(path):
    """True bila file MP4 utuh: ffprobe membaca durasi >= 7 detik."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip()) >= 7.0
    except Exception:
        return False


def _download_video(url, out_path, timeout=120, tries=5):
    """Unduh MP4 dengan curl resumable (urllib terbukti terpotong untuk
    flow-content lewat proxy ini — pola sama seperti unduhan gambar)."""
    import shutil
    curl_bin = shutil.which("curl")
    if not curl_bin:
        raise RuntimeError("curl tidak ditemukan")
    last_exc = None
    for attempt in range(tries):
        cmd = [curl_bin, "-sS", "-L", "--max-time", str(timeout),
               "-C", "-", "-A", "Mozilla/5.0",
               "-e", "https://flow.google.com/",
               "-o", str(out_path), url]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=timeout + 15)
        except Exception as e:  # noqa: BLE001
            last_exc = e
            time.sleep(4 * (attempt + 1))
            continue
        if proc.returncode == 33:  # server tak dukung resume; mulai ulang
            try:
                out_path.unlink()
            except OSError:
                pass
            time.sleep(4 * (attempt + 1))
            continue
        if out_path.exists() and _verify_video(out_path):
            return out_path.stat().st_size
        last_exc = IOError(f"unduhan belum utuh (rc={proc.returncode})")
        time.sleep(4 * (attempt + 1))
    raise IOError(f"Unduhan video gagal setelah {tries} upaya: {last_exc}")


class FlowVideoRunner(GoogleFlowRunner):
    # --- util mouse CDP (el.click() DOM tidak cukup untuk UI Flow) ---
    def _mouse_click(self, x, y):
        self._send("Input.dispatchMouseEvent",
                   {"type": "mousePressed", "x": x, "y": y,
                    "button": "left", "clickCount": 1})
        self._send("Input.dispatchMouseEvent",
                   {"type": "mouseReleased", "x": x, "y": y,
                    "button": "left", "clickCount": 1})

    def _click_radio(self, label_regex):
        # Radio di panel setelan merespons el.click() DOM (terbukti pada
        # konfigurasi manual 2026-10-19); klik mouse koordinat justru
        # meleset untuk radio yang posisinya rendah di panel (720p/10 dtk).
        return self.evaluate_js(f"""
        (() => {{
            const el = Array.from(document.querySelectorAll('[role="radio"]'))
                .find(x => new RegExp({json.dumps(label_regex)})
                    .test(x.innerText || ''));
            if (!el) return false;
            el.scrollIntoView({{block: 'center'}});
            el.click();
            return true;
        }})()
        """)

    def _open_settings(self):
        self.evaluate_js("""
        (() => {
            const b = Array.from(document.querySelectorAll('button'))
                .find(x => /Pemicu setelan/.test(
                    (x.getAttribute('aria-label') || '') + (x.innerText || '')));
            if (b) b.click();
            return !!b;
        })()
        """)
        time.sleep(2)

    def _close_settings(self):
        self._send("Input.dispatchKeyEvent",
                   {"type": "rawKeyDown", "windowsVirtualKeyCode": 27,
                    "unmodifiedText": "", "text": ""})
        self._send("Input.dispatchKeyEvent",
                   {"type": "keyUp", "windowsVirtualKeyCode": 27,
                    "unmodifiedText": "", "text": ""})
        time.sleep(0.5)

    def ensure_video_settings(self):
        """Atur panel ke Video/Veo Fast/720p/16:9/10 dtk dan verifikasi.

        Diulang sampai 3x: panel Flow kadang me-render ulang di tengah
        pengaturan sehingga sebagian klik hilang (kasus 2026-10-19: 720p
        dan 10 dtk tidak tercentang pada percobaan pertama).
        """
        last_state = None
        for attempt in range(1, 4):
            self._open_settings()
            # Mode Video + sub-mode Bahan + aspek 16:9 + resolusi 720p
            self._click_radio("Video")
            time.sleep(1)
            self._click_radio("Bahan")
            time.sleep(0.5)
            self._click_radio("16:9")
            time.sleep(0.5)
            self._click_radio("720p")
            time.sleep(0.5)
            # Model: buka pemilih lalu klik opsi dengan mouse asli
            self.evaluate_js("""
            (() => {
                const b = Array.from(document.querySelectorAll('button'))
                    .find(x => /Omni|Veo/.test(x.innerText || '') &&
                               /arrow_drop_down/.test(x.innerText || ''));
                if (b) b.click();
                return !!b;
            })()
            """)
            time.sleep(2)
            rect = self.evaluate_js(f"""
            (() => {{
                const cands = Array.from(document.querySelectorAll('*'))
                    .filter(x => {{
                        const t = (x.innerText || '').replace(/\\s+/g, ' ');
                        return t.includes({json.dumps(MODEL_LABEL)}) &&
                               x.offsetParent !== null;
                    }});
                if (!cands.length) return null;
                cands.sort((a, b) => (a.innerText || '').length -
                                     (b.innerText || '').length);
                cands[0].scrollIntoView({{block: 'center'}});
                const r = cands[0].getBoundingClientRect();
                return {{x: r.left + r.width / 2, y: r.top + r.height / 2}};
            }})()
            """)
            if rect:
                self._mouse_click(rect["x"], rect["y"])
                time.sleep(2)
            # Durasi TERAKHIR (pemilihan model bisa meresetnya)
            self._click_radio(DURATION_LABEL)
            time.sleep(1)
            checked = self.evaluate_js("""
            (() => Array.from(document.querySelectorAll('[role="radio"]'))
                .filter(e => e.getAttribute('aria-checked') === 'true')
                .map(e => (e.innerText || '').trim()
                    .replace(/\\s+/g, ' ')))()
            """) or []
            model = self.evaluate_js("""
            (() => Array.from(document.querySelectorAll('button'))
                .map(b => (b.innerText || '').trim())
                .find(t => /Veo|Omni/.test(t)) || '')()
            """) or ""
            ok = (any("Video" in c for c in checked)
                  and any("720p" in c for c in checked)
                  and any(DURATION_LABEL in c for c in checked)
                  and MODEL_LABEL in model)
            print(f"  Setelan (percobaan {attempt}): checked={checked} "
                  f"model={model!r} -> {'OK' if ok else 'BELUM COCOK'}",
                  flush=True)
            self._close_settings()
            if ok:
                return True
            last_state = (checked, model)
            time.sleep(2)
        raise RuntimeError(
            f"Setelan Flow tidak cocok setelah 3 percobaan: {last_state}")

    def _poster_urls(self):
        return self.evaluate_js("""
        (() => Array.from(document.images)
            .map(i => i.src)
            .filter(Boolean)
            .filter(s => s.includes('flow-content.google/image/')))()
        """) or []

    def _grid_url(self):
        url = self.evaluate_js("(() => location.href)()") or ""
        return url.split("/edit/")[0]

    def _wait_editor(self, timeout=60):
        """Tunggu sampai editor prompt grid proyek muncul lagi."""
        start_t = time.time()
        while time.time() - start_t < timeout:
            ok = self.evaluate_js("""
            (() => !!document.querySelector(
                '.ProseMirror[contenteditable="true"]'))()
            """)
            if ok:
                return True
            time.sleep(3)
        return False

    def _back_to_grid(self):
        """Keluar dari halaman /edit/<aset> kembali ke grid proyek.

        Pelajaran 19 Okt 2026: klik kartu aset membuka halaman /edit/<id>
        (bukan overlay); Escape TIDAK keluar dari sana — generator batch
        pertama macet total setelah video pertama karena halaman tidak
        pernah kembali ke grid. Navigasi eksplisit + tunggu editor.
        """
        url = self.evaluate_js("(() => location.href)()") or ""
        if "/edit/" not in url:
            return True
        grid = url.split("/edit/")[0]
        self._send("Page.navigate", {"url": grid})
        return self._wait_editor(90)

    def generate_video_one(self, prompt, out_mp4, timeout=GEN_TIMEOUT):
        if not self.ws:
            self.connect()
        # Pastikan mulai dari grid proyek (bukan halaman /edit/ sisa shot
        # sebelumnya) — tanpa editor, generate pasti gagal.
        if not self._back_to_grid():
            raise RuntimeError(
                "Tidak bisa kembali ke grid Flow (editor tidak muncul).")
        before = set(self._poster_urls())

        # Fokus editor, bersihkan, ketik prompt
        self.evaluate_js("""
        (() => {
            const e = document.querySelector(
                '.ProseMirror[contenteditable="true"]');
            if (e) {
                e.focus();
                document.execCommand('selectAll', false, null);
                document.execCommand('delete', false, null);
                return true;
            }
            return false;
        })()
        """)
        time.sleep(0.3)
        self._send("Input.insertText", {"text": prompt})
        time.sleep(0.5)

        coords = self.evaluate_js("""
        (() => {
            const b = Array.from(document.querySelectorAll('button'))
                .find(x => /Mulai pembuatan|Start generation/i.test(
                    x.getAttribute('aria-label') || x.innerText || ''));
            if (!b || b.disabled) return null;
            const r = b.getBoundingClientRect();
            return {x: r.left + r.width / 2, y: r.top + r.height / 2};
        })()
        """)
        if not coords:
            raise RuntimeError("Tombol 'Mulai pembuatan' tidak ditemukan/aktif.")
        self._mouse_click(coords["x"], coords["y"])
        print("  → Prompt video terkirim. Menunggu klip selesai "
              "(bisa 1-3 menit)...", flush=True)

        # Tunggu poster aset baru muncul (= generasi selesai di server)
        start_t = time.time()
        new_poster = None
        while time.time() - start_t < timeout:
            time.sleep(5)
            diff = [u for u in self._poster_urls() if u not in before]
            if diff:
                new_poster = diff[0]
                break
        if not new_poster:
            raise TimeoutError(
                f"Flow tidak menyelesaikan video dalam {timeout}s.")
        print(f"  ✓ Generasi selesai dalam "
              f"{int(time.time() - start_t)}s. Mengambil MP4...", flush=True)

        # Buka kartu aset -> baca <video> src di viewer -> unduh
        asset_id = new_poster.split("/image/")[1].split("?")[0]
        rect = self.evaluate_js(f"""
        (() => {{
            const img = Array.from(document.querySelectorAll('img'))
                .find(i => i.src.includes({json.dumps(asset_id)}));
            if (!img) return null;
            const r = img.getBoundingClientRect();
            return {{x: r.left + r.width / 2, y: r.top + r.height / 2}};
        }})()
        """)
        if not rect:
            raise RuntimeError("Kartu aset video tidak ditemukan di grid.")
        self._mouse_click(rect["x"], rect["y"])
        video_url = None
        for _ in range(12):
            time.sleep(2)
            video_url = self.evaluate_js("""
            (() => {
                const v = document.querySelector('video');
                return v ? (v.currentSrc || v.src) : null;
            })()
            """)
            if video_url and "/video/" in video_url:
                break
        if not video_url:
            self._back_to_grid()
            raise RuntimeError("URL video tidak terbaca dari viewer Flow.")
        # WAJIB kembali ke grid sebelum shot berikutnya (halaman /edit/
        # tidak punya editor/grid — batch pertama macet di sini).
        self._back_to_grid()
        _download_video(video_url.replace("&amp;", "&"), out_mp4)
        return str(out_mp4)


def run_batch(delay_between=10):
    data = json.loads(STORY_PATH.read_text(encoding="utf-8"))
    shots = [s for s in data["shots"] if s.get("media") == "video"]

    runner = FlowVideoRunner()
    runner.connect()
    runner.ensure_video_settings()

    print(f"\n=== GENERASI VIDEO FLOW ({len(shots)} shot video) ===", flush=True)
    try:
        for i, s in enumerate(shots, 1):
            sid = s["id"]
            out_mp4 = VIDEO_DIR / f"{sid}.mp4"
            prompt = s.get("video_prompt") or s["visual_prompt"]
            print(f"\n[{i}/{len(shots)}] {sid} (Babak {s['chapter']})", flush=True)
            if out_mp4.exists() and _verify_video(out_mp4):
                print(f"  ✓ Video sudah ada & valid: {out_mp4.name} "
                      f"({out_mp4.stat().st_size/1048576:.1f} MB)", flush=True)
                continue
            try:
                runner.generate_video_one(prompt, out_mp4)
                print(f"  ✓ Berhasil: {out_mp4.name} "
                      f"({out_mp4.stat().st_size/1048576:.1f} MB)", flush=True)
            except Exception as e:
                print(f"  ✗ Gagal: {e}", flush=True)
                time.sleep(6)
            if i < len(shots):
                print(f"  ⏳ Jeda {delay_between}s...")
                time.sleep(delay_between)
    finally:
        runner.close()
    print("\n=== GENERASI VIDEO SELESAI ===", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Flow videos for shots marked media=video")
    parser.add_argument("project", nargs="?",
                        help="Project directory (or CINEMATIC_PROJECT_DIR)")
    parser.add_argument("--delay", type=int, default=10)
    args = parser.parse_args()
    if args.project:
        os.environ["CINEMATIC_PROJECT_DIR"] = args.project
        BASE = project_dir()
        VIDEO_DIR = BASE / "output" / "flow_videos"
        STORY_PATH = BASE / "input" / "storyboard.json"
        LOG_FILE = BASE / "flow_video_generator.log"
        VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        globals().update(BASE=BASE, VIDEO_DIR=VIDEO_DIR,
                         STORY_PATH=STORY_PATH, LOG_FILE=LOG_FILE)
    run_batch(args.delay)
