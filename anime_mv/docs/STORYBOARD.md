# 花骨朵 — storyboard (anime_mv)

Grid: steady 120 BPM, bar *n* starts at 0.09 + 2(n−1) s (`tools/lock_grid.py`); the music stops dead at 160.19 s.
Lyric lines are referred to by index and onset from the user's LRC (L01 15.85 … L42 155.35) — never by text; the
engine reads the words at runtime and every glyph appears on its own sung onset (`analysis/char_timing.json`).
Typography is designed per line inside each image (`engine/scenes/hgd_type.js`); the "type" column says how.
Impact frames (集中線 + negative / carmine punch) mark the biggest hits: 16.09, both direction words of each
refrain, 48.09, 66.09 (landing), 80.09, 128.09, 140.09 (the hairpin), 144.09, 154.14 (the bloom).

## Intro 0–16.09 (stops 11.00–11.38, 14.85–15.54 freeze the picture)

| # | time | scene | picture | type |
|---|---|---|---|---|
| s01 | 0–4.09 | branch | a bare branch inks itself in on a white page; a closed bud at its tip | – |
| s02 | 4.09–8.09 | palm | her cupped hands; a white cochineal walks into the palm; the first carmine | – |
| s03 | 8.09–11.38 | bust | blinking, breathing, rim light, snow bokeh passing | – |
| s04 | 11.38–15.54 | title | full figure on the white page; 花骨朵 typeset on the beats; credit | title |

## Refrain 1 16.09–32.09 — the bewildered question

| # | time | scene | picture | type |
|---|---|---|---|---|
| s05 | 15.54–17.85 | field | crane down to the fork; impact on 16.09; she turns (turn_mid → turn_back); shockwave | L01 gathers out of the snow, then blows away |
| s06 | 17.85–20.09 | field | tracking run (3-drawing cycle), whip in, speed lines, snow rushing | L02 first half streams off behind her |
| s07 | 20.09–22.59 | fork | camera whips to each path as its direction is sung (impact lines) | L02 second half pressed into the two footpaths |
| s08 | 22.59–26.09 | palm | the insect walks her palm | L03 along her palm lines; the insect's name crawls after it |
| s09 | 26.09–30.59 | palm | the insect curls into the bud (match cut) | L04 unfurls around the bud like petals |

## Verse 32.09–48.09 — last winter

| # | time | scene | picture | type |
|---|---|---|---|---|
| s10 | 30.59–34.59 | sky | a pale sun tries to rise; her silhouette below | L05 frosts over in the sky |
| s11 | 34.59–38.59 | alley | empty alley, light shafts, the sun sinking; she far away | L06 old paint on the wall; its sun glyph sits in the sun |
| s12 | 38.59–42.59 | alley | walking away, her long shadow on the wall | L07 a shadow beside hers |
| s13 | 42.59–46.40 | alley | hugging her knees under the eaves | L08 falls like snow and settles around her |
| s14 | 46.40–48.09 | bust | she lifts her gaze; warm light, blinks | L09 breathed out in rouge |

## B1 48.09–64.09 — a house

| # | time | scene | picture | type |
|---|---|---|---|---|
| s15 | 48.09–50.59 | house | paper walls hinge up on the beats, punches | L10 one glyph brushed onto each wall |
| s16 | 50.59–54.59 | room | the curtain lifted; window light shafts | L11 behind the sheer curtain |
| s17 | 54.59–56.59 | bride | the veil, bead glints | L12 made of silver beads |
| s18 | 56.59–58.59 | rouge | fingertip on the lip; carmine floods the frame | L13 smeared like rouge |
| s19 | 58.59–62.59 | card | an elegant vertical card, cloud scrolls, her ghost | L14 typed on its onsets |
| s20 | 62.59–64.09 | wind | wind and petals rise | L15 torn away by the wind |

## B2 64.09–80.09 — to die in spring

| # | time | scene | picture | type |
|---|---|---|---|---|
| s21 | 64.09–66.59 | fall | the backward fall (pendulum, slow motion, second drawing mid-air), landing impact + petal burst | L16 falls with her |
| s22 | 66.59–70.59 | flowers | top-down among poppies, petals passing the lens | L17 white paper glyphs among the flowers |
| s23 | 70.59–74.59 | mud | roots grow on the beats | L18 sprouts roots |
| s24 | 74.59–79.59 | page | silverfish eat the page | L19 printed on the page, eaten through |

## Refrain 2 80.09–96.09 — the question as accusation

| # | time | scene | picture | type |
|---|---|---|---|---|
| s25 | 79.59–82.09 | sing | carmine impact on 80.09, lip sync, red rim light, petals | L20 rouge stamps around her |
| s26 | 82.09–83.59 | field | the run again, carmine | L21 first half streams off in brush |
| s27 | 83.59–86.59 | fork | the frame splits on each direction word | L21 second half stamped into the paths |
| s28 | 86.59–88.59 | palm | the hand trembles; dye seeps out | L22 first half bleeds out with the dye |
| s28b | 88.59–90.09 | montage | eyes / her on carmine / the hand, one cut per beat | the insect's name, one glyph per cut |
| s29 | 90.09–92.59 | palm | the bud cracks | L23 petals of words |
| s30 | 92.59–94.59 | sing | close singing, lip sync | L23 end floats around her |
| s31 | 94.59–96.09 | turn | she turns away and leaves | L24 left behind where she stood |

## B3 96.09–112.09 — the skin (night)

| # | time | scene | picture | type |
|---|---|---|---|---|
| s32 | 96.09–98.59 | reach | the hand reaches, then closes on nothing (reach → reach_b) | L25 glows beside her fingertips, then fades |
| s33 | 98.59–102.59 | doll | drawing / paper doll on the beats | L26 visible only inside the paper doll |
| s34 | 102.59–106.59 | bed | one bed, lamp and window | L27 on the quilt, warm half / cold half |
| s35 | 106.59–110.59 | bed split | the frame splits along the bed | L28 split with the halves |
| s36 | 110.59–112.09 | eyes | push into her eyes, blinks | L29 huge and dim behind her |

## B4 112.09–128.09 — workaholic

| # | time | scene | picture | type |
|---|---|---|---|---|
| s37 | 112.09–114.59 | office | dolly rush, a punch on every beat | L30 repeated on every desk |
| s38 | 114.59–118.59 | calendar | solar-term pages flip one per beat | L31 handwritten on the page |
| s39 | 118.59–122.59 | desk | day / night strobe on the beats | L32 rubber-stamped on the paper piles |
| s40 | 122.59–126.09 | memory | earlier shots as prints, burning | L33 captions on the prints |
| s41 | 126.09–127.59 | white-out | snow rushes in | L33 end rises as ash |

## Refrain 3 128.09–144.09 — snow in June

| # | time | scene | picture | type |
|---|---|---|---|---|
| s42 | 127.59–130.09 | sing | negative impact on 128.09, blizzard, lip sync | L34 formed of snow |
| s43 | 130.09–131.59 | field | the run through the blizzard | L35 first half streams off |
| s44 | 131.59–134.59 | fork | the paths buried | L35 second half pressed into the snow, then buried |
| s45 | 134.59–136.59 | palm | snow lands in her palm | L36 flakes melting into rouge |
| s45b | 136.59–138.09 | montage | hairpin / eyes / hand | one glyph per cut |
| s46 | 138.09–141.09 | hairpin | carmine impact on 140.09: the hairpin is torn out and held high | L37 first half whirled away |
| s47 | 141.09–143.59 | kneel | the dropped bud in the snow, focus pull | L37 end settles in the snow |

## Outro 144.09–160.19 — the bloom, and the tail

| # | time | scene | picture | type |
|---|---|---|---|---|
| s48 | 143.59–146.09 | sing | carmine impact, petal storm, lip sync | L38 rises with the petals |
| s49 | 146.09–150.59 | face | the tear, slow push, light | L39 tiny, down the track of her tear |
| s50 | 150.59–154.09 | branch | the bud swells and cracks; a thread of rouge winds up to it | L40 strung along the thread |
| s51 | 154.09–155.35 | bloom | the bud pops open on the downbeat (impact) | L41 pops out with it |
| s52 | 155.35–160.19 | ignored | pull back until the flower is a dot on a white page; she walks away, tiny | L42 tiny at the branch tip |
| s53 | 160.19–end | tail | **hard cut**: the same branch, a new closed bud, silence, credits | – |
