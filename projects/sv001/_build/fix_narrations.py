#!/usr/bin/env python3
"""Perbaiki kalimat narasi yang buntutnya janggal — ganti manual per kalimat."""
from pathlib import Path

P = Path("/home/hatch/workspace/kontroversi-ijazah-gibran/projects/sv001/_build/narrations.txt")
text = P.read_text(encoding="utf-8")

FIXES = [
("Namun fakta yang jarang disadari publik adalah bahwa benua Eropa ternyata menyimpan tiga sistem vulkanik raksasa yang hingga hari ini masih menunjukkan tanda-tanda kehidupan sebagaimana tercatat dalam sejarah geologi modern.",
 "Namun fakta yang jarang disadari publik adalah bahwa benua Eropa ternyata menyimpan tiga sistem vulkanik raksasa yang hingga hari ini masih menunjukkan tanda-tanda kehidupan yang jelas."),
("Yang kedua mengintai dari kedalaman Laut Aegea Yunani, sebuah gunung bawah laut yang air kawahnya cukup asam untuk melarutkan logam kapal yang membuat para vulkanolog di seluruh dunia waspada.",
 "Yang kedua mengintai dari kedalaman Laut Aegea Yunani, sebuah gunung bawah laut yang air kawahnya cukup asam untuk melarutkan logam kapal, sebuah lingkungan ekstrem yang langka di dunia."),
("Karena memahami supervolcano bukan soal menebar ketakutan di masyarakat, melainkan soal membaca bahasa bumi dengan jujur dan bersiap dengan cerdas sejak dini yang menjadi perhatian serius para ahli.",
 "Karena memahami supervolcano bukan soal menebar ketakutan di masyarakat, melainkan soal membaca bahasa bumi dengan jujur dan bersiap dengan cerdas sejak dini secara sistematis dan terukur."),
("Mari kita mulai perjalanan panjang ini dari Italia selatan, tempat sebuah kaldera raksasa bernapas tepat di bawah kaki setengah juta jiwa, sebuah titik balik besar dalam sejarah peradaban manusia.",
 "Mari kita mulai perjalanan panjang ini dari Italia selatan, tempat sebuah kaldera raksasa bernapas dengan gelisah tepat di bawah kaki setengah juta jiwa yang tidak menyadarinya."),
("Sistem ini tidak memiliki satu puncak pun, melainkan hamparan kawah, danau kawah, dan bukit vulkanik yang tersebar luas di kawasan metropolitan yang padat penduduk sebagaimana tercatat dalam sejarah geologi modern.",
 "Sistem ini tidak memiliki satu puncak pun, melainkan hamparan kawah, danau kawah, dan bukit vulkanik yang tersebar luas di sebuah kawasan metropolitan yang padat penduduk."),
("Namun para ilmuwan menegaskan satu hal yang penting, kegelisahan yang meningkat ini bukan berarti letusan besar pasti akan terjadi dalam waktu dekat yang membuat para vulkanolog di seluruh dunia waspada.",
 "Namun para ilmuwan menegaskan satu hal yang penting, kegelisahan yang meningkat ini bukan berarti letusan besar pasti akan terjadi dalam waktu yang dekat atau dapat diprediksi."),
("Sejak saat itu raksasa ini tertidur, namun tidurnya tidak pernah benar-benar nyenyak, karena tanah di atasnya terus bergerak naik dan turun perlahan dalam upaya memahami bahaya yang mengintai.",
 "Sejak saat itu raksasa ini tertidur, namun tidurnya tidak pernah benar-benar nyenyak, karena tanah di atasnya terus bergerak naik dan turun dengan perlahan yang memengaruhi fondasi bangunan."),
("Sejak tahun dua ribu lima, permukaan tanah di kota Pozzuoli telah terangkat antara seratus empat puluh lima hingga seratus enam puluh tujuh sentimeter yang menjadi perhatian serius para ahli.",
 "Sejak tahun dua ribu lima, permukaan tanah di kota Pozzuoli telah terangkat antara seratus empat puluh lima hingga seratus enam puluh tujuh sentimeter secara bertahap."),
("Sejak tahun dua ribu dua belas, otoritas Italia menetapkan status siaga kuning untuk Campi Flegrei, yaitu sebuah tanda kewaspadaan resmi pada tingkat kedua, kekuatan yang sanggup mengubah iklim seluruh planet.",
 "Sejak tahun dua ribu dua belas, otoritas Italia menetapkan status siaga kuning untuk Campi Flegrei, yaitu sebuah tanda kewaspadaan resmi pada tingkat kedua dari empat."),
("Dari Italia kita menyeberang menuju Laut Aegea, ke arah gugusan pulau Yunani yang kecantikannya menyimpan salah satu letusan terbesar dalam sejarah manusia yang membuat para vulkanolog di seluruh dunia waspada.",
 "Dari Italia kita menyeberang menuju Laut Aegea, ke arah gugusan pulau Yunani yang kecantikannya menyimpan salah satu letusan terbesar dalam sejarah manusia yang pernah tercatat."),
("Puncak gunung itu runtuh total dan membentuk kaldera selebar sebelas kali tujuh setengah kilometer, yang kini menjadi laguna biru yang dikelilingi tebing putih dalam upaya memahami bahaya yang mengintai.",
 "Puncak gunung itu runtuh total dan membentuk kaldera selebar sebelas kali tujuh setengah kilometer, yang kini menjadi laguna biru memesona yang dikelilingi tebing putih yang terjal."),
("Keterhubungan itu berarti letusan bawah laut berpotensi memicu tsunami di Laut Aegea, sebuah ancaman serius yang kini masuk dalam peta bahaya resmi Yunani yang membuat para vulkanolog di seluruh dunia waspada.",
 "Keterhubungan itu berarti letusan bawah laut berpotensi memicu tsunami di Laut Aegea, sebuah ancaman serius yang kini masuk dalam peta bahaya resmi negara Yunani dan dipantau ketat."),
("Dari birunya Laut Aegea, perjalanan kita berlanjut jauh ke utara, menuju sebuah danau yang tenang di Jerman dan menyimpan rahasia kelam ribuan tahun dalam upaya memahami bahaya yang mengintai.",
 "Dari birunya Laut Aegea, perjalanan kita berlanjut jauh ke utara, menuju sebuah danau yang tenang di Jerman dan menyimpan rahasia kelam selama ribuan tahun yang terlupakan."),
("Airnya terlihat biru dan tenang dikelilingi hutan pinus, namun ketenangan itu menipu, karena danau ini adalah kawah gunung berapi yang masih aktif yang menjadi perhatian serius para ahli.",
 "Airnya terlihat biru dan tenang dikelilingi hutan pinus, namun ketenangan itu menipu, karena danau ini adalah kawah gunung berapi yang masih aktif dan terus diawasi."),
("Yang mengejutkan banyak orang, gunung ini ternyata belum mati, karena di pantai timurnya masih keluar semburan gas karbon dioksida yang disebut mofet, kekuatan yang sanggup mengubah iklim seluruh planet.",
 "Yang mengejutkan banyak orang, gunung ini ternyata belum mati, karena di pantai timurnya masih keluar semburan gas karbon dioksida yang disebut mofet hingga hari ini."),
("Para ilmuwan juga merekam gempa frekuensi rendah yang berasal dari kedalaman bumi, sebuah tanda adanya migrasi fluida magmatik yang bergerak di bawah danau sebagaimana tercatat dalam sejarah geologi modern.",
 "Para ilmuwan juga merekam gempa frekuensi rendah yang berasal dari kedalaman bumi, sebuah tanda adanya migrasi fluida magmatik yang bergerak di bawah danau secara perlahan."),
("Laacher See dijuluki sebagai gunung yang dilupakan, karena jutaan orang tinggal di sekitarnya tanpa menyadari sejarah kelam di bawah kaki mereka yang membuat para vulkanolog di seluruh dunia waspada.",
 "Laacher See dijuluki sebagai gunung yang dilupakan, karena jutaan orang tinggal di sekitarnya tanpa menyadari sejarah kelam yang tersimpan di bawah kaki mereka selama ini."),
("Dibandingkan Campi Flegrei dan Kolumbo, Laacher See memang tampak paling tenang, namun ketenangan sebuah gunung vulkanik tidak pernah bisa diartikan sebagai kematian dalam upaya memahami bahaya yang mengintai.",
 "Dibandingkan Campi Flegrei dan Kolumbo, Laacher See memang tampak paling tenang, namun ketenangan sebuah gunung vulkanik tidak pernah bisa diartikan sebagai kematiannya sama sekali."),
("Para vulkanolog dengan jujur mengaku masih banyak hal yang belum mereka pahami tentang sistem ini, dan itulah mengapa penelitian terus didanai serta diperluas yang menjadi perhatian serius para ahli.",
 "Para vulkanolog dengan jujur mengaku masih banyak hal yang belum mereka pahami tentang sistem ini, dan itulah mengapa penelitian terus didanai serta diperluas oleh pemerintah Jerman."),
("Karena pertanyaan sebenarnya bukan sekadar apakah mereka akan terbangun suatu hari, melainkan apakah kita sudah cukup siap ketika saat itu tiba, menjadikannya salah satu yang paling ekstrem di Eropa.",
 "Karena pertanyaan sebenarnya bukan sekadar apakah mereka akan terbangun suatu hari nanti, melainkan apakah umat manusia sudah cukup siap ketika saat itu tiba dengan segala konsekuensinya."),
("Benua Eropa ternyata memiliki tiga sistem raksasa semacam itu, yaitu Campi Flegrei di Italia, Santorini Kolumbo di Yunani, dan Laacher See di Jerman, sebuah titik balik besar dalam sejarah peradaban manusia.",
 "Benua Eropa ternyata memiliki tiga sistem raksasa semacam itu, yaitu Campi Flegrei di Italia, Santorini Kolumbo di Yunani, dan Laacher See di Jerman yang semuanya masih aktif."),
("Ketiganya kini diawasi ketat dengan teknologi pemantauan modern, mulai dari jaringan seismik, pengukuran satelit GNSS, sensor gas, hingga radar citra satelit, kekuatan yang sanggup mengubah iklim seluruh planet.",
 "Ketiganya kini diawasi ketat dengan teknologi pemantauan modern, mulai dari jaringan seismik, pengukuran satelit GNSS, sensor gas, hingga radar citra satelit yang bekerja tanpa henti."),
("Data yang mengalir setiap detik itu menjadi fondasi sistem peringatan dini, memberi waktu yang berharga bagi otoritas untuk bertindak sebelum krisis memburuk sebagaimana tercatat dalam sejarah geologi modern.",
 "Data yang mengalir setiap detik itu menjadi fondasi sistem peringatan dini, memberi waktu yang berharga bagi otoritas untuk bertindak dengan cepat dan tepat sebelum krisis memburuk."),
("Zona merah telah ditetapkan secara resmi, jalur evakuasi dilatih berulang kali, dan simulasi bencana digelar rutin agar warga tahu ke mana harus pergi, dan para ilmuwan terus mempelajarinya hingga kini.",
 "Zona merah telah ditetapkan secara resmi, jalur evakuasi dilatih berulang kali, dan simulasi bencana digelar rutin agar warga tahu ke mana harus pergi saat bahaya datang."),
("Di Napoli, anak-anak sekolah kini belajar tentang kaldera raksasa di bawah kota mereka, sebagaimana mereka belajar tentang sejarah dan matematika setiap hari yang membuat para vulkanolog di seluruh dunia waspada.",
 "Di Napoli, anak-anak sekolah kini belajar tentang kaldera raksasa di bawah kota mereka, sebagaimana mereka belajar tentang sejarah dan matematika setiap hari di sekolah dengan serius."),
("Tujuan utama sains bukanlah menakut-nakuti manusia, melainkan memberi kita cukup waktu dan pengetahuan berharga agar kita dapat melindungi diri dan keluarga tercinta dengan bermartabat, sebuah warisan geologi yang masih terus diteliti.",
 "Tujuan utama sains bukanlah menakut-nakuti manusia, melainkan memberi kita cukup waktu dan pengetahuan berharga agar kita dapat melindungi diri dan keluarga tercinta dengan penuh bermartabat."),
("Letusan-letusan raksasa di masa lalu telah membentuk tanah yang subur, danau yang indah, dan bahkan jalur peradaban yang kita huni hingga saat ini yang menjadi perhatian serius para ahli.",
 "Letusan-letusan raksasa di masa lalu telah membentuk tanah yang subur, danau yang indah, dan bahkan jalur peradaban yang kita huni hingga saat ini dengan penuh syukur."),
("Di Napoli, kehidupan terus berjalan tepat di atas kaldera, pasar tetap ramai dan anak-anak bermain riang, sementara alat pemantau bekerja dalam senyap, menjadikannya salah satu yang paling ekstrem di Eropa.",
 "Di Napoli, kehidupan terus berjalan tepat di atas kaldera, pasar tetap ramai dan anak-anak bermain riang, sementara alat pemantau bekerja dalam senyap menjaga mereka semua."),
("Di Santorini, para wisatawan menikmati matahari terbenam di tepi kaldera, tanpa menyadari monster bawah laut yang kini dijaga ketat oleh para ilmuwan menurut catatan para peneliti yang mempelajarinya.",
 "Di Santorini, para wisatawan menikmati matahari terbenam di tepi kaldera, tanpa menyadari monster bawah laut yang kini dijaga ketat oleh para ilmuwan siang dan malam."),
("Di Jerman, danau Laacher See tetap biru dan tenang, menyimpan rahasianya sambil menunggu giliran untuk dipahami lebih dalam oleh sains modern, sebuah titik balik besar dalam sejarah peradaban manusia.",
 "Di Jerman, danau Laacher See tetap biru dan tenang, menyimpan rahasianya sambil menunggu giliran untuk dipahami lebih dalam oleh sains modern di masa depan yang cerah."),
("Raksasa-raksasa tidur Eropa itu bukanlah sebuah kutukan, melainkan pengingat bahwa kita hanyalah tamu sementara di planet yang luar biasa dinamis ini, kekuatan yang sanggup mengubah iklim seluruh planet.",
 "Raksasa-raksasa tidur Eropa itu bukanlah sebuah kutukan, melainkan pengingat bahwa kita hanyalah tamu sementara di planet yang luar biasa dinamis ini yang harus kita jaga bersama."),
("Terima kasih telah menonton sampai akhir, bagikan film ini agar semakin banyak orang yang waspada, dan sampai jumpa di petualangan Banyak Tau berikutnya sebagaimana tercatat dalam sejarah geologi modern.",
 "Terima kasih telah menonton sampai akhir, bagikan film ini agar semakin banyak orang yang waspada, dan sampai jumpa di petualangan Banyak Tau berikutnya yang lebih seru."),
]

applied = 0
for old, new in FIXES:
    if text.count(old) != 1:
        print(f"PROBLEM: old text found {text.count(old)}x: {old[:60]}...")
        continue
    text = text.replace(old, new)
    applied += 1

P.write_text(text, encoding="utf-8")
print(f"applied {applied}/{len(FIXES)} fixes")

# re-check word counts
bad = []
for i, line in enumerate(text.splitlines(), 1):
    line = line.strip()
    if not line:
        continue
    w = len(line.split())
    import re
    if not (25 <= w <= 35):
        bad.append((i, w))
    if re.search(r"\d", line):
        bad.append((i, "digit"))
    if "\u2014" in line:
        bad.append((i, "emdash"))
print("BAD:", bad if bad else "none")
