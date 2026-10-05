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

**Logline.** The last closed bud on a branch that survived the winter. Everything around her wants her open,
coloured and useful — a bride, a worker, a pressed flower in someone's album; through house, spring and office she
refuses, tears herself off the stem, and blooms — on a branch nobody looks at.

**Protagonist = the bud.** The interpretation this film follows reads the song from the bud's side
(「主角就是花骨朵本身」), so there is no drawn singer: the protagonist is a poppy bud drawn as a botanical plate, nodding
on its hairy stem (poppy buds hang their heads and straighten just before they open — submission → defiance), with
her red as the only warm colour in a world of ink and paper. `CHARACTER.md` and `tools/build_jobs.py` stay in the
repo for a possible later version with a generated singer (阿朵); this version uses no image assets at all.

## Emotional arc per section (bars from `analysis/sections.json`)

| section | bars / time | arc | treatment |
|---|---|---|---|
| Intro | 1–8 · 0:00–0:16 | promise: a specimen page waits | white page, one red bud; labels type in; the two stops (11.0, 14.85 s) are stamp hits; title |
| Refrain 1 | 9–16 · 0:16–0:32 | bewildered question | late-spring afternoon, open sky; left/right; the cochineal in her palm |
| Verse | 17–24 · 0:32–0:48 | the cold before her | last winter in blue-grey; a sun that won't rise; an empty lane |
| B1 | 25–32 · 0:48–1:04 | first "I want": a house | lantern red against mourning silver; 房 opens like a door; a lacquer box closes; rouge; a veil over nobody |
| B2 | 33–40 · 1:04–1:20 | second "I want": to die in spring | spring explodes green+red; a robe of poppies laid on the grass; silverfish eat the page |
| Refrain 2 | 41–48 · 1:20–1:36 | the question becomes an accusation | night, rouge neon, a press crushing a row of insects; the bud splits |
| B3 | 49–56 · 1:36–1:52 | "don't forget me" — quiet | an old photo of the sheet; a glassine skin peeled back; two text columns on one bed, two dreams |
| B4 | 57–64 · 1:52–2:08 | "not like this" | fluorescent office white; solar-term seals; a conveyor of identical buds; 少年郎 dissolves |
| Refrain 3 | 65–72 · 2:08–2:24 | the last asking: the bud itself | summer green with snow falling; she tears off the stem; the bud cracks |
| Outro | 73–80 · 2:24–2:40 | refusal → the bloom | red takes the frame; the bloom; hard cut on the dead stop (160.19 s) |
| Tail | 2:40–2:50 | the world's verdict | silent herbarium page: the bloom pressed flat, labelled; credits |

## Colour script

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

- **Master shape — the bud/teardrop**: the closed poppy bud (the protagonist), drops of rouge, tears, the 。 of
  typography, iris transitions shaped like a bud. State change: closed (intro) → split (refrain 2) → cracking
  (refrain 3) → open (outro).
- **Secondary shape — the specimen label/frame**: rectangles with catalogue numbers, pins, glassine sheets; the
  HUD and the lyric plates are labels; the world keeps trying to frame her.
- **Rouge (pigment extraction)**: insect → crushed → red smear → lipstick stroke → wedding red → office stamps.
- **Silverfish (衣鱼)**: forgetting; they eat the paper image itself (holes in the frame and in the text).
- **Solar terms**: time as stamps (惊蛰 … 霜降), 16 seals on eighth notes.
- **Motion**: the stem's nod (head down = submission, head up = refusal); in the outro a wisp of red silk becomes the petals.

## Typography voice

Song serif (Noto Serif SC) for feeling; Ma Shan Zheng brush for the キメ words; ZCOOL QingKe HuangYou and Noto Sans SC
Black for the office and factory; Long Cang handwriting for labels, captions and the child's 少年郎; ZCOOL XiaoWei and
Zhi Mang Xing for classical columns and the outro; DotGothic16 for catalogue numbers and the HUD.
JIZURA plans per section (light schemes on white pages, dark schemes at night). Scene-owned typography for the
キメ lines: 胭脂妆, 死, 少年郎, 花骨朵, 无人问津.

## Signature moments

1. **The specimen sheet** (0:00–0:16): the bud writes itself as a botanical plate; the label types in; the stop at
   11.0 s lands the seal 「待开」 ("to be opened"); the stop at 14.85 s is the title in silence.
2. **胭脂虫** (0:22.6): the cochineal under a magnifier is crushed on the downbeat → its red floods the lyric.
3. **A sun that won't rise** (0:34.1): the glyph 日 is the sun; it rises, stalls and sinks back.
4. **胭脂妆!** (0:56.6): a giant rouge brush stroke wipes the frame red.
5. **死在春天里!** (1:04.1): 死 slams in carmine and poppies burst open around it.
6. **Silverfish eat the page** (1:14.1): holes spread through picture and lyric until neon shows through.
7. **惊蛰→霜降** (1:54.6): 16 solar-term seals stamp on eighth notes.
8. **少年郎!** (2:02.1): the child's handwriting dissolves into petals.
9. **花骨朵!** (2:18.1): June snow; the bud lifts its head, cracks and tears free while 花 骨 朵 slam behind it.
10. **The bloom + hard cut** (2:30.6–2:40.2): red takes the frame, the poppy opens alone on a bare branch; dead
    stop → the silent herbarium sheet with the pressed bloom and the seal 「无人问津」.
