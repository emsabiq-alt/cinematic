#!/usr/bin/env python3
"""Generator paket proyek sv001 — SUPERVOLCANO EROPA."""
import json, re, sys
from pathlib import Path

BASE = Path("/home/hatch/workspace/kontroversi-ijazah-gibran/projects/sv001")
BUILD = BASE / "_build"
INP = BASE / "input"
SCR = BASE / "script"

narrations = [l.rstrip("\n") for l in (BUILD / "narrations.txt").read_text(encoding="utf-8").splitlines()]
visuals = [l.rstrip("\n") for l in (BUILD / "visuals.txt").read_text(encoding="utf-8").splitlines()]
assert len(narrations) == 90, f"narrations={len(narrations)}"
assert len(visuals) == 90, f"visuals={len(visuals)}"

# ---- validasi narasi ----
EMDASH = "\u2014"
bad = []
for i, n in enumerate(narrations, 1):
    wc = len(n.split())
    if not (25 <= wc <= 35):
        bad.append((i, wc, "wordcount"))
    if re.search(r"\d", n):
        bad.append((i, wc, "digit"))
    if EMDASH in n:
        bad.append((i, wc, "emdash"))
if bad:
    print("NARASI BERMASALAH:")
    for i, wc, kind in bad:
        print(f"  shot_{i:03d}: {kind} (words={wc})")
    sys.exit(1)
print("OK: 90 narasi valid (25-35 kata, tanpa digit, tanpa em-dash)")

shot_types = [
    "WS","AERIAL","CU","MS","DRONE","AERIAL","WS","AERIAL","MACRO","WS","MS","CU","WS","MS","CU","WS","AERIAL","DRONE",
    "AERIAL","WS","CU","WS","MS","CU","WS","MS","MACRO","WS","CU","MS","WS","CU","MS","CU","AERIAL","WS",
    "AERIAL","WS","CU","DRONE","WS","AERIAL","MACRO","CU","WS","MS","MACRO","WS","AERIAL","MS","WS","CU","WS","AERIAL",
    "WS","MS","WS","CU","AERIAL","WS","CU","MS","CU","MS","WS","AERIAL","CU","WS","MS","CU","DRONE","WS",
    "CU","AERIAL","MS","CU","WS","MS","CU","MS","WS","AERIAL","WS","CU","MS","WS","WS","WS","AERIAL","WS",
]
assert len(shot_types) == 90
durations = [10, 9, 11, 8, 12]

PREFIX = "Cinematic 35mm film still, 16:9 full-bleed."
PALETTE = ("Palette: ember-orange, basalt-black, volcanic ash grey, dramatic chiaroscuro, "
           "volumetric god-rays, subtle 35mm film grain.")
SUFFIX = "No frame, no border, no collage, no text, no watermark."

shots = []
for i in range(90):
    sid = f"shot_{i+1:03d}"
    chapter = i // 18 + 1
    shots.append({
        "id": sid,
        "chapter": chapter,
        "narration": narrations[i],
        "visual_prompt": f"{PREFIX} {visuals[i]} {PALETTE} {SUFFIX}",
        "shot_type": shot_types[i],
        "duration_hint": durations[i % 5],
    })

# ---- storyboard.json ----
storyboard = {
    "style": "Cinematic 35mm Volcanic Documentary — Ember & Basalt",
    "description": ("Full-color 35mm cinematic volcanic documentary style for Supervolcano Eropa. "
                    "Ember-orange lava glow against basalt-black rock, drifting volcanic ash, dramatic chiaroscuro "
                    "falloff into deep shadow, volumetric god-rays through smoke and steam, subtle 35mm film grain. "
                    "Aerial caldera vistas, close-up fumaroles, Naples beneath the caldera, underwater Kolumbo vents, "
                    "misty Laacher See, scientists at observatories. 0% frame, 0% collage, 0% text, 0% watermark."),
    "shots": shots,
}
(INP / "storyboard.json").write_text(json.dumps(storyboard, ensure_ascii=False, indent=2), encoding="utf-8")

# ---- script.md ----
markers = ["PROLOG", "BABAK DUA:", "BABAK TIGA:", "BABAK EMPAT:", "BABAK LIMA:"]
parts = []
for c in range(5):
    parts.append(markers[c] + "\n")
    for i in range(c * 18, c * 18 + 18):
        parts.append(narrations[i] + "\n")
(INP / "script.md").write_text("\n".join(parts), encoding="utf-8")

# ---- script/shot_*.txt ----
for i, n in enumerate(shots):
    (SCR / f"{n['id']}.txt").write_text(n["narration"], encoding="utf-8")

# ---- chapters.json ----
chapters = {
    "1": "PROLOG — RAKSASA TIDUR EROPA: KONSEP SUPERVOLCANO, KALDERA, DAN SKALA VEI",
    "2": "BABAK II — CAMPI FLEGREI: SETENGAH JUTA JIWA DI ATAS KALDERA NAPOLI",
    "3": "BABAK III — SANTORINI DAN KOLUMBO: MONSTER BAWAH LAUT AEGEA",
    "4": "BABAK IV — LAACHER SEE: GUNUNG YANG DILUPAKAN JERMAN",
    "5": "BABAK V — EPILOG: KETIKA RAKSASA TERBANGUN, SAINS, MITIGASI, DAN REFLEKSI",
}
(INP / "chapters.json").write_text(json.dumps(chapters, ensure_ascii=False, indent=2), encoding="utf-8")

# ---- chapter_titles.json ----
chapter_titles = [
    {"title": "RAKSASA TIDUR EROPA", "theme": "Konsep supervolcano dan kaldera, skala VEI, tiga sistem vulkanik raksasa Eropa yang masih aktif"},
    {"title": "SETENGAH JUTA JIWA DI ATAS KALDERA", "theme": "Campi Flegrei Napoli: bradyseism, gempa, siaga kuning, dan rencana evakuasi raksasa"},
    {"title": "MONSTER BAWAH LAUT AEGEA", "theme": "Santorini dan Kolumbo: letusan Minoan, dapur magma, krisis gempa dua ribu dua puluh lima"},
    {"title": "GUNUNG YANG DILUPAKAN JERMAN", "theme": "Laacher See Eifel: letusan VEI enam purba, mofet, dan desakan penilaian ulang bahaya"},
    {"title": "KETIKA RAKSASA TERBANGUN", "theme": "Pemantauan modern, mitigasi bencana, dan refleksi hidup berdampingan dengan raksasa geologi"},
]
(INP / "chapter_titles.json").write_text(json.dumps(chapter_titles, ensure_ascii=False, indent=2), encoding="utf-8")

# ---- youtube_meta.json ----
description = (
    "Eropa menyimpan tiga supervolcano yang masih aktif: Campi Flegrei di bawah Napoli Italia, "
    "Santorini dan Kolumbo di Laut Aegea Yunani, serta Laacher See di Jerman. Bagaimana sains modern "
    "memantau raksasa-raksasa tidur ini, dan seberapa siap kita jika mereka terbangun? Dokumenter sinematik "
    "Banyak Tau menelusuri kaldera raksasa, dapur magma bawah laut, danau kawah yang dilupakan, hingga strategi "
    "mitigasi bencana vulkanik Eropa.\n\n"
    "CHAPTERS\n"
    "00:00 PROLOG — RAKSASA TIDUR EROPA: KONSEP SUPERVOLCANO, KALDERA, DAN SKALA VEI\n"
    "03:30 BABAK II — CAMPI FLEGREI: SETENGAH JUTA JIWA DI ATAS KALDERA NAPOLI\n"
    "07:00 BABAK III — SANTORINI DAN KOLUMBO: MONSTER BAWAH LAUT AEGEA\n"
    "10:30 BABAK IV — LAACHER SEE: GUNUNG YANG DILUPAKAN JERMAN\n"
    "14:00 BABAK V — EPILOG: KETIKA RAKSASA TERBANGUN, SAINS, MITIGASI, DAN REFLEKSI\n"
    "16:30 PENUTUP & KESIMPULAN\n\n"
    "CREDIT MUSIK\n"
    "- Crypto by Kevin MacLeod (incompetech.com), CC BY 4.0\n"
    "  Licensed under Creative Commons: By Attribution 4.0 License\n"
    "  http://creativecommons.org/licenses/by/4.0/\n"
    "- Lightless Dawn by Kevin MacLeod (incompetech.com), CC BY 4.0\n"
    "  Licensed under Creative Commons: By Attribution 4.0 License\n"
    "  http://creativecommons.org/licenses/by/4.0/\n\n"
    "CREDIT PRODUKSI\n"
    "Production: Banyak Tau Studio\n"
    "Voice Over: Supertonic v3 (M2 (Supertonic Pria Ngebass 91.9 Hz))\n"
    "Visual Architecture: 35mm Cinematic Volcanic Documentary, Ember and Basalt\n"
    "Master Film: 1920x1080 30fps Full-Bleed Borderless\n\n"
    "#Supervolcano #CampiFlegrei #Santorini #Kolumbo #LaacherSee #Vulkanologi #BencanaAlam #BanyakTau #Dokumenter"
)
youtube_meta = {
    "titles": [
        "SUPERVOLCANO EROPA: Raksasa Tidur di Bawah Napoli yang Bikin Ilmuwan Waspada",
        "Setengah Juta Jiwa Tinggal di Atas Supervolcano Aktif — Ini Faktanya",
        "Santorini, Napoli, Jerman: Tiga Supervolcano Eropa yang Masih Hidup",
    ],
    "hooks": [
        "RAKSASA TIDUR DI BAWAH NAPOLI",
        "SETENGAH JUTA JIWA DI ATAS MAGMA",
        "MONSTER BAWAH LAUT AEGEA",
    ],
    "thumbnail_formula": ("YouTube thumbnail, 16:9, 1280x720, dramatic volcanic cinematic poster: colossal glowing "
                          "caldera at night, ember-orange lava veins cracking through basalt-black rock, ash plume "
                          "rising behind a coastal city silhouette, bold 3D title text, terrified awe mood, "
                          "high contrast chiaroscuro, volumetric light"),
    "description": description,
}
(INP / "youtube_meta.json").write_text(json.dumps(youtube_meta, ensure_ascii=False, indent=2), encoding="utf-8")

# ---- project.json ----
project = {
    "id": "sv001",
    "title": "SUPERVOLCANO EROPA: Raksasa Tidur di Bawah Napoli, Santorini, dan Jerman",
    "duration": "15-20 min",
    "pacing": "8-12s",
    "voice": "M2 (Supertonic Pria Ngebass 91.9 Hz)",
    "mode": "step",
    "status": "draft",
    "project_dir": "projects/sv001",
    "created_at": "2026-10-11",
    "pipeline": [
        {"key": "outline", "label": "Documentary Outline", "status": "completed"},
        {"key": "script", "label": "Voiceover Script", "status": "completed"},
        {"key": "storyboard", "label": "Storyboard", "status": "completed"},
        {"key": "assets", "label": "Visual Assets", "status": "pending"},
        {"key": "tts", "label": "TTS + Subtitle", "status": "pending"},
        {"key": "render", "label": "Local Render Engine", "status": "pending"},
    ],
    "active_stage": "storyboard",
}
(BASE / "project.json").write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")

# ---- outline.md ----
outline = """# OUTLINE DOKUMENTER: SUPERVOLCANO EROPA: Raksasa Tidur di Bawah Napoli, Santorini, dan Jerman

## PREMIS
Dokumenter sinematik populer namun akurat secara ilmiah tentang tiga sistem supervolcano aktif di Eropa: Campi Flegrei di Italia, Santorini dan Kolumbo di Yunani, serta Laacher See di Jerman. Menelusuri konsep kaldera dan skala VEI, kegelisahan vulkanik yang terpantau sains modern, strategi mitigasi, dan refleksi hidup berdampingan dengan raksasa geologi. Tanpa sensasionalisme: mengikuti kehati-hatian ilmiah para vulkanolog.

## GAYA VISUAL (STANDAR TERKUNCI)
- Format: Full-Bleed 16:9 Cinematic 35mm Volcanic Documentary, Ember and Basalt
- Lighting: Ember-orange lava glow, basalt-black shadow, dramatic chiaroscuro, volumetric god-rays menembus asap dan uap
- Color: Ember-orange, basalt-black, abu vulkanik, kontras chiaroscuro dramatis, subtle 35mm film grain
- Perspective: Aerial kaldera, close-up fumarol, kota di kaki kaldera, visualisasi bawah laut, danau berkabut, observatorium
- Purity: 0% frame, 0% collage, 0% text/watermark, tanpa teks atau diagram berlabel di gambar

## STRUKTUR 5 BABAK (TOTAL 90 SHOT SIMETRIS)

### PROLOG — RAKSASA TIDUR EROPA (Shot 001 - 018)
- Konsep kaldera dan definisi supervolcano sebagai raksasa tidur dunia geologi.
- Skala indeks letusan vulkanik dari nol hingga delapan dan makna setiap tingkatnya.
- Fakta mengejutkan: Eropa menyimpan tiga sistem vulkanik raksasa yang masih aktif.
- Ketiganya berada di bawah kota besar, jalur pelayaran, dan kawasan padat penduduk.
- Perkenalan tiga lokasi: Teluk Napoli, Laut Aegea, dan danau kawah Jerman barat.
- Komitmen akurasi: seluruh fakta berasal dari INGV, observatorium Athena, dan riset geosains Jerman.

### BABAK II — CAMPI FLEGREI: SETENGAH JUTA JIWA DI ATAS KALDERA (Shot 019 - 036)
- Kaldera bersarang di barat Napoli, ladang yang terbakar, tanpa satu puncak pun.
- Lebih dari tujuh puluh letusan dalam lima belas ribu tahun; Campanian Ignimbrite sekitar tiga puluh sembilan ribu tahun lalu berskala tujuh.
- Letusan terakhir tahun seribu lima ratus tiga puluh delapan melahirkan Monte Nuovo.
- Bradyseism: tanah Pozzuoli terangkat antara seratus empat puluh lima hingga seratus enam puluh tujuh sentimeter sejak tahun dua ribu lima.
- Rangkaian gempa menguat: magnitudo empat koma empat, empat koma enam, hingga empat koma tujuh pada tiga puluh satu Juli dua ribu dua puluh enam.
- Status siaga kuning sejak tahun dua ribu dua belas; fumarol Solfatara dan sinyal gas dari magma lebih dari enam kilometer.
- Sekitar lima ratus ribu jiwa di dalam kaldera; rencana evakuasi empat ratus delapan puluh satu ribu orang dalam tujuh puluh dua jam.
- Penegasan ilmiah: kegelisahan meningkat bukan berarti letusan pasti terjadi; INGV memantau dua puluh empat jam.

### BABAK III — SANTORINI DAN KOLUMBO: MONSTER BAWAH LAUT AEGEA (Shot 037 - 054)
- Letusan Minoan sekitar tahun seribu enam ratus tiga belas sebelum masehi berskala tujuh, sekitar enam puluh kilometer kubik, sebanding Tambora.
- Kaldera selebar sebelas kali tujuh setengah kilometer; kaitan dengan kemunduran peradaban Minoa.
- Kolumbo tujuh kilometer di timur laut Santorini: kawah lima ratus meter di bawah laut, air asam pH lima, gas dua ratus dua puluh derajat celsius.
- Letusan tahun seribu enam ratus lima puluh menewaskan sekitar tujuh puluh orang akibat gas beracun.
- Temuan dua ribu dua puluh dua: dapur magma dua hingga empat kilometer di bawah dasar laut, satu koma empat kilometer kubik, terisi empat juta meter kubik per tahun.
- Krisis Januari Februari dua ribu dua puluh lima: lebih dari dua puluh delapan ribu gempa, intrusi tiga belas kilometer berhenti tanpa letusan.
- Studi dua ribu dua puluh lima: keduanya terhubung hidraulik dalam satu sistem magma; risiko tsunami Aegea.

### BABAK IV — LAACHER SEE: GUNUNG YANG DILUPAKAN JERMAN (Shot 055 - 072)
- Danau kawah di Eifel Jerman barat berdiameter sekitar dua kilometer; tampak tenang namun masih aktif.
- Letusan sekitar dua belas ribu sembilan ratus tahun lalu berskala enam: dua puluh kilometer kubik, dua ratus lima puluh kali St Helens, abu hingga Swedia dan Italia utara.
- Bukti aktivitas kini: mofet karbon dioksida di pantai timur dan gempa frekuensi rendah dari kedalaman.
- Belum ada deformasi permukaan sehingga bukan pertanda letusan dekat; ilmuwan GFZ dan KIT mendesak penilaian ulang bahaya.
- Julukan gunung yang dilupakan: jutaan orang tinggal di sekitarnya tanpa menyadari sejarahnya.

### BABAK V — EPILOG: KETIKA RAKSASA TERBANGUN (Shot 073 - 090)
- Definisi ilmiah supervolcano: sistem kaldera raksasa dengan letusan skala tujuh hingga delapan.
- Tiga sistem Eropa dirangkum: Campi Flegrei, Santorini Kolumbo, Laacher See.
- Pemantauan modern: jaringan seismik, GNSS, sensor gas, radar citra satelit, sistem peringatan dini.
- Mitigasi: zona merah, jalur evakuasi, simulasi rutin, edukasi publik termasuk anak sekolah di Napoli.
- Kejujuran ilmiah tentang batas prediksi; tujuan sains adalah kesiapan, bukan ketakutan.
- Penutup reflektif: hidup berdampingan dengan raksasa geologi dengan hormat, waspada, dan ilmu pengetahuan.
"""
(INP / "outline.md").write_text(outline, encoding="utf-8")

print("OK: semua file ditulis")

# ================= VERIFIKASI =================
errors = []

# 1. storyboard.json valid, 90 shot
sb = json.loads((INP / "storyboard.json").read_text(encoding="utf-8"))
if len(sb["shots"]) != 90:
    errors.append(f"shots={len(sb['shots'])}")

# 2. id berurutan, chapter tepat 18
for i, s in enumerate(sb["shots"]):
    exp_id = f"shot_{i+1:03d}"
    if s["id"] != exp_id:
        errors.append(f"id mismatch idx {i}: {s['id']} != {exp_id}")
    if s["chapter"] != i // 18 + 1:
        errors.append(f"chapter mismatch {s['id']}")
from collections import Counter
cc = Counter(s["chapter"] for s in sb["shots"])
if dict(cc) != {1: 18, 2: 18, 3: 18, 4: 18, 5: 18}:
    errors.append(f"chapter counts: {dict(cc)}")

# 3. visual_prompt prefix/suffix
for s in sb["shots"]:
    vp = s["visual_prompt"]
    if not vp.startswith(PREFIX):
        errors.append(f"{s['id']}: bad prefix")
    if not vp.endswith(SUFFIX):
        errors.append(f"{s['id']}: bad suffix")

# 4. 90 file script cocok dengan narration
for s in sb["shots"]:
    p = SCR / f"{s['id']}.txt"
    if not p.exists():
        errors.append(f"missing {p.name}")
    elif p.read_text(encoding="utf-8") != s["narration"]:
        errors.append(f"content mismatch {p.name}")

# 5. semua JSON valid
for jf in ["storyboard.json", "chapters.json", "chapter_titles.json", "youtube_meta.json"]:
    try:
        json.loads((INP / jf).read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"{jf} invalid: {e}")
try:
    json.loads((BASE / "project.json").read_text(encoding="utf-8"))
except Exception as e:
    errors.append(f"project.json invalid: {e}")

# 6. script.md: marker + 90 kalimat
sm = (INP / "script.md").read_text(encoding="utf-8")
for m in markers:
    if m not in sm:
        errors.append(f"marker hilang: {m}")
paras = [p for p in sm.split("\n\n") if p.strip() and p.strip() not in markers]
if len(paras) != 90:
    errors.append(f"script.md paragraphs={len(paras)}")

if errors:
    print("VERIFIKASI GAGAL:")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("VERIFIKASI LOLOS: 90 shot, 18/babak, id berurutan, 90 file txt cocok, semua JSON valid, script.md 90 kalimat.")
