"""flow_batch_generator_a044.py — Google Flow Batch Generator for Merapi 1006.

Features:
- Connects to Chrome DevTools Protocol at port 9222 (flow.google.com).
- Dispatches prompt to ProseMirror editor with input events.
- Dispatches real mouse events to "Start generation" button.
- Detects new images dynamically (supporting flow.google.com/asb and flow-content.google).
- Auto-crops edge borders if needed and resizes to 1920x1080 Full-Bleed 16:9.
- Progress tracking and resuming capability (skips existing images > 50KB).
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import websocket
from pathlib import Path

CDP_PORT = int(os.environ.get("CHROME_CDP_PORT", 9222))
CDP_BASE = f"http://127.0.0.1:{CDP_PORT}"

BASE = Path("D:/project/a044")
FLOW_DIR = BASE / "output" / "flow_images"
STORY_PATH = BASE / "input" / "merapi_master_storyboard_enriched.json"
MAPPING_JSON = BASE / "output" / "flow_mapping.json"
LOG_FILE = BASE / "flow_generator.log"

FLOW_DIR.mkdir(parents=True, exist_ok=True)
(BASE / "output").mkdir(parents=True, exist_ok=True)


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

        req = urllib.request.Request(
            new_url.replace("&amp;", "&"),
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://flow.google.com/"}
        )
        with urllib.request.urlopen(req, timeout=40) as r, open(out_png, "wb") as f:
            f.write(r.read())

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
    print(f"\n=== MEMULAI GENERASI GOOGLE FLOW A044 (Shots {start_idx} s/d {end_idx}) ===")

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=75)
    parser.add_argument("--delay", type=int, default=14)
    args = parser.parse_args()

    run_batch(args.start, args.end, args.delay)
