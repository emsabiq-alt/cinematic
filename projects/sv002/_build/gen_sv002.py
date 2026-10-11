#!/usr/bin/env python3
"""Generate sv002 (LA GARITA) Tahap A artifacts: script.md, shot_*.txt,
storyboard.json, chapters.json, chapter_titles.json from the 90-shot data."""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INP = os.path.join(BASE, "input")
SCR = os.path.join(BASE, "script")
os.makedirs(INP, exist_ok=True)
os.makedirs(SCR, exist_ok=True)

STYLE_KEY = ("Full-Bleed 16:9 Cinematic 35mm Volcanic Documentary, Ember and Basalt; "
             "ember-orange lava glow, basalt-black, chiaroscuro, volumetric god-rays, "
             "subtle 35mm grain; 0% frame, 0% collage, 0% text/watermark")
PURE = "No frame, no border, no collage, no text, no watermark."

ACTS = [
    ("PROLOG", "PROLOG — HITUNG MUNDUR LETUSAN TERBESAR", 1),
    ("BABAK DUA:", "BABAK II — MONSTER MODERN: ST. HELENS DAN KRAKATAU", 2),
    ("BABAK TIGA:", "BABAK III — TAMBORA 1815: TAHUN TANPA MUSIM PANAS", 3),
    ("BABAK EMPAT:", "BABAK IV — SUPER-LETUSAN PRASEJARAH: TOBA DAN YELLOWSTONE", 4),
    ("BABAK LIMA:", "BABAK V — LA GARITA: SANG RAJA LETUSAN DAN EPILOG", 5),
]

SHOTS = [
# ================= PROLOG 001-018 =================
("Ada letusan gunung berapi yang tidak sekadar menghancurkan sebuah kota, melainkan menulis ulang sejarah iklim seluruh planet Bumi.",
 "Tiny human silhouette standing before a colossal dark volcano on the horizon, storm clouds boiling above, embers drifting in the wind",
 "WS"),
("Hari ini kita akan menghitung mundur letusan-letusan terbesar yang pernah dikenal dalam sejarah geologi planet ini.",
 "Giant countdown numerals carved into a basalt cliff face, glowing cracks of magma between the stone digits",
 "WS"),
("Untuk memeringkatnya, para ilmuwan mengukur volume material yang disemburkan, dengan satuan yang sederhana namun mengerikan: kilometer kubik.",
 "Scientist hands in gloves holding volcanic rock and ash samples under dramatic lab light, floating dust particles",
 "CU"),
("Indeks letusan vulkanik membentang dari nol hingga delapan, sebuah skala logaritmik di mana setiap kenaikan angka berarti kekuatan yang berlipat ganda.",
 "Nested glowing magma chambers of exponentially increasing size receding into darkness, each dwarfing the last",
 "WS"),
("Ambang skala delapan adalah lebih dari seribu kilometer kubik, setara dengan melarutkan sebuah gunung raksasa ke langit dalam hitungan hari.",
 "A mountain dissolving upward into a sky-filling ash column, rock vaporizing into glowing particles",
 "WS"),
("Peringkat kelima dalam hitungan mundur kita adalah Gunung St. Helens di Amerika, yang meletus dahsyat pada tahun seribu sembilan ratus delapan puluh.",
 "Aerial view of Mount St. Helens crater with steaming dome, 1980s archival film look, pine forests below",
 "AERIAL"),
("Letusan St. Helens berskala lima dengan volume sekitar satu kilometer kubik, dan ia hanyalah satu per lima ribu dari sang juara kita.",
 "A small glowing cube of one cubic kilometer dwarfed beside a towering mountain silhouette",
 "WS"),
("Namun bahkan letusan sekecil itu meratakan hutan sejauh bermil-mil dengan semburan lateralnya, dan mengguncang seluruh Amerika Serikat.",
 "Lateral blast flattening a vast pine forest, trees snapping like matchsticks under a racing ash cloud",
 "WS"),
("Naik satu tingkat: peringkat keempat adalah Krakatau di Selat Sunda, yang meledak pada tahun seribu delapan ratus delapan puluh tiga.",
 "Krakatau island silhouette in the Sunda Strait at dusk, ominous plume rising, fishing boats in foreground",
 "WS"),
("Krakatau berskala enam dengan volume sekitar dua puluh lima kilometer kubik, dua puluh lima kali lipat St. Helens.",
 "The island tearing itself apart in a cataclysmic explosion, pyroclastic surges racing across the sea",
 "WS"),
("Tsunaminya menerjang pesisir, dan suara ledakannya terdengar hingga ribuan kilometer jauhnya, tercatat sebagai suara terkeras dalam sejarah manusia.",
 "Towering tsunami wave approaching a 19th century coastal village, people fleeing uphill",
 "WS"),
("Peringkat ketiga adalah Tambora pada tahun seribu delapan ratus lima belas, letusan terbesar yang pernah disaksikan manusia modern.",
 "Mount Tambora peak on Sumbawa island, deceptively calm, dark clouds gathering at its summit",
 "WS"),
("Tambora berskala tujuh dengan volume sekitar seratus enam puluh kilometer kubik, dan memicu Tahun Tanpa Musim Panas pada seribu delapan ratus enam belas.",
 "A darkened sun behind a global veil of ash, snow falling over a summer landscape in 1816",
 "WS"),
("Gagal panen melanda dunia, namun bahkan Tambora bukanlah yang terbesar, karena dua raksasa prasejarah menanti di depan.",
 "Withered crops and frost-covered summer fields stretching to the horizon under a grey sky",
 "WS"),
("Peringkat kedua dihuni oleh dua nama legendaris: Toba dan Yellowstone, keduanya berskala delapan.",
 "Two colossal ash columns rising side by side over a prehistoric landscape, dwarfing mountain ranges",
 "WS"),
("Toba meletus sekitar tujuh puluh empat ribu tahun lalu dengan volume dua ribu delapan ratus kilometer kubik, dan hampir memusnahkan umat manusia.",
 "Hellish volcanic crater where a serene lake will one day be, rivers of lava under a black sky",
 "WS"),
("Teori bottleneck genetik yang diajukan Stanley Ambrose pada tahun seribu sembilan ratus sembilan puluh delapan menyebut populasi manusia menyusut drastis akibat letusan itu.",
 "A small band of early humans huddled in an ash-covered wasteland, embers falling like snow",
 "MS"),
("Namun bahkan Toba yang legendaris itu bukanlah peringkat pertama, karena sang raja sesungguhnya hampir dua kali lipat lebih besar darinya.",
 "Toba's ash cloud dwarfed by an even more colossal eruption column rising behind it, scale comparison",
 "WS"),
# ================= BABAK II 019-036 =================
("Kita mulai dari bawah tangga raksasa ini, dari sebuah gunung indah di negara bagian Washington yang tampak begitu tenang.",
 "Symmetrical snow-capped cone of Mount St. Helens before 1980, pristine morning light, mirror lake reflection",
 "WS"),
("Pada pagi delapan belas Mei seribu sembilan ratus delapan puluh, gempa mengguncang lereng utara St. Helens hingga runtuh.",
 "Earthquake fissures cracking across the mountainside, dust rising, birds scattering in panic",
 "MS"),
("Seluruh sisi gunung longsor dalam sekejap, memicu semburan lateral superpanas yang melesat menyamping dengan kecepatan mengerikan.",
 "The entire north face of the mountain collapsing in a massive landslide, dust cloud exploding outward",
 "WS"),
("Hutan pinus berusia ratusan tahun tumbang seperti lidi, diratakan sejauh mata memandang oleh gelombang panas dan abu.",
 "Centuries-old pine forest flattened radially, trunks snapped and stripped bare by the lateral blast",
 "AERIAL"),
("Kolom abu menjulang menembus stratosfer, dan langit siang berubah menjadi malam di kota-kota sekitarnya.",
 "Colossal ash column punching through the stratosphere, daylight turning to darkness over towns below",
 "WS"),
("Inilah wajah letusan skala lima, dan dunia modern untuk pertama kalinya menyaksikan kekuatan penuh sebuah gunung berapi dari dekat.",
 "Scientists and observers silhouetted against the eruption, cameras and instruments in the foreground ash",
 "MS"),
("Namun ingatlah angka ini baik-baik: satu kilometer kubik, karena setiap raksasa berikutnya akan membuat angka ini terasa seperti mainan anak-anak.",
 "A single small glowing cube labeled by scale alone beside an ever-growing staircase of larger cubes",
 "WS"),
("Kita menyeberangi Pasifik menuju Selat Sunda, tempat sebuah pulau vulkanik menyimpan dendamnya selama berabad-abad.",
 "Aerial view of the Sunda Strait, Krakatau island steaming gently among scattered islets",
 "AERIAL"),
("Pada akhir Agustus seribu delapan ratus delapan puluh tiga, Krakatau meledak dengan kekuatan yang merobek pulau itu sendiri.",
 "Krakatau exploding in a blinding flash, the island ripped apart, mushroom of ash and fire",
 "WS"),
("Letusan skala enam ini menyemburkan sekitar dua puluh lima kilometer kubik material, dua puluh lima kali lipat St. Helens.",
 "Pyroclastic surges racing across the ocean surface away from the disintegrating island",
 "WS"),
("Gelombang tsunami raksasa menerjang pesisir Jawa dan Sumatra, menelan desa-desa pesisir dalam hitungan menit.",
 "Towering tsunami surging over 19th century coastal villages of Java and Sumatra",
 "WS"),
("Ledakannya terdengar hingga ribuan kilometer jauhnya, dari Australia hingga Samudra Hindia, sebagai suara terkeras yang pernah tercatat manusia.",
 "Concentric shockwave rings expanding across the ocean from the blast epicenter, ships tossed below",
 "AERIAL"),
("Gelombang tekanannya mengelilingi bumi berkali-kali, tercatat oleh barometer di seluruh penjuru dunia selama berhari-hari.",
 "Antique barometer needles trembling violently in observatories across the world, storm light through windows",
 "CU"),
("Matahari terbenam berubah menjadi merah darah selama bertahun-tahun, dilukis oleh abu Krakatau yang melayang di stratosfer.",
 "Blood-red sunsets over a 19th century harbor, sailors staring at the crimson sky",
 "WS"),
("Lebih dari seabad kemudian, Filipina menyaksikan monster modern berikutnya: Pinatubo.",
 "Mount Pinatubo in the Philippines, massive ash column rising over tropical highlands, 1991",
 "WS"),
("Pada tahun seribu sembilan ratus sembilan puluh satu, Pinatubo meletus dengan skala enam, dan abunya mendinginkan suhu global planet ini.",
 "Ash veil wrapping the blue planet seen from space, sunlight dimmed by the stratospheric haze",
 "WS"),
("Dari satu kilometer kubik menjadi dua puluh lima: setiap anak tangga skala ini adalah lompatan sepuluh kali lipat yang brutal.",
 "A brutal logarithmic staircase of glowing magma cubes, each step ten times the last, ascending into darkness",
 "WS"),
("Namun semua itu hanyalah pemanasan, karena monster-monster modern hanyalah anak tangga bawah dari tangga yang sesungguhnya.",
 "Modern volcanoes shrunk to foothills at the base of an impossibly tall staircase of fire",
 "WS"),
# ================= BABAK III 037-054 =================
("Pada tahun seribu delapan ratus lima belas, sebuah gunung di Sumbawa menulis sejarah kelam umat manusia.",
 "Mount Tambora looming over Sumbawa island villages, restless plume coiling from its summit",
 "WS"),
("Namanya Tambora, dan selama berbulan-bulan ia menggeram, memuntahkan abu, sebelum akhirnya meledak pada bulan April.",
 "The mountain rumbling for months, ash venting, villagers watching anxiously from the fields",
 "MS"),
("Puncak gunung itu runtuh ke dalam, meninggalkan kaldera raksasa tempat dulu berdiri ribuan meter batuan.",
 "The summit collapsing inward in slow cataclysm, a vast caldera yawning open where the peak stood",
 "WS"),
("Letusannya berskala tujuh dengan volume sekitar seratus enam puluh kilometer kubik, terbesar yang pernah tercatat dalam sejarah manusia.",
 "Pyroclastic flows pouring down every flank of the mountain, glowing avalanches under a black sky",
 "WS"),
("Awan panas meluncur hingga ke laut dan tsunami menerjang pesisir, merenggut korban dalam jumlah yang mengerikan.",
 "Glowing pyroclastic flows plunging into the sea, steam explosions and tsunami racing toward the coast",
 "WS"),
("Kolom abunya menjulang puluhan kilometer ke langit, dan tirai belerang mulai menyelimuti seluruh planet.",
 "Ash column tens of kilometers tall piercing the sky, a sulfurous veil spreading across the globe",
 "WS"),
("Tahun berikutnya, seribu delapan ratus enam belas, dikenang dunia sebagai Tahun Tanpa Musim Panas.",
 "Snow falling in July over a New England farmstead, bewildered farmers staring at the white fields",
 "WS"),
("Salju turun di bulan Juli di belahan bumi utara, dan tanaman gagal panen dari Eropa hingga Amerika.",
 "Frostbitten summer crops across Europe, withered wheat fields under a pale sun",
 "WS"),
("Kelaparan melanda, wabah menyebar, dan penderitaan menjalar ke berbagai benua tanpa ampun.",
 "Gaunt refugees on muddy roads, empty markets, famine gripping 19th century towns",
 "WS"),
("Bahkan dunia sastra pun lahir dari kegelapan itu: novel Frankenstein ditulis pada musim panas yang tak pernah datang.",
 "A candle-lit writing desk in a stormy lakeside villa, quill and manuscript, lightning outside the window",
 "CU"),
("Tambora mengubah iklim planet ini selama setahun penuh, dan manusia mencatatnya sebagai bencana vulkanik terbesar dalam sejarah tertulis.",
 "The darkened Earth wrapped in Tambora's ash veil, storms and failed harvests circling the globe",
 "WS"),
("Namun inilah ironi yang mengerikan: Tambora hanyalah peringkat ketiga, dan ia terpaut jauh dari dua raksasa di atasnya.",
 "Tambora's eruption column dwarfed by two far larger columns looming behind it in the distance",
 "WS"),
("Seratus enam puluh kilometer kubik berbanding lima ribu: sang juara lebih dari tiga puluh kali lipat lebih besar dari Tambora.",
 "Two glowing cubes side by side, one modest, one monstrously larger, embers swirling between them",
 "WS"),
("Dua raksasa berikutnya meletus sebelum manusia mengenal tulisan, sebelum peradaban, sebelum sejarah itu sendiri.",
 "A primeval Earth with no humans, no cities, only vast wilderness under an ash-darkened sky",
 "WS"),
("Saksi satu-satunya adalah lapisan abu di dasar laut, inti es di kutub, dan kode genetik di dalam tubuh kita.",
 "Scientists drilling an ice core in Antarctica, ancient ash layers visible in the translucent ice",
 "MS"),
("Untuk memeringkat mereka, sains membaca arsip bumi yang ditulis dengan bahasa batuan dan es.",
 "A geologist tracing a distinct ash layer through a canyon wall of ancient rock strata",
 "MS"),
("Kita kini melangkah mundur puluhan ribu tahun, ke sebuah danau raksasa di Sumatra.",
 "Aerial view of the vast serene crater lake of Toba in North Sumatra, morning mist on the water",
 "AERIAL"),
("Tujuh puluh empat ribu tahun yang lalu, danau itu adalah kawah neraka yang menelan langit.",
 "The same basin 74,000 years ago: a hellish crater of lava rivers and towering fire under a black sky",
 "WS"),
# ================= BABAK IV 055-072 =================
("Namanya Toba, supervolcano yang kini tidur di bawah danau indah di Sumatra Utara.",
 "Lake Toba's calm blue waters ringed by green highlands, a supervolcano sleeping in disguise",
 "AERIAL"),
("Letusannya berskala delapan dengan volume sekitar dua ribu delapan ratus kilometer kubik, sekitar tujuh belas kali lipat Tambora.",
 "Toba's eruption column engulfing the sky, a continent-scale plume of ash and fire",
 "WS"),
("Lapisan abu Toba ditemukan hingga ke India, ribuan kilometer jauhnya dari sumber letusannya.",
 "A thin grey ash layer blanketing a distant Indian landscape, fine ash sifting over ancient terrain",
 "WS"),
("Musim dingin vulkanik pun tiba: langit gelap bertahun-tahun, suhu global anjlok, tumbuhan mati di berbagai benua.",
 "A volcanic winter: dim red sun over dead forests, ash falling endlessly on a frozen world",
 "WS"),
("Inilah saat tergelap umat manusia, ketika populasi kita menyusut drastis hingga nyaris punah.",
 "Scattered small bands of early humans struggling through the endless ash-darkened wasteland",
 "WS"),
("Teori bottleneck genetik yang diajukan Stanley Ambrose pada tahun seribu sembilan ratus sembilan puluh delapan menyebut kita semua adalah keturunan dari segelintir penyintas.",
 "A few glowing human figures standing resilient among shadows, the seed of all future humanity",
 "MS"),
("Setiap manusia yang hidup hari ini membawa warisan letusan Toba di dalam DNA-nya.",
 "A luminous double helix of DNA rising from volcanic ash, connecting past survivors to the present",
 "CU"),
("Namun bahkan Toba bukanlah yang terbesar, karena dua ribu delapan ratus kilometer kubik masih kalah dari lima ribu.",
 "Toba's ash cloud dwarfed by a far greater eruption column rising beyond it, humbling the giant",
 "WS"),
("Sang juara hampir dua kali lipat Toba, dan nama yang lebih terkenal pun tak mampu menandinginya: Yellowstone.",
 "Yellowstone caldera with geysers steaming and bison grazing, deceptively peaceful wilderness",
 "WS"),
("Yellowstone terakhir meletus membentuk kaldera sekitar enam ratus empat puluh ribu tahun lalu, dengan volume sekitar dua ribu lima ratus kilometer kubik.",
 "Yellowstone erupting 640,000 years ago, a stupendous column of ash over the American West",
 "WS"),
("Ia dipantau ketat, dibintangi film-film bencana, dan ditakuti jutaan orang, namun rekornya pun runtuh di hadapan sang raja.",
 "A modern volcano observatory monitoring room at night, screens glowing, scientists watching seismic traces",
 "MS"),
("Letusan La Garita lebih dari dua kali lipat letusan kaldera terakhir Yellowstone.",
 "La Garita's colossal plume towering over Yellowstone's, an undeniable changing of the guard",
 "WS"),
("Toba dan Yellowstone adalah raksasa zaman es, namun kita harus mundur jauh lebih dalam: dua puluh delapan juta tahun ke masa lalu.",
 "Time rewinding violently: ice age landscapes dissolving into the deep Oligocene past",
 "WS"),
("Saat itu Colorado bukanlah pegunungan bersalju seperti sekarang, melainkan medan vulkanik San Juan yang bergolak hebat.",
 "Ancient Colorado 28 million years ago: a tortured volcanic landscape, not a single snowcap in sight",
 "WS"),
("Di era Oligosen, kawasan itu dilanda badai ignimbrit, letusan-letusan raksasa yang datang silih berganti.",
 "The ignimbrite flare-up: multiple giant volcanoes erupting in sequence across the American West",
 "AERIAL"),
("Di bawah Pegunungan San Juan, sebuah dapur magma membengkak hingga ukuran yang mustahil.",
 "Cutaway view deep underground: an impossibly vast magma chamber swelling beneath the mountains",
 "WS"),
("Tekanan menumpuk selama ribuan tahun, dan kerak bumi pun tak lagi sanggup menahannya.",
 "The Earth's crust cracking and groaning under unbearable pressure, magma glowing through the fractures",
 "CU"),
("Apa yang terjadi selanjutnya adalah ledakan tunggal terbesar yang pernah diketahui dalam sejarah geologi Bumi.",
 "An unnatural silence over the landscape, animals fleeing, the ground trembling before the cataclysm",
 "WS"),
# ================= BABAK V 073-090 =================
("Dua puluh delapan juta tahun yang lalu, bumi bersiap meledakkan mahakaryanya yang paling dahsyat.",
 "The San Juan Mountains 28 million years ago, a supervolcano swelling, the sky holding its breath",
 "WS"),
("Letusan Fish Canyon Tuff pun dimulai, dan dalam hitungan hari ia menyemburkan sekitar lima ribu kilometer kubik material vulkanik.",
 "The Fish Canyon Tuff eruption begins: a sky-shattering column of ash and fire erupting upward",
 "WS"),
("Lima ribu kilometer kubik: cukup untuk mengisi seluruh Danau Michigan hingga penuh.",
 "Lake Michigan filled to the brim with glowing volcanic ash, a staggering visualization of volume",
 "AERIAL"),
("Gunung itu tidak meledak ke atas, melainkan runtuh ke dalam, meninggalkan kaldera raksasa selebar seratus kali tiga puluh lima kilometer.",
 "The mountain collapsing inward, a 100 by 35 kilometer caldera yawning open in the Earth's crust",
 "AERIAL"),
("Awan panas melesat ratusan kilometer ke segala arah, membakar dan mengubur apa pun yang dilaluinya.",
 "Pyroclastic flows racing hundreds of kilometers in all directions, incinerating everything in their path",
 "WS"),
("Abu menyelimuti sebuah benua, langit menggelap, dan musim dingin vulkanik mencengkeram planet ini selama bertahun-tahun.",
 "Ash blanketing an entire continent, a darkened sky, the planet gripped by volcanic winter",
 "WS"),
("Para ilmuwan menyebutnya peristiwa paling energik di Bumi sejak tumbukan asteroid Chicxulub yang memusnahkan dinosaurus.",
 "A cosmic comparison: the Chicxulub asteroid impact and La Garita's eruption, two titans of Earth's history",
 "WS"),
("Inilah tangga terakhir hitungan mundur kita: lima ribu kali St. Helens, dua ratus kali Krakatau, lebih dari tiga puluh kali Tambora, dan hampir dua kali lipat Toba.",
 "The final countdown ladder: five glowing rungs from St. Helens to La Garita, each dwarfing the last",
 "WS"),
("Beberapa peneliti bahkan mengusulkan skala sembilan koma dua untuknya, namun skala resmi indeks letusan vulkanik mentok di angka delapan.",
 "Scientists debating around a chalkboard of eruption scales, the VEI scale ending firmly at eight",
 "MS"),
("La Garita adalah puncak dari badai ignimbrit Oligosen, era ketika Amerika bagian barat menjadi tungku raksasa planet ini.",
 "Panorama of the Oligocene American West as a furnace of erupting volcanoes under a glowing sky",
 "WS"),
("Lalu mengapa hampir tak ada yang mengenal namanya? Karena ia meletus dua puluh delapan juta tahun sebelum manusia pertama membuka matanya.",
 "A vast empty prehistoric landscape with no humans, no witnesses, only the silent record of stone",
 "WS"),
("Yellowstone mendapat film-film Hollywood, sementara La Garita yang memegang rekor dunia justru dilupakan sejarah populer.",
 "A Hollywood-style film camera pointed at Yellowstone while the greater La Garita caldera sits forgotten in shadow",
 "MS"),
("Mungkinkah ia terulang? Sistem supervolcano masih ada di bumi, dan para ilmuwan terus memantau mereka siang dan malam.",
 "Modern volcano monitoring: seismometers and observatories keeping watch through day and night",
 "MS"),
("Bumi mencatat skornya dengan batu, bukan dengan berita utama, dan catatannya tidak pernah berbohong.",
 "Ancient rock layers like the pages of a stone archive, a geologist's hammer resting on Fish Canyon Tuff",
 "CU"),
("Hitungan mundur ini mengajarkan satu hal: setiap anak tangga yang tampak raksasa ternyata kerdil di hadapan tangga berikutnya.",
 "A tiny human figure standing humbled before the towering staircase of Earth's greatest eruptions",
 "WS"),
("Dari satu kilometer kubik menjadi lima ribu: inilah skala kekerasan sejati sebuah planet yang hidup.",
 "Planet Earth seen from space, alive and breathing, wreathed in faint volcanic haze",
 "WS"),
("Sang raja letusan tidur di Pegunungan San Juan, Colorado, dan geologi tidak pernah melupakan.",
 "The San Juan Mountains of Colorado today, peaceful and snow-dusted, hiding the king of eruptions",
 "AERIAL"),
("Terima kasih telah menonton sampai akhir, bagikan film ini agar semakin banyak orang mengenal sang raja yang terlupakan, dan sampai jumpa di petualangan Banyak Tau berikutnya yang lebih seru.",
 "Embers rising from a glowing volcano into a starry night sky, a majestic cinematic farewell",
 "WS"),
]

assert len(SHOTS) == 90, f"expected 90 shots, got {len(SHOTS)}"

def vp(visual):
    return f"Cinematic 35mm film still, 16:9 full-bleed. {visual}. Palette: ember-orange, basalt-black, volcanic ash grey, dramatic chiaroscuro, volumetric god-rays, subtle 35mm film grain. {PURE}"

# --- script.md ---
lines = []
for i, (narr, _, _) in enumerate(SHOTS, 1):
    act = (i - 1) // 18
    if i % 18 == 1:
        lines.append(ACTS[act][0])
        lines.append("")
    lines.append(narr)
    lines.append("")
with open(os.path.join(INP, "script.md"), "w") as f:
    f.write("\n".join(lines).rstrip() + "\n")

# --- shot_*.txt ---
for i, (narr, _, _) in enumerate(SHOTS, 1):
    with open(os.path.join(SCR, f"shot_{i:03d}.txt"), "w") as f:
        f.write(narr + "\n")

# --- storyboard.json ---
shots_json = []
for i, (narr, visual, stype) in enumerate(SHOTS, 1):
    act = (i - 1) // 18
    shots_json.append({
        "id": f"shot_{i:03d}",
        "chapter": act + 1,
        "narration": narr,
        "visual_prompt": vp(visual),
        "shot_type": stype,
        "duration_hint": 10,
    })
storyboard = {
    "style": STYLE_KEY,
    "description": ("Storyboard 90 shot dokumenter sinematik 'LA GARITA: Letusan Terdahsyat "
                    "Sepanjang Sejarah Bumi' — hitung mundur letusan terbesar: St. Helens, "
                    "Krakatau, Tambora, Toba, Yellowstone, hingga La Garita."),
    "shots": shots_json,
}
with open(os.path.join(INP, "storyboard.json"), "w") as f:
    json.dump(storyboard, f, ensure_ascii=False, indent=2)
    f.write("\n")

# --- chapters.json / chapter_titles.json ---
with open(os.path.join(INP, "chapters.json"), "w") as f:
    json.dump({str(a[2]): a[1] for a in ACTS}, f, ensure_ascii=False, indent=2)
    f.write("\n")

chapter_themes = [
    ("HITUNG MUNDUR LETUSAN TERBESAR", "Konsep skala VEI logaritmik dan tangga peringkat letusan: St. Helens, Krakatau, Tambora, Toba, hingga sang juara"),
    ("MONSTER MODERN", "St. Helens 1980, Krakatau 1883, dan Pinatubo 1991: letusan modern sebagai anak tangga bawah"),
    ("TAHUN TANPA MUSIM PANAS", "Tambora 1815: letusan terbesar dalam sejarah manusia dan bencana iklim global 1816"),
    ("SUPER-LETUSAN PRASEJARAH", "Toba 74 ribu tahun lalu dan Yellowstone 640 ribu tahun lalu: raksasa zaman es sebelum manusia mencatat sejarah"),
    ("SANG RAJA LETUSAN", "La Garita 28 juta tahun lalu: Fish Canyon Tuff 5000 km kubik, letusan eksplosif tunggal terbesar yang diketahui"),
]
with open(os.path.join(INP, "chapter_titles.json"), "w") as f:
    json.dump([{"title": t, "theme": th} for t, th in chapter_themes], f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"OK: {len(SHOTS)} shots, files written to {BASE}")
