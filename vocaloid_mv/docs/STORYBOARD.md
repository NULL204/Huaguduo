# 花骨朵 — storyboard (v1)

Song 170.4 s, 120.4 BPM, 80 bars; music stops dead at **160.19 s**. Film = 160.19 s + a 7.4 s silent end card.
Times: `B(n)` = start of bar n (`analysis/audio.json` bars[].index), `nb(t)` = nearest beat. `Ln` = lyric line n of the
user's LRC (0-based, `analysis/lyrics_source.lrc`, never committed). Per-glyph onsets: `analysis/char_timing.json`.

**Protagonist.** No drawn singer. The interpretation the film follows says 「主角就是花骨朵本身」: the protagonist is the
poppy bud. It nods on a hairy stem (poppy buds hang their heads and straighten just before they open), survives the
winter, is pressed for its colour, lifts its head in June snow, tears free and blooms — on a branch nobody looks at —
and is filed as a specimen. Red in the frame is always *her*; the world is ink, paper and seasonal tints.

**Look.** Two-colour print on rice paper (sumi ink `#1B1420` + carmine `#C8183C`), one seasonal tint per section,
botanical-engraving line art, Chinese type (Noto Serif SC / Ma Shan Zheng brush / Long Cang hand / ZCOOL QingKe
heavy), misregistered red under ink, seals, specimen labels. Post: line boil 0.6–1.0, grain, low bloom on paper
(daylight settings), more bloom and CA at night and in the climax.

**Typography.** Two voices: JIZURA (curated `paper` / `specimen` / `crimson` plans, light text schemes on paper) for
9 narrative lines, and scene-owned typography (lyric `'none'`) where the words *are* the image (日 as the sun, 房 as a
house, 死 slammed, 少年郎 dissolving into petals, 花骨朵 behind the bud, 无人问津 as a seal).

**Colour script.** H1 paper (intro, end) · H2 late spring blush (refrain 1) · H3 winter blue-grey (verse) · H4 red &
silver (B1) · H5 spring green (B2) · H6 rouge night indigo + neon (refrain 2) · H7 sepia photo (B3) · H8 fluorescent
white + alarm red (B4) · H9 June snow on summer green (refrain 3) · H10 carmine field → bloom (outro).

**Scene files.** `engine/scenes/hgd_core.js` (shared kit, `Z.HGD`), `hgd_page.js` (hPage, hType), `hgd_refrain.js`
(hForget, hCross, hInsect), `hgd_winter.js` (hWinter), `hgd_house.js` (hHouse), `hgd_spring.js` (hSpring,
hSilverfish), `hgd_office.js` (hBed, hOffice, hYouth), `hgd_bloom.js` (hBud, hSlam, hTunnel, hWisp, hBloom).

## Shot list

| id | t0 → t1 | scene · mode | lyric | picture | sync points | in |
|---|---|---|---|---|---|---|
| **INTRO** H1 | | | | | | |
| s01 | 0 → 11.00 | hPage · intro | none | black → rice-paper herbarium sheet; a carmine drop falls and blooms into a stain; sheet marks, scale bar, `No.0507` type in; the bud writes itself as a botanical plate (stem 4.10→6.6, bud 6.6→7.4, hatch + bristles 7.4→8.5, wash 8.5→9.5, red slit); specimen label types in 8.1→10.8; slow push | drop 0.55 · pin 3.37 · tape strip 7.37 | — |
| s02 | 11.00 → 14.85 | hPage · stamp | none | STOP 11.00–11.38: the frame holds (no motion, grain only); seal 「待开」 stamps on the label at 11.36 with a jolt; camera glides label → bud close-up; the red slit pulses | stamp 11.36 · pulse 13.56 | cut |
| s03 | 14.85 → 15.89 | hType · title | none | STOP 14.85–15.54: hard cut to the title 「花骨朵」 (brush, ink, huge, cropped) + small seal + HUAGUDUO / vocal 洛天依; holds in the silence, pushes when the music returns | 15.54 | cut |
| **REFRAIN 1** H2 | | | | | | |
| s04 | 15.89 → 17.89 | hForget · paper | L0 scene | blush paper, petals; the line types per glyph; then glyphs lose strokes (eraser bites, fading to grey) — forgetting | glyph onsets | flash `#FBE3E6` |
| s05 | 17.89 → 22.56 | hCross · day | L1 JIZURA `paper` | a grey band and a carmine band cross (left / right); thin ← → arrows; petals in wind | cross at B(11)=19.99 | cut |
| s06 | 22.56 → 26.03 | hInsect · crush | L2 scene | magnifier on paper: the cochineal + label 胭脂虫 Dactylopius coccus; the line types below; a press block slams on the insect at B(13)=24.08 → splat; the red floods into the text | slam 24.08 · drip 25.37 | cut |
| s07 | 26.03 → 30.03 | hBud · refrain | L3 scene | bud-iris from the splat into the nodding bud; giant pale 「花骨朵」 behind; L3 vertical, last 3 glyphs carmine; slit glows on the last glyph | glyph onsets · 28.91 | budIris |
| s08 | 30.03 → 34.10 | hWinter · frost | L4 JIZURA `winter` | colour drains; frost grows in from the edges; snow begins; blue-grey | frost 30.03→32.09 | xfade |
| **VERSE** H3 | | | | | | |
| s09 | 34.10 → 38.08 | hWinter · sun | L5 scene | horizon; first 4 glyphs vertical; the glyph 日 is the sun: rises 36.13→37.5, stalls, sinks by 38.0 (the sun that will not rise) | glyph onsets | cut |
| s10 | 38.08 → 42.08 | hWinter · lane | L6 scene | one-point-perspective empty lane, closed gates, snow; the glyphs sit on the wall panels receding; slow dolly | glyph onsets | push |
| s11 | 42.08 → 46.40 | hWinter · branch | L7 JIZURA `winterCF` | a bare branch of withered grey buds and one living bud; camera pans to it; long shadows on snow | a dead bud drops 44.51 | cut |
| s12 | 46.40 → 48.09 | hType · want | L8 scene | GAP 46.40–46.54 = black; then the line small in paper-white on ink | glyph onsets | cut |
| **B1** H4 | | | | | | |
| s13 | 48.09 → 50.59 | hHouse · house | L9 scene | 房 drawn as an architectural elevation (stroke write-on); its door (户) swings open on lantern red | open 49.60 | flash `#FFF1E6` |
| s14 | 50.59 → 54.09 | hHouse · box | L10 scene | the line types; a red lacquer box builds around it; the lid closes on the downbeat | close B(28)=54.09 | cut |
| s15 | 54.09 → 56.56 | hHouse · wrap | L11 scene | silver-white silk strips wrap across the frame, one per beat; silver serif | 54.56 55.07 55.56 56.05 | cut |
| s16 | 56.56 → 58.09 | hHouse · rouge | L12 scene (キメ) | a giant rouge brush stroke swipes the frame carmine; the three glyphs slam in paper-white brush | 56.85 57.17 57.49 | cut |
| s17 | 58.09 → 62.09 | hHouse · veil | L13 scene | hollow gold calligraphy columns on red paper, clouds; a red veil with gold fringe falls at 60.06, lifts at 61.6 — nothing underneath | 60.06 · 61.6 | wipe |
| s18 | 62.09 → 64.07 | hType · want2 | L14 scene | the "I want" line again, carmine on paper, larger | glyph onsets | cut |
| **B2** H5 | | | | | | |
| s19 | 64.07 → 66.10 | hSlam · death | L15 scene (キメ) | 死 slams huge in carmine brush on green paper; poppies burst open around it; the rest of the line small; flowers start to grow over the glyph | 64.18 · 64.41 · 65.6 | flash `#FFFFFF` |
| s20 | 66.10 → 70.09 | hSpring · bed | L16 JIZURA `paperCF` | top-down meadow; a robe laid flat, made of red poppies (no body); petals drift; slow rotation, pull back | — | cut |
| s21 | 70.09 → 74.08 | hSpring · grow | L17 scene | grass and vines grow from the mud in spurts per beat, curling around the glyphs until green covers them | beats | cut |
| s22 | 74.08 → 79.57 | hSilverfish | L18 scene | a printed page (line + spring plate); silverfish crawl in from 75.07, holes spread along their paths and bite the glyphs; by 79.3 the page is mostly gone and neon glows through the holes | 75.07 → 79.3 | cut |
| **REFRAIN 2** H6 | | | | | | |
| s23 | 79.57 → 81.56 | hForget · neon | L19 scene | neon type on indigo, strokes flicker out (glitch) | downbeat 80.09 | cut |
| s24 | 81.56 → 86.87 | hCross · night | L20 JIZURA `night` | two neon arrow signs alternate per beat; bands cross faster | beats | cut |
| s25 | 86.87 → 90.37 | hInsect · press | L21 scene | a hydraulic press slams on 4 beats over a row of insects; red spurts and runs in channels | 86.87 87.38 87.85 88.35 | cut |
| s26 | 90.37 → 94.04 | hBud · night | L22 JIZURA `nightCF` | the bud under neon, sepals split; giant neon outline 「花骨朵」 behind; beat zooms | beats | flash `#FF3D6E` |
| s27 | 94.04 → 96.08 | hType · dont | L23 scene | quiet: the line in white on near-black, dust | glyph onsets | black |
| **B3** H7 | | | | | | |
| s28 | 96.08 → 98.59 | hPage · photo | L24 scene | an old sepia photograph of the specimen page; the line handwritten on its border; the print yellows | glyph onsets | xfade |
| s29 | 98.59 → 102.57 | hPage · glassine | L25 JIZURA `spec` | the specimen under a milky glassine sheet that peels back from a corner | peel 99.1→101.5 | cut |
| s30 | 102.57 → 106.57 | hBed · bed | L26 scene | top-down sheet and two pillows; the line split into two columns lying side by side, red and grey | glyph onsets | xfade |
| s31 | 106.57 → 110.57 | hBed · dream | L27 scene | the columns drift apart; two dream bubbles (an open poppy / a closed box); right column mirrored | glyph onsets | cut |
| s32 | 110.57 → 112.09 | hType · dont2 | L28 scene | carmine slam on fluorescent white; the last two glyphs come late | 110.90 112.01 112.11 | cut |
| **B4** H8 | | | | | | |
| s33 | 112.09 → 114.60 | hOffice · grid | L29 scene | the line copy-pasted into a spreadsheet grid, rows on beats; red 已阅 stamps; tube light flicker (small) | beats | cut |
| s34 | 114.60 → 118.58 | hOffice · seals | L30 scene | 16 solar-term seals 惊蛰→霜降 stamp on eighth notes into a 4×4 calendar; sun/moon dial turns | 115.07 + k·0.25 | cut |
| s35 | 118.58 → 122.08 | hOffice · conveyor | L31 scene | a conveyor of identical buds; each beat a stamp 合格 and a pin; spinning clock; heavy gothic type | beats | cut |
| s36 | 122.08 → 127.58 | hYouth | L32 scene (キメ) | first six glyphs small; 少年郎 in red handwriting (125.48 126.11 126.59) dissolves into petals that blow away; white rises | 125.48 → 127.5 | cut |
| **REFRAIN 3** H9 | | | | | | |
| s37 | 127.58 → 129.84 | hForget · snow | L33 scene | summer-green paper, heavy snow; the line types; snow caps and buries the glyphs | downbeat 127.87 | flash `#FFF3C8` |
| s38 | 129.84 → 134.56 | hCross · snow | L34 JIZURA `paper` | bands cross in snow; the red band stops dead at the centre (it refuses to pass) | stop 132.30 | cut |
| s39 | 134.56 → 138.09 | hInsect · release | L35 scene | the press descends and halts in the air at 136.01; the insect walks out of frame leaving tiny red footprints | 136.01 | cut |
| s40 | 138.09 → 141.59 | hBud · lift | L36 scene (part) | the bud lifts its head (nod 0.9 → 0.15, 138.46 → 140.4); first 7 glyphs small; snow swirls | glyph onsets | cut |
| s41 | 141.59 → 143.59 | hBud · crack | L36 scene (キメ) | giant 花 骨 朵 slam behind the bud (141.87 142.48 143.43); sepals crack with light; on 朵 the bud tears free of the stem | 141.87 142.48 143.43 | cut |
| **OUTRO** H10 | | | | | | |
| s42 | 143.59 → 146.07 | hSlam · refuse | L37 scene | carmine field; one glyph per sung onset slams (paper-white / ink alternating) with spring camera kicks; the freed bud tumbles | 143.63 144.06 144.22 145.40 145.61 145.78 145.96 | flash `#FFFFFF` |
| s43 | 146.07 → 150.58 | hTunnel | L38 JIZURA `climax` | push through stacked pages of the film (winter, house, meadow, office, photo), one tears open per bar | 146.07 148.08 150.04 | cut |
| s44 | 150.58 → 153.59 | hWisp | L39 scene | a wisp of red silk rises and curls until the frame is red; the bud's sepals part; cursive white type | — | cut |
| s45 | 153.59 → 155.06 | hBloom · pop | L40 scene | "like a joke": the sepals pop off, crumpled petals spring out with a cartoon bounce; playful type | 153.88 154.37 154.48 154.85 | cut |
| s46 | 155.06 → 160.19 | hBloom · open | L41 scene (キメ) | petals unfold into a frame-filling poppy (155.3 → 157.1); pull back: the bloom alone on a bare branch on an empty sheet; 无人问津 emphasised | glyph onsets · 157.6 → 160.0 | cut |
| **END** H1 | | | | | | |
| s47 | 160.19 → 167.6 | hPage · end | none | HARD CUT, silence: the same herbarium sheet, now with the pressed bloom; label 状态 已开; seal 「无人问津」 at 161.2; credits type into the label; a silverfish crosses the sheet; cut to black at the end | 161.2 · 162–164 | cut |

## Global punctuation

- Flashes (`Z.globalFX`, ≤ 3/s, never on white frames): 15.89 (blush), 48.09, 64.07 (white, short), 80.09 (rouge),
  127.87 (warm), 143.59 (white). Kick shake only in refrain 2, refrain 3 and the outro.
- Stops: 11.00–11.38 hold, 14.85–15.54 title in silence, 46.40–46.54 black, 160.19 hard cut to silence.
- Holds (≥ 2 bars, almost still): s02, s09, s28–s30, s47.
