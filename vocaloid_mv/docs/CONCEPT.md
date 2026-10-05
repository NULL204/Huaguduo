# 花骨朵 — concept

Fan-made Vocaloid-style (V家手书 / 文字PV) lyric MV for 《花骨朵》 (vocal: 洛天依), built with the
vocaloid-style-mv-pipeline. Lyrics are shown from the user's official LRC; this repo stores only timings and
markup positions.

## Thesis

**Usefulness is pressed out of the living.** Rouge is made by crushing a living insect; a bud becomes "a flower
people like to look at" by being forced open; a pressed flower keeps its colour by being flattened and labelled.
The film is a **herbarium** (标本册): every frame is a page the world keeps of her — catalogue numbers, labels,
pins, glassine sheets — and the red in the world (rouge, wedding red, warning stamps) is pigment taken from her.
She tries not to be pressed. She blooms anyway, alone, and the world files her as a specimen.

**Logline.** 阿朵 is the last closed bud on a branch that survived the winter. Everything around her wants her
open, coloured and useful — a bride, a worker, a pressed flower in someone's album; she runs from house to spring
to office through the seasons, tears herself off the branch, and blooms — on a branch nobody looks at.

## Emotional arc per section (bars from `analysis/sections.json`)

| section | bars / time | arc | treatment |
|---|---|---|---|
| Intro | 1–8 · 0:00–0:16 | promise: a specimen page waits | white page, one red bud; labels type in; the two stops (11.0, 14.85 s) are stamp hits; title |
| Refrain 1 | 9–16 · 0:16–0:32 | bewildered question | late-spring afternoon, open sky; left/right; the cochineal in her palm |
| Verse | 17–24 · 0:32–0:48 | the cold before her | last winter in blue-grey; a sun that won't rise; an empty lane |
| B1 | 25–32 · 0:48–1:04 | first "I want": a house | warm lantern red against white mourning silver; the bride; rouge |
| B2 | 33–40 · 1:04–1:20 | second "I want": to die in spring | spring explodes green+red, she lies in the flowers; silverfish eat the page |
| Refrain 2 | 41–48 · 1:20–1:36 | the question becomes an accusation | night, rouge-neon, a factory of red; crushed insects; hands |
| B3 | 49–56 · 1:36–1:52 | "don't forget me" — quiet | dim sepia room, one window; two sleepers, two dreams; the hide |
| B4 | 57–64 · 1:52–2:08 | "not like this" | fluorescent office white; solar-term calendar stamps; the child self fades |
| Refrain 3 | 65–72 · 2:08–2:24 | the last asking: the bud itself | summer green with snow falling; she tears off the stem; the bud cracks |
| Outro | 73–80 · 2:24–2:40 | refusal → the bloom | red takes the frame; the bloom; hard cut on the dead stop (160.19 s) |
| Tail | 2:40–2:50 | the world's verdict | silent herbarium page: the bloom pressed flat, labelled; credits |

## Colour script (new palettes; none of 残光's P1–P5)

- **H1 宣纸 paper** (intro, outro end card): paper white #F4EEE4, ink #1B1420, carmine #C8183C — monochrome + one red.
- **H2 晚春 late spring** (refrain 1): sky haze #DCE7EE, blossom white #FFF6F2, petal pink #F2B8C0, carmine accent.
- **H3 去冬 last winter** (verse): snow #E9EEF3, slate #6F7E93, deep blue-grey #2B3446 — red nearly absent.
- **H4 红白 red & white** (B1): lantern red #B3122E, mourning silver #D9DCE3, gold #D9A55B, ink.
- **H5 春泥 spring mud** (B2): grass #5E9A4E, young green #B9D27A, poppy red #D7263D, mud #3B2A22.
- **H6 胭脂夜 rouge night** (refrain 2): indigo #141433, rouge neon #FF3D6E, carmine #C8183C.
- **H7 旧照 old photo** (B3): sepia #CBB79A, dusk grey #6D6470, faded red #A4505A.
- **H8 荧光 fluorescent** (B4): office white #F2F5F5, cyan-grey #A9BCC4, alarm red #E0243C.
- **H9 六月雪 June snow** (refrain 3): summer green #4F8F45, white snow, sunlight #FFF3C8, carmine.
- **H10 绽 bloom** (outro): carmine field #B0102E → rouge pink #FF6B88 → white flash.

One palette per shot; changes on cuts. A full-red frame is an event (B1 rouge stroke, outro bloom).

## Shapes & motifs

- **Master shape — the bud/teardrop**: the closed poppy bud (her hairpin), drops of rouge, tears, the 。 of
  typography, iris transitions shaped like a bud. State change: closed (intro) → split (refrain 2) → cracking
  (refrain 3) → open (outro).
- **Secondary shape — the specimen label/frame**: rectangles with catalogue numbers, pins, glassine sheets; the
  HUD and the lyric plates are labels; the world keeps trying to frame her.
- **Rouge (pigment extraction)**: insect → crushed → red smear → lipstick stroke → wedding red → office stamps.
- **Silverfish (衣鱼)**: forgetting; they eat the paper image itself (holes in the frame and in the text).
- **Solar terms**: time as stamps (惊蛰 … 霜降), 16 seals on eighth notes.
- **Motion prop**: her long carmine 披帛 (silk shawl) — streams in every wind; in the outro it becomes the petals.

## Typography voice

Song/Ming serif (Noto Serif SC, Zen Old Mincho) for feeling; heavy gothic (Dela Gothic One, Zen Kaku Gothic New
Black) for slams; Klee One handwriting for memory/label notes; DotGothic16 for catalogue numbers and the HUD.
JIZURA plans per section (light schemes on white pages, dark schemes at night). Scene-owned typography for the
キメ lines: 胭脂妆, 死, 少年郎, 花骨朵, 无人问津.

## Signature moments

1. **Title on the specimen page** (0:00–0:16): a pressed red bud; catalogue label types in; the stops at 11.0 s and
   14.85 s are two stamp slams; the title seal lands on the vocal pickup at 15.85 s.
2. **胭脂虫 in the palm** (0:22.9): macro of her hand; the insect is pressed → red bleeds into the lyric text.
3. **A sun that won't rise** (0:34.9): pale disc behind frost; it sinks on the line end.
4. **胭脂妆!** (0:56.9): a giant lipstick stroke wipes the frame red on the downbeat.
5. **死在春天里!** (1:04.3): spring explodes around her lying figure; 死 slams in red.
6. **Silverfish eat the page** (1:14.9): holes spread through image and lyrics into black.
7. **惊蛰→霜降** (1:54.9): 16 solar-term seals stamp on eighth notes; day/night strobes.
8. **少年郎!** (2:02.9): her child self fades into petals beside the desk.
9. **花骨朵!** (2:18.5): June snow; the bud hairpin cracks open; giant 花骨朵 behind her.
10. **The bloom + hard cut** (2:30.9–2:40.2): red takes the frame; dead stop → silent herbarium page with the
    pressed bloom labelled 「无人问津」; credits in the label.

## Different from the 残光 example (variation matrix)

| axis | 残光 | 花骨朵 |
|---|---|---|
| world | suburb at dusk | herbarium pages + Chinese lanes, courtyard, office |
| time arc | dusk→night→dawn | seasons: late spring→winter→spring→summer |
| key | low-key night | mostly high-key paper daylight (§13), two night sections |
| palette | afterglow amber/violet | ink + carmine monochrome, seasonal accents |
| master shape | circle + crack | bud/teardrop + specimen label |
| material | glass & light | paper, pigment (rouge), pressed flowers |
| motion prop | wrist ribbon | silk 披帛 shawl |
| typography | mincho + gold | serif + catalogue labels + seals |
| 3D | Blender flythroughs | none: layered 2.5D pages |
| transitions | irises + shatter | page turns, pigment wipes, eaten holes, bud irises |
| ending | cyan afterimage | the bloom pressed into the album |
