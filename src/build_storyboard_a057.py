"""
build_storyboard_a057.py
Generates the 90-shot symmetrical storyboard for project a057
(KONTROVERSI IJAZAH GIBRAN: INVESTIGASI FORENSIK DOKUMEN DAN SISTEM PENDIDIKAN)
Using the locked 35mm Cinematic Chiaroscuro Warm Tungsten & Forensic Documentary Style.
"""
import json
import re
from pathlib import Path

PROJECT_DIR = Path("D:/project/a057")
SCRIPT_FILE = PROJECT_DIR / "input" / "script.md"
OUT_FILE = PROJECT_DIR / "input" / "storyboard.json"
SCRIPT_DIR = PROJECT_DIR / "script"
SCRIPT_DIR.mkdir(parents=True, exist_ok=True)

def get_narration_chunks():
    text = SCRIPT_FILE.read_text(encoding="utf-8")
    
    p1 = text.find("PROLOG")
    p2 = text.find("BABAK DUA:")
    p3 = text.find("BABAK TIGA:")
    p4 = text.find("BABAK EMPAT:")
    p5 = text.find("BABAK LIMA:")
    
    c1 = text[p1:p2].replace("PROLOG", "").replace("BABAK SATU: DARI SYDNEY HINGGA SINGAPURA", "").strip()
    c2 = text[p2:p3].replace("BABAK DUA: ANATOMI PATHWAY DAN SKEMA DIPLOMA", "").strip()
    c3 = text[p3:p4].replace("BABAK TIGA: AUDIT DOKUMEN DAN PENYETARAAN RESMI", "").strip()
    c4 = text[p4:p5].replace("BABAK EMPAT: ANATOMI NARASI DI RUANG PUBLIK", "").strip()
    c5 = text[p5:].replace("BABAK LIMA: REFLEKSI KREDIBILITAS DAN AKUNTABILITAS PUBLIK", "").strip()

    chapters = [c1, c2, c3, c4, c5]
    chunks = []
    for c in chapters:
        sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', c) if s.strip()]
        assert len(sents) == 18, f"Expected 18 sentences, got {len(sents)}"
        chunks.extend(sents)
    return chunks

PROMPTS = [
    # BABAK 1: PROLOG & DARI SYDNEY HINGGA SINGAPURA (Shots 001 - 018)
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Macro shot of an official diploma certificate document resting on a polished dark mahogany table, illuminated by a warm tungsten banker's lamp. "
        "Lighting: warm tungsten pool radiating from the brass lamp, casting deep chiaroscuro shadows across the dark timber, rich golden highlights on the textured heavy parchment paper. "
        "Color: warm amber (#FF9E3B), aged paper ivory, and deep mahogany brown against obsidian shadows. "
        "Extreme shallow depth of field, paper fiber texture, faint embossed seal reflections, subtle organic 35mm film grain. Forensic historic gravitas. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Dramatic low-angle medium shot inside a dimly lit parliamentary archive hall at twilight, tall arched windows looking out into dusk. "
        "Lighting: low-key chiaroscuro with warm bronze reading lamps casting long geometric shadows across rows of heavy timber counsel desks and leather chairs. "
        "Color: warm amber glow and antique brass against deep charcoal slate shadows. "
        "Deep vanishing point down the central carpeted aisle, dust motes floating in volumetric light shafts. High-stakes political tension. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Wide cinematic interior of a high-floor executive state office at night, overlooking the illuminated cityscape skyline of Jakarta through floor-to-ceiling glass. "
        "Lighting: warm directional ceiling spotlights illuminating a massive teak desk with state files, contrasted by the deep blue and amber glow of the metropolis outside. "
        "Color: warm honey amber, deep navy blue, and rich teak wood tones against dark shadows. "
        "Symmetrical one-point perspective, cinematic atmospheric depth, pristine 35mm realism. Solemn political ascent. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Forensic investigative close-up of thick government dossier folders, legal briefs, and archival records stacked on a desk under a focused overhead warm lamp. "
        "Lighting: intense warm tungsten cone of light piercing through deep shadows, illuminating paper edges, red ribbon bindings, and official file tabs. "
        "Color: warm parchment cream, dull file folder manila, and deep mahogany against pitch-black surroundings. "
        "Shallow depth of field, dust motes caught in the concentrated light beam. Uncompromising documentary scrutiny. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Nostalgic wide exterior of a classic Indonesian public junior high school courtyard in Surakarta during late golden hour. "
        "Lighting: warm golden sunlight streaming through tropical banyan and mahogany trees, casting long diagonal amber shadows across vintage red-brick corridors and tiled pavements. "
        "Color: rich warm amber, terracotta brick red, and leafy green against deep courtyard shadows. "
        "Deep linear perspective along the school veranda, subtle atmospheric haze, timeless documentary aesthetic. Childhood academic roots. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Atmospheric medium shot inside an international airport departure terminal lounge at dusk, a solitary teenage student silhouette holding travel papers looking out the rain-streaked window. "
        "Lighting: warm amber tarmac lights reflecting off the wet apron outside, soft interior terminal ceiling lamps casting gentle rim light on the traveler. "
        "Color: warm tungsten amber and wet tarmac gold against deep indigo twilight. "
        "Cinematic three-quarter angle with soft bokeh of airport runway lights, delicate film grain. The overseas crossroad. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Exterior establishing shot of a modern secondary school campus in Singapore in early morning light, clean architectural lines and tropical covered walkways. "
        "Lighting: soft morning sunlight breaking through light tropical mist, casting clean warm highlights on white concrete facades and lush green foliage. "
        "Color: warm morning gold and pristine ivory against deep emerald landscaping. "
        "Architectural wide perspective with deep vanishing point down the modern pedestrian colonnade. Structured international schooling. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Intimate medium shot of a student's wooden study desk at night in Singapore, an open English textbook, vocabulary notes, and a brass desk lamp. "
        "Lighting: warm tungsten bulb illuminating the desktop pages in a warm golden pool, the rest of the bedroom submerged in deep comforting shadows. "
        "Color: warm amber (#FF9E3B), notebook cream, and dark timber against obsidian background. "
        "Shallow depth of field, rain droplets clinging to the window behind, focused quiet diligence. Self-reliance far from home. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Wide panoramic aerial view of Sydney Harbour at twilight, looking across the calm dark waters toward the illuminated Sydney skyline and harbour infrastructure. "
        "Lighting: warm amber city lights and ferry terminal lanterns contrasting with the deep cobalt and violet evening sky, reflections shimmering on the water surface. "
        "Color: glowing amber-gold, slate grey, and deep oceanic indigo. "
        "Grand cinematic establishing shot with sweeping horizon, subtle atmospheric film texture. Transcontinental journey south. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Medium shot of the UTS Insearch modern campus entrance in Sydney, red sandstone blending with contemporary glass and steel architecture. "
        "Lighting: warm late-afternoon Australian sunlight casting crisp directional shadows across the stone plaza and student entryways. "
        "Color: warm sandstone ochre, amber glass reflections, and deep cool urban shadows. "
        "Dynamic low-angle perspective, students in soft focus in the background, sharp documentary realism. Academic pathway gateway. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Interior view of a contemporary university tiered lecture theatre at UTS Insearch, curved timber desks and tiered seating. "
        "Lighting: warm recessed architectural downlights illuminating the polished wood surfaces in sequential pools of light, dark acoustic walls. "
        "Color: warm honey amber, pale beech wood, and dark charcoal shadows. "
        "Symmetrical perspective from the rear row looking down toward the lectern, deep vanishing point. Structured bridging environment. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Over-the-shoulder close-up of business economics case studies, market analysis charts, and financial textbooks spread across an oak study carrel. "
        "Lighting: directional warm tungsten reading lamp raking across printed graphs and handwritten notes, highlighting pen ink sheen and paper texture. "
        "Color: warm amber light, crisp white paper, and dark oak wood against deep shadows. "
        "Macro depth of field, tactile paper grain, dust motes in the lamp beam. Rigorous business fundamentals. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Wide exterior shot of the Management Development Institute of Singapore (MDIS) campus grounds during late afternoon golden hour. "
        "Lighting: golden tropical sun casting long warm rays through manicured palms, illuminating the modern multi-story academic buildings and glass atriums. "
        "Color: radiant golden amber and polished stone ivory against rich tropical green. "
        "Grand architectural perspective, clean contemporary aesthetic, 35mm cinematic clarity. Higher education destination in Singapore. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Interior view of the grand entrance lobby of MDIS, polished granite floor reflecting overhead warm brass chandeliers and institutional heraldic seals. "
        "Lighting: warm ambient chandelier lighting paired with floor-to-ceiling glass natural light, casting soft balanced illumination across reception pillars. "
        "Color: warm amber, dark granite, and polished brass highlights against neutral shadows. "
        "Deep one-point vanishing point down the central foyer corridor. Established institutional legacy. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Formal academic partnership council room, a long mahogany boardroom table flanked by British and Singaporean flags, leather binders of academic agreements. "
        "Lighting: focused warm ceiling spotlights shining directly onto the polished wood table and framed bilateral charters on the panelled walls. "
        "Color: deep mahogany red, warm amber gold, and brass accents against rich dark shadows. "
        "Symmetrical cinematic framing, dignified institutional atmosphere, subtle 35mm film grain. Transnational higher education pacts. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Symmetrical wide shot down a long, stately academic colonnade lined with framed crests of partner universities from the UK and Commonwealth. "
        "Lighting: rhythmic warm wall sconces casting scalloped golden arcs of light down the corridor, deep obsidian shadows between arches. "
        "Color: warm amber, cream marble, and dark oak against deep shadows. "
        "Dramatic one-point vanishing point receding into glowing warmth at the far end. Cross-continental curriculum oversight. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Archival flat-lay desk composition: an antique world map with glowing golden flight corridors connecting Indonesia, Singapore, Sydney, and the United Kingdom, alongside passports and academic dossiers. "
        "Lighting: warm tungsten angle lamp casting high-contrast shadows across folded maps, brass compass, and passport covers. "
        "Color: warm parchment amber, brass gold, and dark leather against shadowy tabletop. "
        "High-angle tactical perspective, rich tactile textures, dust motes in the warm ray. Dynamic three-nation educational mobility. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Forensic investigative research wall: an organized corkboard with pinned academic certificates, timeline diagrams, and red verification thread connecting dates, under a flickering tungsten desk lamp. "
        "Lighting: stark single-source tungsten light from below, casting dramatic shadows upward across pins, paper edges, and string lines. "
        "Color: warm amber (#FF9E3B), aged document cream, and dark cork against obsidian shadows. "
        "Three-quarter close perspective, shallow depth of field, high investigative tension. Seed of future public controversy. No frame, no border, no collage, no text, no watermark."
    ),

    # BABAK 2: ANATOMI PATHWAY DAN SKEMA DIPLOMA (Shots 019 - 036)
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Split comparative archival composition: on the left, a traditional Indonesian National Education curriculum handbook; on the right, an intricate Commonwealth modular credit syllabus, resting on a heavy oak table. "
        "Lighting: low-hanging brass library pendant lamp casting a balanced warm pool of light across both open volumes. "
        "Color: warm amber, aged paper ivory, and deep oak brown against dark library background. "
        "Overhead symmetrical perspective, crisp typography and paper texture under 35mm film grain. Dual educational paradigms. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Symmetrical wide interior of an Indonesian university graduation hall, rows of empty wooden auditorium seats and national academic ceremonial banners under formal lighting. "
        "Lighting: warm incandescent auditorium chandeliers casting a solemn golden glow over polished floorboards, deep shadows between seating rows. "
        "Color: warm amber, golden fabric trim, and rich teak wood against deep shadows. "
        "Grand one-point perspective looking toward the ceremonial stage. Traditional linear bachelor expectation. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Contemporary international university admissions office: an academic counselor and a student reviewing a clear multi-tiered pathway chart on a glass consultation desk. "
        "Lighting: warm architectural downlights creating soft pools of amber light, large window behind letting in muted daylight. "
        "Color: warm honey amber, brushed aluminium, and clean glass against soft neutral shadows. "
        "Medium three-quarter angle with shallow depth of field, modern professional clarity. The flexible global pathway system. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Close macro shot of an official UTS Insearch student guide and vocational diploma syllabus binder lying flat on a dark executive desk. "
        "Lighting: focused warm directional spotlight highlighting the embossed metallic silver institution logo on the textured navy folder. "
        "Color: warm amber light reflections, deep royal blue, and silver foil against dark wood. "
        "Shallow depth of field, sharp paper texture, forensic documentary clarity. Matriculation and diploma distinction. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Intensive international business tutorial classroom: diverse students gathered around a seminar table engaged in case study analysis, whiteboard filled with strategic formulas. "
        "Lighting: warm directional late-afternoon sunlight cutting through venetian blinds, creating striped patterns of amber light and shadow across the room. "
        "Color: warm sunlit gold and amber against cool classroom shadows. "
        "Dynamic medium perspective, dust motes dancing in the sunbeams, authentic academic realism. Intensive bridging preparation. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Forensic macro view of an official completion certificate on thick textured laid paper, bearing the formal seal and credit transfer clauses of UTS Insearch. "
        "Lighting: warm raking tungsten light from the side, revealing the micro-relief of the paper fibers, embossed seal rim, and crisp dark typography. "
        "Color: warm parchment cream, dark charcoal ink, and amber light highlights. "
        "Extreme macro perspective, shallow depth of field. The bridge to higher university credits. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Investigative close-up of two distinct educational documents laid side by side on a green felt desk blotter, observed through a brass magnifying glass held by an examiner. "
        "Lighting: warm directional desk lamp illuminating the glass lens and the contrasting headings: preparatory certificate versus bachelor degree. "
        "Color: warm amber (#FF9E3B), aged paper ivory, and antique brass against deep forest green. "
        "Macro optical perspective with subtle distortion around the lens edge, high forensic scrutiny. Anatomy of public confusion. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Exterior tracking shot of the MDIS administrative tower in Singapore at dusk, warm interior office lights glowing through glass curtain walls. "
        "Lighting: warm tungsten interior glows contrasting beautifully with deep twilight royal blue sky, manicured palm silhouettes in the foreground. "
        "Color: warm amber and glowing windows against deep evening blue. "
        "Architectural medium perspective, clean geometric framing, 35mm film grain. The Singapore academic hub under scrutiny. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Elegant dark mahogany library vitrine displaying official marketing course curriculum handbooks bearing the joint insignias of MDIS and the University of Bradford UK. "
        "Lighting: warm interior cabinet spotlights casting radiant golden reflections across gilded book spines and glass shelves. "
        "Color: rich warm amber, polished mahogany red, and gold leaf against dark museum shadows. "
        "Dramatic angled perspective with soft bokeh reflections. Bilateral British-Singaporean educational partnership. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Formal high-level international education symposium chamber: UK Quality Assurance Agency flags and international academic treaty protocols on an ornate lectern. "
        "Lighting: grand warm chandelier lighting from above, casting stately golden illumination across wood-panelled hall walls and leather treaties. "
        "Color: warm amber gold, antique parchment, and deep British oak against soft shadows. "
        "Dignified wide perspective, deep architectural depth, subtle film texture. Transnational higher education framework. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Flat-lay macro view of official examination test papers and grading rubrics embossed with British university external moderation stamps and red auditor annotations. "
        "Lighting: classic green banker's desk lamp casting focused warm tungsten light across test booklets and grading sheets. "
        "Color: warm ivory paper, red examiner ink, and dark wood against deep shadows. "
        "Extreme flat-lay macro, crisp printed text, tactile paper grain. Strict UK curriculum and examination alignment. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Traditional faculty senate boardroom inside the University of Bradford, UK: senior professors in academic regalia reviewing international partner moderation files. "
        "Lighting: warm chandelier glow blending with soft overcast British daylight entering through tall leaded windows, illuminating oak panelling. "
        "Color: warm amber, dark English oak, and crimson gown accents against deep shadows. "
        "Dramatic three-quarter wide framing, dignified historic gravitas, 35mm documentary realism. Rigorous European quality audits. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Close shot of a royal blue hardbound university degree folder being gently opened on an oak examination desk, revealing the official gold foil crest of the University of Bradford. "
        "Lighting: warm directional tungsten lamp highlighting the metallic gleam of the gold crest and the heavy parchment certificate beneath. "
        "Color: shimmering gold, royal blue leatherette, and warm ivory paper against dark oak. "
        "Intimate close-up perspective, shallow depth of field, dust motes in the warm light beam. The authentic conferring institution. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Forensic macro shot of the degree title engraved on heavy parchment: 'Bachelor of Science with Second Class Honours (Second Division) in Marketing'. "
        "Lighting: raking warm tungsten light across the crisp serif letterforms, embossed border, and official registrar signature. "
        "Color: warm amber (#FF9E3B), dark soot-black printing ink, and aged parchment cream. "
        "Extreme macro depth of field, paper grain fibers visible, flawless archival clarity. Formal degree conferring text. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Conceptual archival progression: three stacked certificates neatly fanned out on a dark desk—foundation certificate, advanced diploma, culminating in the bachelor degree parchment at the top. "
        "Lighting: focused warm spotlight tracing the stepped sequence of credentials from bottom to top. "
        "Color: warm golden amber, cream paper, and dark mahogany against deep shadows. "
        "Symmetrical low-angle perspective, clear structural hierarchy, 35mm documentary precision. The top-up degree articulation mechanism. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Majestic wide view inside a historic British cathedral graduation ceremony: hundreds of university graduates in black gowns and blue silk hoods standing beneath towering stone arches. "
        "Lighting: warm golden volumetric light streaming down from high clerestory windows, illuminating the sea of graduation caps and golden stone pillars. "
        "Color: radiant warm gold, deep navy and black gowns, and sandstone ivory. "
        "Grand architectural perspective with soaring vaulted ceiling, celebration of global academic achievement. Standard global educational practice. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Dimly lit domestic room at night: a glowing computer monitor displaying online message boards with conflicting comments and questioned document scans. "
        "Lighting: harsh blue monitor glow on the keyboard and desk edge contrasted by a warm tungsten desk lamp casting long amber shadows across the wall. "
        "Color: warm amber and cool monitor cyan against deep domestic shadows. "
        "Over-the-shoulder medium perspective, atmospheric tension, realistic digital documentary aesthetic. Public suspicion and unfamiliarity. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Forensic investigative composition: sensationalist news clippings, printed viral blog posts, and red question mark annotations strewn across a dark investigator's desk. "
        "Lighting: stark overhead warm spotlight casting sharp chiaroscuro edges across crumpled papers and printed social media threads. "
        "Color: warm amber, faded newspaper grey, and deep timber brown against pitch-black shadows. "
        "Dynamic high-angle framing, shallow depth of field, dust motes in the light beam. Viral allegations taking root. No frame, no border, no collage, no text, no watermark."
    ),

    # BABAK 3: AUDIT DOKUMEN DAN PENYETARAAN RESMI (Shots 037 - 054)
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Imposing low-angle view of the Ministry of National Education headquarters building in Jakarta at dusk, bronze national emblem Garuda Pancasila gleaming above the main portico. "
        "Lighting: dramatic warm architectural uplighting illuminating the bronze national coat of arms against a deep twilight sky, shadowed granite steps below. "
        "Color: rich warm amber and gleaming bronze against dark slate and evening blue. "
        "Symmetrical low-angle perspective, authoritative institutional weight, subtle 35mm film grain. The legal gatekeeper of national credentials. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Vast state archive repository: endless rows of towering steel rolling file cabinets holding official foreign degree equivalency files, a ministry archivist carrying a blue dossier folder. "
        "Lighting: long vanishing line of warm overhead pendant lights casting alternating pools of golden light and dark shadow down the archive corridor. "
        "Color: warm amber (#FF9E3B), industrial steel grey, and dark floor shadows. "
        "Dramatic one-point linear perspective receding into deep gloom. Directorate General of Higher Education verification repository. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Credential evaluator's desk in forensic detail: passport with official immigration entry and exit stamps, semester credit conversion worksheets, and university accreditation registers. "
        "Lighting: strong directional tungsten desk lamp focused sharply onto the verification stamp pad and document pages, deep room falloff. "
        "Color: warm amber, passport burgundy, and aged paper cream against dark wood. "
        "Macro three-quarter perspective, tactile ink and paper details, uncompromising audit realism. Comprehensive factual credential evaluation. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Macro shot of an official ministry document submission registration receipt stamped with the year '2019' and the Directorate of Learning and Student Affairs seal. "
        "Lighting: warm tungsten raking light across the official receipt, highlighting the purple ink stamp impression, paper texture, and formal registration number. "
        "Color: warm amber, purple stamp ink, and cream paper against dark felt blotter. "
        "Close forensic framing, shallow depth of field, sharp documentary evidence. Formal application for national equivalence in 2019. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Government verification workstation: an investigator reviewing the UK Government official recognized higher education bodies portal showing the University of Bradford. "
        "Lighting: soft warm task lighting over the workstation, subtle warm screen glow illuminating official database entries, dark office surroundings. "
        "Color: warm amber light, soft monitor luminescence, and dark charcoal shadows. "
        "Medium over-the-shoulder angle with shallow focus on the screen text. State verification of foreign university legitimacy. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Official Indonesian Ministerial Decree document with the national Garuda Pancasila header: 'Surat Keputusan Direktur Jenderal Pembelajaran dan Kemahasiswaan Nomor 1300 Tahun 2019'. "
        "Lighting: warm tungsten downlight centered precisely on the header and legal preamble of the decree, casting soft shadows to the edges. "
        "Color: warm amber, crisp government document ivory, and dark typography against mahogany desk. "
        "Direct overhead flat-lay perspective, flawless legal clarity, 35mm archival fidelity. Formal government ministerial equivalence decree. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Forensic macro shot of the decisive verdict paragraph in the decree stating the degree is recognized as equivalent to 'Sarjana (S1)' in Indonesia, bearing official ministerial stamp and signature. "
        "Lighting: intense warm spotlight on the equivalence clause and the official purple government seal, deep shadows surrounding. "
        "Color: warm amber (#FF9E3B), violet stamp ink, and dark black signature ink on cream paper. "
        "Extreme macro depth of field, tactile paper fibers, undeniable legal resolution. Full bachelor equivalence status granted. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Symmetrical wide shot inside the General Elections Commission (KPU) legal candidate verification chamber: verified candidate filing boxes and legal staff at wooden tables. "
        "Lighting: warm institutional fluorescent and tungsten ambient lamps creating orderly pools of light across verification desks, election seals in background. "
        "Color: warm golden amber, cardboard archive brown, and dark timber paneling against shadows. "
        "Deep one-point perspective down the verification floor, disciplined state administrative atmosphere. Equivalence filing submitted to KPU. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Surakarta City Election Commission (KPU Surakarta) office during mayoral candidate registration: commissioners in formal batik inspecting verified candidate credential folders. "
        "Lighting: warm ceiling lighting creating a rich golden glow across traditional batik patterns, timber desk surfaces, and official candidate binders. "
        "Color: warm amber, batik earth tones (sogan), and deep mahogany against shadowed office walls. "
        "Medium three-quarter perspective, respectful administrative formality, 35mm documentary realism. Factual verification for Surakarta mayoral candidacy 2020. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Crowded press and verification hall at the national KPU headquarters during vice-presidential registration: journalists, security officers, and formal submission of candidate folders. "
        "Lighting: dynamic camera flashes popping against warm ambient hall chandeliers, casting sharp dramatic highlights across the ceremonial handover of files. "
        "Color: warm golden amber and bright specular flash highlights against dark suit fabrics. "
        "Wide journalistic perspective, high kinetic energy and tension, 35mm cinematic sharpness. Heightened scrutiny for 2024 presidential election. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Balai Kota Surakarta formal conference room at dusk: rows of microphones from various news networks arranged across a long dark conference table. "
        "Lighting: warm directional press spotlights illuminating the microphones, table surface, and podium, background receding into deep dignified shadow. "
        "Color: warm amber (#FF9E3B), polished dark timber, and sleek black microphone metal against obsidian shadows. "
        "Dramatic low-angle perspective looking along the table toward the speaker seat. Anticipation before direct public transparency. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Medium close-up of a black leather executive binder being unzipped and opened flat on the press table, revealing the pristine original foreign degree certificate inside protective plastic. "
        "Lighting: focused warm press spotlight gleaming on the zipper teeth and the smooth ivory parchment inside, surrounded by camera lenses. "
        "Color: warm honey amber, deep black leather, and parchment ivory against dark surroundings. "
        "Intimate three-quarter angle with shallow depth of field, high-stakes documentary revelation. The original archive presented to the media. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Over-the-shoulder view behind professional television cameras and DSLR zoom lenses focusing intensely on the displayed diploma document on the table. "
        "Lighting: rapid rhythmic camera flash pulses illuminating the document and camera viewfinders in brilliant contrast with warm room light. "
        "Color: warm amber ambient light and crisp white flash reflections against dark camera bodies. "
        "Dynamic journalistic framing, camera screens showing magnified document details, authentic media coverage. Journalists documenting the Bradford degree. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Extreme macro forensic shot of the embossed University of Bradford university seal: deep circular paper relief, crisp crest lettering, and the Vice-Chancellor signature in dark ink. "
        "Lighting: side-angled warm tungsten light creating pronounced three-dimensional micro-shadows inside the embossed paper indentations. "
        "Color: warm ivory paper tone, rich amber highlights, and dark archival ink. "
        "Extreme macro depth of field, individual paper fibers and ink edges razor sharp. Physical authenticity features of the degree. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Macro flat-lay of the official University of Bradford academic transcript sheet: columns of marketing course codes, credit values, modular marks, and security border pattern. "
        "Lighting: warm even tungsten light raking across the transcript grid, highlighting the official university watermark and paper texture. "
        "Color: warm amber light, pale cream security paper, and crisp black tabular typography. "
        "Direct overhead macro perspective, pristine documentary clarity, zero distortion. Comprehensive semester-by-semester grades. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Macro close-up of the official Indonesian Ministry of Education decree accompaniment: legal duty stamp (meterai) with cancellation signature and shimmering prismatic security hologram. "
        "Lighting: warm tungsten lamp catching the prismatic rainbow reflections of the ministry hologram alongside crisp blue ballpoint ink. "
        "Color: warm amber (#FF9E3B), iridescent rainbow hologram sheen, and deep blue ink on crisp white paper. "
        "Shallow depth of field, tactile tax stamp ridges, forensic state authenticity. Validated state equivalence decree with hologram. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Imposing symmetrical composition: the original British degree parchment and the Indonesian ministerial decree displayed side by side on a polished judicial oak lectern. "
        "Lighting: dual warm tungsten downlights casting solemn golden pools of light across both documents, deep obsidian shadows enveloping the background. "
        "Color: warm golden amber, cream parchment, and dark oak against pitch-black shadows. "
        "Direct front-facing perspective, balanced judicial dignity, 35mm film texture. Complete administrative and legal verification established. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Dramatic wide shot of the empty Balai Kota press room late at night after the media briefing: empty chairs, abandoned camera tripods, and a solitary warm maintenance light. "
        "Lighting: single overhead warm tungsten lamp casting a pool of light over the cleared table, long deep shadows stretching across the wooden hall floor. "
        "Color: warm amber and deep timber browns against cavernous dark shadows. "
        "Wide atmospheric perspective, poignant silence after media frenzy, subtle film grain. Physical proof versus persistent political storm. No frame, no border, no collage, no text, no watermark."
    ),

    # BABAK 4: ANATOMI NARASI DI RUANG PUBLIK (Shots 055 - 072)
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Moody conceptual darkroom: dozens of suspended smartphone screens glowing with viral social media comment threads, notification badges pulsing in warm amber and crimson. "
        "Lighting: deep obsidian darkness punctured only by the warm and crimson screen glows, casting faint colored rim light across floating dust particles. "
        "Color: warm amber, warning crimson, and dark slate against pitch-black shadows. "
        "Three-quarter floating perspective with dreamy bokeh, atmospheric digital echo chamber. The power of viral outrage over administrative fact. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Gritty montage: high-speed political pamphlet printing machinery in a dimly lit warehouse juxtaposed with glowing computer monitor timelines scrolling endlessly. "
        "Lighting: warm industrial pendant lamps casting harsh chiaroscuro shadows across metal rollers, flying paper sheets, and ink trays. "
        "Color: warm tungsten amber and machine oil black against shadowy industrial brick. "
        "Dynamic angled perspective, mechanical motion captured in sharp 35mm focus. Political commodification and endless reproduction of accusations. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Conceptual investigative blackboard in a shadowy war room: divergent chalk diagrams, competing speculative timelines, and conflicting claims branching across dark slate. "
        "Lighting: single directional warm gallery spotlight illuminating the chalk lines, dusty slate texture, and red connective strings. "
        "Color: warm amber (#FF9E3B), chalk white, and charcoal slate against deep room shadows. "
        "Dramatic three-quarter framing, chalk dust floating in the light cone, high conceptual tension. Fragmented narratives and contradictory theories. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Moody noir scene: an underground counterfeit print shop in deep shadows at midnight, an antique letterpress in the gloom, a single hanging bare bulb illuminating blank certificates. "
        "Lighting: harsh low-hanging bare tungsten bulb casting stark dramatic shadows up brick walls, heavy falloff into obsidian blackness. "
        "Color: warm amber filament glow, printer ink black, and dingy paper yellow against deep shadows. "
        "Atmospheric low-angle perspective, film noir investigative aesthetic, palpable tension. Dark allegations of counterfeit certificates. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Comparative forensic examination: an Indonesian vocational high school diploma placed on a lightbox alongside an international degree certificate. "
        "Lighting: cool translucent white lightbox illumination shining through the paper fibers, contrasted by warm amber ambient desk lamp light. "
        "Color: warm tungsten amber and translucent paper white against dark workshop shadows. "
        "Macro overhead angle, watermark transparency visible through the sheets. Misconceptions of vocational equivalency. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Archival photographic scrutiny: a vintage framed graduation photograph showing students in mortarboards and academic hoods, examined through a large magnifying glass. "
        "Lighting: warm directional reading light reflecting off the magnifying glass rim, illuminating the printed photographic grain and faces under scrutiny. "
        "Color: warm amber, sepia photographic tones, and dark mahogany against deep shadows. "
        "Macro optical framing, shallow depth of field, dust motes in the warm ray. Scrutiny of graduation pictures and ceremony claims. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Contemporary broadcast studio setting: a high-end broadcast dynamic microphone on an articulated boom arm, studio headphones, acoustic dark foam walls. "
        "Lighting: moody warm tungsten and amber neon edge lighting outlining the microphone silhouette and studio console in deep atmospheric gloom. "
        "Color: warm glowing amber, deep charcoal grey, and subtle brass accents against black acoustic panels. "
        "Cinematic close-up perspective, shallow depth of field, pristine broadcast realism. Public commentary and open podcast debates. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Macro view of an open British university academic regulations handbook on a polished oak lectern, open to the honours classification system page. "
        "Lighting: warm reading lamp light focused on the explanatory text defining 'Second Class Honours (Second Division)', deep shadows in the hall. "
        "Color: warm amber (#FF9E3B), aged book cream, and dark leather binding against dark oak. "
        "Extreme macro depth of field, crisp historic book typography, quiet analytical clarity. Deconstructing academic honours classifications. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Imposing low-angle shot outside the Central Jakarta District Court: monumental neoclassical stone pillars and heavy bronze double doors under dramatic evening illumination. "
        "Lighting: warm facade spotlights washing up the fluted stone columns, casting deep architectural shadows between porticoes under dusk sky. "
        "Color: warm sandstone amber and bronze patina against deep indigo twilight. "
        "Grand architectural perspective, authoritative judicial solemnity, 35mm film texture. Transition from social media debate to legal action. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Central Information Commission hearing chamber: a solid wood judicial bench, an official legal gavel resting on a leather block, formal public information petitions stacked neatly. "
        "Lighting: warm overhead courtroom downlights focused on the gavel and legal dossiers, deep shadows across empty counsel benches. "
        "Color: warm amber gold, polished walnut brown, and dark leather against courtroom shadows. "
        "Low-angle three-quarter framing, quiet judicial gravity, dust particles in the warm light cone. Public information disclosure disputes filed. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Dramatic courtroom interior during a civil lawsuit hearing: counsel tables covered in open legal lawbooks, judicial dais in background beneath the national coat of arms. "
        "Lighting: shafts of warm afternoon sunlight cutting diagonally through tall courtroom windows, illuminating floating dust motes and polished timber. "
        "Color: warm amber sunlight, deep mahogany, and dark green baize against cool stone shadows. "
        "Dynamic wide perspective, judicial formality, high legal drama in 35mm realism. Civil lawsuit demanding candidacy annulment. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Imposing exterior view of the University of Bradford Richmond Building in Yorkshire, UK: historic red-brick and stone university tower under an overcast northern sky. "
        "Lighting: warm tungsten interior lights glowing from university administrative windows against cool moody British overcast daylight. "
        "Color: warm glowing window amber and weathered red brick against slate grey sky. "
        "Grand architectural perspective, autumnal trees framing the campus, documentary gravitas. Direct institutional response from the United Kingdom. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Official University of Bradford press statement on heavy institution letterhead resting on an executive oak desk, signed by the university registrar. "
        "Lighting: focused warm brass desk lamp casting a clean pool of light over the letterhead, official signature, and the graduation confirmation text of 2006. "
        "Color: warm amber (#FF9E3B), crisp letterhead white, and rich oak brown against dark shadows. "
        "Macro flat-lay perspective, tactile paper grain and ink signature, authoritative confirmation. University officially confirms 2006 graduate status. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Dignified British Embassy reception room in Jakarta: polished dark wood wall paneling, a large embossed British royal coat of arms in gleaming brass. "
        "Lighting: warm recessed chandelier lighting casting soft, prestigious golden reflections across the brass royal emblem and fine timber paneling. "
        "Color: warm amber gold, antique brass, and dark mahogany against deep room shadows. "
        "Symmetrical medium perspective, stately diplomatic atmosphere, subtle 35mm grain. British diplomatic and quality assurance affirmation. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Solitary figure in dark silhouette standing before a towering wall of flickering digital monitors displaying relentless online political debates. "
        "Lighting: deep obsidian darkness contrasted by the intense warm amber and copper glow emanating from the video wall, illuminating dust particles in air. "
        "Color: warm radiant amber and copper against pitch-black void. "
        "Dramatic wide perspective with deep vanishing point, evocative conceptual documentary mood. Persistent resistance despite official verifications. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Conceptual psychological composition: an authentic golden framed diploma displayed behind thick glass in a quiet archival hall, while outside through windows blurred crowds debate in shadow. "
        "Lighting: warm radiant spotlight inside the glass case illuminating the parchment, cool shadowy exterior. "
        "Color: warm golden amber and cream parchment against cool shadow tones. "
        "Intimate three-quarter perspective, reflective glass texture, deep thematic symbolism. The psychology of digital confirmation bias. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Archival forensic darkroom: official government verification documents examined under an ultraviolet forensic detection light, revealing authentic glowing security fibers. "
        "Lighting: ultraviolet blue luminescence revealing glowing green and amber security fibers on the paper, framed by ambient warm tungsten desk light. "
        "Color: glowing fluorescent amber-green security fibers and deep navy under warm room falloff. "
        "Extreme macro depth of field, undeniable scientific authenticity. Forensic proof versus conspiracy theories. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Intimate atmospheric shot inside a voting booth on election day: the voting screen curtain in shadow, an official ballot paper resting on the wooden shelf under a single warm hanging bulb. "
        "Lighting: single warm tungsten bulb directly overhead creating a concentrated cone of golden light on the ballot paper, deep shadows enveloping the booth. "
        "Color: warm amber (#FF9E3B), ballot paper ivory, and raw plywood brown against dark shadows. "
        "Medium POV perspective, solemn democratic moment, subtle 35mm film grain. Weaponization of narratives in the voting booth. No frame, no border, no collage, no text, no watermark."
    ),

    # BABAK 5: REFLEKSI KREDIBILITAS DAN AKUNTABILITAS PUBLIK (Shots 073 - 090)
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Stately legal archive: a massive, thick leather-bound volume of the State Gazette of the Republic of Indonesia (Lembaran Negara) opened on a ceremonial carved teak dais. "
        "Lighting: warm overhead library chandelier lighting casting rich golden highlights across gilt-edged pages and embossed leather binding. "
        "Color: warm amber gold, deep burgundy leather, and dark teak wood against deep archival shadows. "
        "Dramatic three-quarter low-angle framing, solemn constitutional gravitas. The ironies of national electoral law. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Macro forensic view of the open statute book of Election Law Number 7 of 2017: the legal clause specifying minimum education requirements for presidential candidates. "
        "Lighting: directional warm tungsten reading lamp raking across the printed legal text: 'berpendidikan paling rendah tamat sekolah menengah atas atau sederajat'. "
        "Color: warm amber, crisp paper ivory, and deep charcoal legal typography. "
        "Extreme macro depth of field, tactile paper grain, razor-sharp statutory clarity. The statutory high school minimum requirement. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Symmetrical wide shot of the grand courtroom of the Constitutional Court of Indonesia (Mahkamah Konstitusi): the elevated bench with nine judicial chairs beneath the national seal. "
        "Lighting: dignified warm architectural cove lighting illuminating the curved wooden dais and red carpet, stately shadows along the gallery. "
        "Color: warm golden amber, ceremonial red, and deep polished timber against soft shadows. "
        "Majestic one-point vanishing point perspective, solemn constitutional authority, 35mm film texture. Constitutional legality satisfied without a university degree. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Close macro shot of an antique bronze balance scale of justice resting perfectly balanced on a dark courtroom table, leather legal books stacked beside it. "
        "Lighting: dramatic warm rim lighting tracing the contours of the bronze pans and balance beam against deep mahogany background. "
        "Color: warm antique brass gold and dark timber brown against obsidian shadows. "
        "Shallow depth of field, dust motes in the warm light beam, timeless symbolic balance. Legal compliance versus political disputes. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Warm interior of a traditional Javanese pendopo hall: ornate carved teak walls proudly adorned with framed academic degree certificates and family honors. "
        "Lighting: warm glowing oil lamps and hanging lanterns casting a rich amber-honey glow across intricate teak carvings and glass frames. "
        "Color: warm amber (#FF9E3B), honeyed teak wood, and antique parchment cream. "
        "Medium three-quarter perspective, cultural reverence for educational symbols, 35mm documentary warmth. Indonesian cultural veneration of academic titles. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Solemn wide shot from the columned veranda of the Presidential Palace at dusk, looking out toward the National Monument (Monas) glowing in the distance. "
        "Lighting: warm sunset amber washing across marble palace pillars and balustrades, contrasting with the darkening evening sky and illuminated city monuments. "
        "Color: warm sunset gold, white marble ivory, and deep twilight slate blue. "
        "Grand architectural perspective, profound historic reflection, subtle film grain. Academic credentials as symbols of public trust and moral capacity. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Stately national archive hall: towering wooden bookshelves filled with biographies of national leaders, presidential records, and historic state registers. "
        "Lighting: warm vertical shafts of late-afternoon sunlight cutting through tall arched windows, illuminating floating dust motes and endless leather spines. "
        "Color: warm amber gold, deep aged leather, and dark oak against soft shadows. "
        "Dramatic one-point perspective down the grand archival hall. The weight of public leadership accountability. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Contemporary university lecture auditorium in Indonesia: an academic professor presenting international educational mobility and credit transfer frameworks on a large interactive screen. "
        "Lighting: warm modern downlights creating an engaging, scholarly environment across rows of attentive university students. "
        "Color: warm honey amber, soft screen illumination, and deep wood tones. "
        "Wide perspective from the mid-auditorium, vibrant intellectual atmosphere, 35mm clarity. The vital lesson for international educational literacy. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Conceptual wide architectural visual: an illuminated global academic network map on an interactive display table, glowing golden connection lines bridging Jakarta, Singapore, Sydney, and London. "
        "Lighting: warm golden luminescence radiating from the digital map surface, casting gentle amber reflections on the faces of gathered observers in a dark room. "
        "Color: radiant warm gold, deep obsidian slate, and copper highlights. "
        "Dramatic high-angle perspective, deep vanishing points, inspiring visual continuity. Higher education transcending borders. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Modern open-plan government digital service center: ministry officers assisting citizens at sleek wooden information counters with transparent digital credential verification kiosks. "
        "Lighting: warm contemporary overhead linear pendant lights illuminating the desks, creating a bright, transparent public service ambiance. "
        "Color: warm amber (#FF9E3B), clean architectural white, and light oak wood. "
        "Deep linear perspective through the public service hall, dignified civil transparency. Ministry reforms in public credential access and transparency. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Macro shot of a public official's hand signing an official integrity and voluntary transparency charter with a classic fountain pen on heavy woven paper. "
        "Lighting: focused warm tungsten desk lamp highlighting the wet black ink flowing from the gold pen nib onto the document, deep background shadows. "
        "Color: warm amber, gleaming gold pen accents, and crisp white paper against dark mahogany. "
        "Extreme macro depth of field, ink sheen, tactile paper texture. The ethical obligation of public disclosure. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Dramatic coastal scene: a sturdy stone lighthouse perched atop a rocky cliff at dusk, casting a brilliant, warm golden beam of light cutting through heavy storm clouds over dark waters. "
        "Lighting: powerful warm tungsten searchlight cutting through mist, warm sunset embers on the horizon contrasting with dark tempestuous sea swells. "
        "Color: blazing golden amber, oceanic navy blue, and wet granite charcoal. "
        "Epic wide perspective with dramatic sea horizon, cinematic documentary grandeur. Proactive transparency dispelling political storms. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Grand interior view of the Indonesian National Parliament plenary chamber (Gedung DPR/MPR): majestic domed ceiling and sweeping tiers of green seating under formal state chandeliers. "
        "Lighting: warm golden ambient chandeliers washing across the national assembly hall, casting dignified architectural shadows across the rostrum. "
        "Color: warm amber gold, assembly green upholstery, and rich timber walls against soft shadows. "
        "Symmetrical grand perspective, dignified democratic institution, 35mm cinematic weight. Healthy democracy rising above prejudice. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Forensic laboratory examination table: the authentic University of Bradford diploma resting securely between official verification seals and legal certificates of authenticity. "
        "Lighting: multi-point warm balanced laboratory spotlights providing immaculate, shadow-free illumination across the documents. "
        "Color: warm amber (#FF9E3B), pristine parchment cream, and dark walnut table tones. "
        "Direct three-quarter perspective, razor-sharp documentary evidence, flawless physical preservation. Forensic confirmation of legal and administrative authenticity. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Intimate medium shot of a statesman in formal batik speaking sincerely at an open forum with citizens, warm natural eye contact and respectful listening atmosphere. "
        "Lighting: warm natural side lighting casting soft humanizing contours across faces, gentle shadows in the background hall. "
        "Color: warm amber tones, rich batik browns, and soft skin highlights. "
        "Shallow depth of field, authentic emotional resonance, 35mm documentary warmth. Humble and convincing public communication. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Artistic macro composition: an ancient brass seal stamp and wax resting beside an unrolled vintage map of the Indonesian archipelago on an executive oak desk. "
        "Lighting: low-angle warm tungsten light casting long evocative shadows across the islands and straits of the map, highlighting bronze textures. "
        "Color: warm golden amber, antique parchment ochre, and deep timber brown. "
        "Macro diagonal perspective, dust motes floating in the beam, timeless poetic symbolism. Leadership measured beyond bureaucratic stamps. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Panoramic cinematic montage of Indonesian national progress: farmers working in golden terraced rice paddies, engineers at modern infrastructure bridges, all bathed in majestic golden hour sunlight. "
        "Lighting: radiant late-afternoon golden sun washing across the landscape, casting warm long shadows and golden rim light over people and structures. "
        "Color: blazing golden amber, rich earth tones, and warm sky gradients. "
        "Sweeping epic wide landscape perspective, deep atmospheric haze, inspiring cinematic documentary realism. Leadership proven through service to the people. No frame, no border, no collage, no text, no watermark."
    ),
    (
        "Cinematic 35mm film still, 16:9 full-bleed. Symmetrical closing shot: the presidential podium standing dignified before the national red-and-white flag inside the state palace, illuminated by a single vertical golden shaft of light from above. "
        "Lighting: a dramatic vertical beam of warm golden tungsten sunlight cutting through the high palace ceiling, illuminating dust motes dancing in the air, deep chiaroscuro shadows framing the stage. "
        "Color: warm radiant amber (#FF9E3B), national red and white, and rich dark teak wood against obsidian shadows. "
        "Solemn one-point perspective, monumental gravitas, delicate 35mm film grain. The eternal mirror of national political legitimacy and truth. No frame, no border, no collage, no text, no watermark."
    )
]

def build():
    chunks = get_narration_chunks()
    assert len(chunks) == 90, f"Expected 90 chunks, got {len(chunks)}"
    assert len(PROMPTS) == 90, f"Expected 90 prompts, got {len(PROMPTS)}"

    shots = []
    for i in range(90):
        ch_num = (i // 18) + 1
        s_id = f"shot_{i+1:03d}"
        
        # Shot types rotation: WS -> CU -> MS -> MCU -> WS ...
        shot_types = ["WS", "CU", "MS", "MCU", "ECU", "POV"]
        st = shot_types[i % len(shot_types)]
        
        s = {
            "id": s_id,
            "chapter": ch_num,
            "narration": chunks[i],
            "visual_prompt": PROMPTS[i],
            "shot_type": st,
            "duration_hint": 7
        }
        shots.append(s)
        
        # Write individual script file
        txt_file = SCRIPT_DIR / f"{s_id}.txt"
        txt_file.write_text(chunks[i] + "\n", encoding="utf-8")

    data = {
        "style": "Cinematic Chiaroscuro Warm Tungsten & Forensic Documentary",
        "description": "Full-color 35mm cinematic live-action documentary style for Kontroversi Ijazah Gibran. Warm tungsten desk lamps, archival spotlighting, bronze reading lamps, dramatic chiaroscuro falloff into deep obsidian shadows, dust particles in volumetric light beams, deep vanishing points, zero collage, zero frames.",
        "shots": shots
    }

    OUT_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Storyboard a057 generated: {OUT_FILE} (90 shots)")
    print(f"✓ Script files generated in {SCRIPT_DIR} (90 files)")

if __name__ == "__main__":
    build()
