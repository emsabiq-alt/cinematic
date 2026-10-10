"""Single source of truth for visual style across every generator.

Shot prompts, storyboard instructions, and thumbnails all read from here so
tone/palette cannot drift between stages.
"""

# Palette shared by every rendered asset.
PALETTE = {
    "shadow": "#3a2a1a",
    "highlight": "#d9c4a0",
    "accent": "#a8763e",
}

MEDIUM = "19th-century archival sepia intaglio copperplate etching"

# Appended to every shot prompt sent to Flow.
STYLE_LOCK = (
    f" Rendered as a {MEDIUM}: "
    "fine cross-hatched engraving lines, warm monochrome sepia palette "
    f"({PALETTE['shadow']} shadows, {PALETTE['highlight']} highlights), aged paper grain, "
    "soft vignette-free even lighting, consistent medium-contrast tonal range, "
    "no colour other than sepia. "
    "Full-bleed 16:9 composition with no frame, no border, no margin, no text, no watermark."
)

# Style rules injected into the storyboard prompt so the model never invents
# a competing medium (this is what produced 'technical diagram' shots before).
STORYBOARD_STYLE_RULES = (
    f"SEMUA visual_prompt WAJIB memakai medium tunggal: {MEDIUM}. "
    "Tulis visual_prompt sebagai DESKRIPSI ISI/ADEGAN saja (subjek, aksi, komposisi, "
    "pencahayaan) dalam bahasa Inggris. JANGAN menulis nama medium, gaya, palet warna, "
    "atau kata seperti 'technical diagram', 'blueprint', 'photorealistic', 'oil painting', "
    "'watercolor', '3d render', 'vibrant colors' — style dikunci otomatis oleh sistem. "
    "Variasikan SUBJEK (peta, instrumen, arsip, lanskap, aksi lapangan, potret) "
    "tanpa mengubah medium atau tone."
)

# Thumbnails: same medium and palette, only framing differs.
THUMBNAIL_STYLE = (
    f"Masterpiece {MEDIUM}, fine cross-hatched engraving lines, "
    f"warm monochrome sepia palette ({PALETTE['shadow']} shadows, "
    f"{PALETTE['highlight']} highlights, {PALETTE['accent']} accents), aged paper grain, "
    "even lighting with consistent medium-contrast tonal range, no colour other than sepia. "
    "Full-bleed 16:9, no frame, no border, no margin, no watermark."
)

# Phrases that switch medium; stripped from model output before the lock.
CONFLICTS = (
    "technical diagram", "technical drawing", "blueprint", "schematic diagram",
    "photorealistic", "photograph", "photo-realistic", "3d render", "digital art",
    "oil painting", "watercolor", "watercolour", "vibrant colors", "vibrant colours",
    "full color", "full colour", "modern illustration", "cartoon",
)

# Leading boilerplate the model tends to write; the lock replaces it.
STYLE_PREFIXES = (
    "full-bleed 16:9 archival sepia intaglio copperplate etching of",
    "full-bleed 16:9 archival sepia intaglio etching of",
    "full-bleed 16:9 archival sepia intaglio scene showing",
    "full-bleed 16:9 archival sepia etching depicting",
    "full-bleed 16:9 archival sepia etching of",
    "full-bleed 16:9 archival sepia of",
    "full-bleed 16:9 archival sepia",
)
