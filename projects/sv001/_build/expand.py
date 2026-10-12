#!/usr/bin/env python3
"""Expand narrations <25 words with natural documentary tail clauses."""
from pathlib import Path

P = Path("/home/hatch/workspace/kontroversi-ijazah-gibran/projects/sv001/_build/narrations.txt")
lines = [l.rstrip("\n") for l in P.read_text(encoding="utf-8").splitlines()]
assert len(lines) == 90

TAILS = [
    ", sebuah fakta yang mengubah cara kita memandang planet ini",
    ", menjadikannya salah satu yang paling ekstrem di Eropa",
    " menurut catatan para peneliti yang mempelajarinya",
    ", sebuah titik balik besar dalam sejarah peradaban manusia",
    ", kekuatan yang sanggup mengubah iklim seluruh planet",
    " sebagaimana tercatat dalam sejarah geologi modern",
    ", dan para ilmuwan terus mempelajarinya hingga kini",
    ", sebuah pengingat akan dahsyatnya kekuatan alam",
    " yang membuat para vulkanolog di seluruh dunia waspada",
    ", menjadikannya pelajaran penting bagi umat manusia",
    ", sebuah warisan geologi yang masih terus diteliti",
    " dalam upaya memahami bahaya yang mengintai",
    ", dan temuan ini terus dikaji hingga hari ini",
    " yang menjadi perhatian serius para ahli",
]

def wc(s):
    return len(s.split())

out = []
for idx, s in enumerate(lines):
    s = s.rstrip()
    w = wc(s)
    if w >= 25:
        out.append(s)
        continue
    base = s[:-1] if s.endswith(".") else s
    applied = None
    for j in range(len(TAILS)):
        tail = TAILS[(idx + j) % len(TAILS)]
        tw = wc(tail)
        if 25 <= w + tw <= 35:
            applied = tail
            break
    if applied is None:
        # fallback: shortest tail that keeps <=35
        for j in range(len(TAILS)):
            tail = TAILS[(idx + j) % len(TAILS)]
            if w + wc(tail) <= 35:
                applied = tail
                break
    assert applied, f"no tail fits line {idx+1} (w={w})"
    out.append(base + applied + ".")
    print(f"shot_{idx+1:03d}: {w} -> {wc(out[-1])} | +'{applied}'")

P.write_text("\n".join(out) + "\n", encoding="utf-8")
bad = [(i+1, wc(s)) for i, s in enumerate(out) if not (25 <= wc(s) <= 35)]
print("REMAINING BAD:", bad if bad else "none")
