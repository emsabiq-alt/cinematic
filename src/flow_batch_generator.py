"""flow_batch_generator.py — Google Flow batch image generator (via Chrome CDP).

Features:
- Connects to Chrome DevTools Protocol (default port 9222, env CHROME_CDP_PORT).
- Drives generation inside an authenticated flow.google.com project tab.
- Detects new images dynamically (flow.google.com/asb and flow-content.google).
- Auto-crops edge borders if needed and resizes to 1920x1080 Full-Bleed 16:9.
- Progress tracking and resuming capability (skips existing images > 50KB).

Project layout is resolved from the ``project`` argument (or CINEMATIC_PROJECT_DIR);
storyboard is read from ``<project>/input/storyboard.json``.
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import websocket
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cine_paths import project_dir  # noqa: E402

CDP_PORT = int(os.environ.get("CHROME_CDP_PORT", 9222))
CDP_BASE = f"http://127.0.0.1:{CDP_PORT}"

BASE = project_dir()
FLOW_DIR = BASE / "output" / "flow_images"
STORY_PATH = BASE / "input" / "storyboard.json"
MAPPING_JSON = BASE / "output" / "flow_mapping.json"
LOG_FILE = BASE / "flow_generator.log"

FLOW_DIR.mkdir(parents=True, exist_ok=True)
(BASE / "output").mkdir(parents=True, exist_ok=True)


def _download_resumable(url, out_path, timeout=40, tries=5):
    """Unduh URL gambar dengan toleransi koneksi terputus di tengah jalan.

    Jalur egress (proxy TLS-inspecting) rutin memutus respons biner besar di
    tengah transfer (IncompleteRead). Daripada membuang hasil parsial lalu
    meregenerasi gambar baru di Flow (boros kuota), lanjutkan dengan HTTP
    Range dari byte terakhir yang sudah tersimpan.

    Setelah unduhan selesai, verifikasi integritas: bandingkan dengan
    Content-Length (bila server memberikannya) dan cek magic bytes
    (PNG/JPEG). File yang gagal verifikasi dihapus dan diunduh ulang dari
    awal — file parsial TIDAK BOLEH lolos sebagai "selesai".
    """
    def _verify(path):
        """Return True jika file adalah gambar utuh (PNG/JPEG)."""
        try:
            data = path.read_bytes()[:8]
        except OSError:
            return False
        if len(data) < 8:
            return False
        is_png = data[:8] == b"\x89PNG\r\n\x1a\n"
        is_jpeg = data[:2] == b"\xff\xd8"
        if not (is_png or is_jpeg):
            return False
        # Untuk JPEG, pastikan end-of-image marker ada di akhir file.
        if is_jpeg:
            try:
                tail = path.read_bytes()[-2:]
            except OSError:
                return False
            if tail != b"\xff\xd9":
                return False
        return True

    base_headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://flow.google.com/"}
    last_exc = None
    for attempt in range(tries):
        have = out_path.stat().st_size if out_path.exists() else 0
        headers = dict(base_headers)
        if have > 0:
            headers["Range"] = f"bytes={have}-"
        req = urllib.request.Request(url, headers=headers)
        expected_total = None
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                if have > 0 and r.status == 200:
                    # Server mengabaikan Range: mulai lagi dari byte 0.
                    have = 0
                # Content-Length untuk respons 206 adalah sisa bytes;
                # total ekspektasi = have + content-length.
                clen = r.headers.get("Content-Length")
                if clen and clen.isdigit():
                    expected_total = have + int(clen)
                mode = "ab" if have > 0 else "wb"
                with open(out_path, mode) as f:
                    while True:
                        chunk = r.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        have += len(chunk)
            # Verifikasi integritas setelah transfer selesai.
            final_size = out_path.stat().st_size if out_path.exists() else 0
            if expected_total and final_size != expected_total:
                raise IOError(
                    f"Ukuran tidak cocok: dapat {final_size}, harap {expected_total} "
                    f"(transfer terpotong)"
                )
            if not _verify(out_path):
                raise IOError("File bukan gambar utuh (magic bytes / EOF marker salah)")
            return final_size
        except Exception as e:  # noqa: BLE001 - resume on any transport error
            last_exc = e
            print(f"  → Unduhan bermasalah ({have} bytes: {e}); menyambung...",
                  flush=True)
            # Hapus file parsial yang gagal verifikasi agar retry mulai bersih
            # bila server tidak mendukung Range dengan benar.
            try:
                if out_path.exists() and not _verify(out_path):
                    out_path.unlink()
            except OSError:
                pass
            time.sleep(4 * (attempt + 1))
    raise IOError(f"Unduhan gagal setelah {tries} upaya: {last_exc}")


class GoogleFlowRunner:
    def __init__(self, port=CDP_PORT):
        self.port = port
        self.ws = None
        self.msg_id = 0

    def connect(self):
        with urllib.request.urlopen(f"{CDP_BASE}/json", timeout=6) as resp:
            tabs = json.loads(resp.read().decode())
        flow_tab = next((t for t in tabs if "flow.google.com/project" in t.get("url", "")), None)
        if not flow_tab:
            flow_tab = next((t for t in tabs if "flow.google.com" in t.get("url", "")), None)
        if not flow_tab:
            raise RuntimeError("Tab Google Flow tidak ditemukan pada port 9222. Pastikan Chrome aktif di flow.google.com.")

        self.ws = websocket.create_connection(flow_tab["webSocketDebuggerUrl"], suppress_origin=True, timeout=30)
        print(f"✓ Terhubung ke Google Flow: {flow_tab.get('title')}")

    def _send(self, method, params=None):
        self.msg_id += 1
        payload = {"id": self.msg_id, "method": method, "params": params or {}}
        self.ws.send(json.dumps(payload))
        while True:
            raw = self.ws.recv()
            data = json.loads(raw)
            if data.get("id") == self.msg_id:
                if "error" in data:
                    raise RuntimeError(f"CDP Error ({method}): {data['error']}")
                return data.get("result", {})

    def evaluate_js(self, script):
        res = self._send("Runtime.evaluate", {
            "expression": script,
            "returnByValue": True,
            "awaitPromise": True
        })
        return res.get("result", {}).get("value")

    def get_flow_image_sources(self):
        script = r'''
        (() => Array.from(document.images)
          .map(i => i.src)
          .filter(Boolean)
          .filter(s => s.includes('flow.google.com/asb/') || s.includes('flow-content.google/image/'))
        )()
        '''
        return self.evaluate_js(script) or []

    def generate_one(self, prompt, out_png, timeout=120):
        if not self.ws:
            self.connect()

        before = set(self.get_flow_image_sources())

        # Clear editor and focus
        self.evaluate_js("""
        (() => {
            const editor = document.querySelector('.ProseMirror[contenteditable="true"]');
            if (editor) {
                editor.focus();
                document.execCommand('selectAll', false, null);
                document.execCommand('delete', false, null);
                return true;
            }
            return false;
        })()
        """)
        time.sleep(0.3)

        # Insert prompt
        self._send("Input.insertText", {"text": prompt})
        time.sleep(0.4)

        # Trigger input change
        self.evaluate_js("""
        (() => {
            const editor = document.querySelector('.ProseMirror');
            if (editor) {
                editor.dispatchEvent(new Event('input', { bubbles: true }));
                editor.dispatchEvent(new Event('change', { bubbles: true }));
            }
        })()
        """)
        time.sleep(0.3)

        # Click Start generation
        coords = self.evaluate_js("""
        (() => {
            const btn = document.querySelector('button[aria-label="Start generation"], button[aria-label="Mulai pembuatan"], button[aria-label*="generation" i], button[aria-label*="pembuatan" i]') ||
                Array.from(document.querySelectorAll('button')).find(b => {
                    const al = (b.getAttribute('aria-label') || '').toLowerCase();
                    return al.includes('generation') || al.includes('pembuatan') || b.innerText.includes('arrow_forward');
                });
            if (!btn) return null;
            const r = btn.getBoundingClientRect();
            if (!btn.disabled) {
                try { btn.click(); } catch(e) {}
            }
            return { x: r.left + r.width / 2, y: r.top + r.height / 2, disabled: btn.disabled };
        })()
        """)

        if coords and not coords.get("disabled"):
            self._send("Input.dispatchMouseEvent", {"type": "mousePressed", "x": coords["x"], "y": coords["y"], "button": "left", "clickCount": 1})
            self._send("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": coords["x"], "y": coords["y"], "button": "left", "clickCount": 1})
            print("  → Prompt terkirim. Menunggu gambar Flow baru...")
        else:
            self._send("Input.dispatchKeyEvent", {"type": "rawKeyDown", "windowsVirtualKeyCode": 13, "unmodifiedText": "\r", "text": "\r"})
            self._send("Input.dispatchKeyEvent", {"type": "keyUp", "windowsVirtualKeyCode": 13, "unmodifiedText": "\r", "text": "\r"})
            print("  → Enter dispatched. Menunggu gambar Flow baru...")

        start_t = time.time()
        new_url = None
        while time.time() - start_t < timeout:
            time.sleep(3.0)
            now = self.get_flow_image_sources()
            diff = [u for u in now if u not in before]
            if diff:
                new_url = diff[0]
                break

        if not new_url:
            raise TimeoutError(f"Flow tidak menyelesaikan gambar dalam {timeout}s.")

        # Unduhan resumable: koneksi proxy sering terputus di tengah transfer.
        _download_resumable(new_url.replace("&amp;", "&"), out_png)

        # Content-aware edge energy full-bleed cropping
        try:
            from auto_crop_full_bleed import crop_image_to_full_bleed
            crop_image_to_full_bleed(str(out_png))
        except Exception as e:
            pass

        return str(out_png)

    def close(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None


def run_batch(start_idx=1, end_idx=75, delay_between=14):
    data = json.loads(STORY_PATH.read_text(encoding="utf-8"))
    shots = data["shots"]

    runner = GoogleFlowRunner()
    runner.connect()

    records = []
    print(f"\n=== MEMULAI GENERASI GOOGLE FLOW (Shots {start_idx} s/d {end_idx}) ===")

    try:
        for idx in range(start_idx, end_idx + 1):
            s = shots[idx - 1]
            sid = s["id"]
            out_png = FLOW_DIR / f"{sid}.png"
            prompt = s["visual_prompt"]

            print(f"\n[{idx:02d}/{len(shots)}] Memproses {sid} (Babak {s['chapter']})")
            print(f"  Narasi: \"{s['narration'][:60]}...\"")

            if out_png.exists() and out_png.stat().st_size > 50000:
                print(f"  ✓ Gambar sudah ada: {out_png} ({out_png.stat().st_size/1024:.1f} KB)")
            else:
                try:
                    runner.generate_one(prompt, out_png)
                    print(f"  ✓ Berhasil diunduh: {out_png} ({out_png.stat().st_size/1024:.1f} KB)")
                    if idx < end_idx:
                        print(f"  ⏳ Jeda manusia alami {delay_between}s...")
                        time.sleep(delay_between)
                except Exception as e:
                    print(f"  ✗ Gagal: {e}")
                    time.sleep(6)

            records.append({
                "shot_id": sid,
                "chapter": s["chapter"],
                "narration": s["narration"],
                "image_file": str(out_png).replace("\\", "/"),
                "status": "ready" if out_png.exists() else "pending"
            })

            # Update mapping periodically
            MAPPING_JSON.write_text(json.dumps({
                "title": data["title"],
                "total_shots": len(shots),
                "records": records
            }, ensure_ascii=False, indent=2), encoding="utf-8")
    finally:
        runner.close()

    print("\n=== GENERASI SELESAI ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Flow images for shots in range")
    parser.add_argument("project", nargs="?", help="Project directory (or CINEMATIC_PROJECT_DIR)")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=90)
    parser.add_argument("--delay", type=int, default=14)
    args = parser.parse_args()
    if args.project:
        import os
        os.environ["CINEMATIC_PROJECT_DIR"] = args.project
        # re-resolve module-level paths for the new project
        BASE = project_dir()
        FLOW_DIR = BASE / "output" / "flow_images"
        STORY_PATH = BASE / "input" / "storyboard.json"
        MAPPING_JSON = BASE / "output" / "flow_mapping.json"
        LOG_FILE = BASE / "flow_generator.log"
        FLOW_DIR.mkdir(parents=True, exist_ok=True)
        globals().update(BASE=BASE, FLOW_DIR=FLOW_DIR, STORY_PATH=STORY_PATH,
                         MAPPING_JSON=MAPPING_JSON, LOG_FILE=LOG_FILE)

    run_batch(args.start, args.end, args.delay)
