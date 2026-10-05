# 花骨朵 — concept (anime_mv)

Fan-made animated PV for 《花骨朵》 (vocal 洛天依). Japanese 2D anime / Vocaloid 手書き PV look, high-key and cool.
Lyrics are never quoted here; lines are referred to by their time (the engine reads the user's LRC at runtime).

## Thesis

**Things only get colour when they are crushed or forced open.** Cochineal becomes rouge only when crushed; a bud
becomes a flower people admire only when it opens. The film's world is high-key, cool and almost colourless: paper
white, frost, ice blue, glass. **Carmine — crushed-cochineal red — is the only saturated colour, and it only appears
where something is crushed, pressed, stained or forced open.** Over the film carmine leaks in from the frame edges
like dye in water. The outro is the first fully saturated frame: the bud opens anyway, on a branch nobody looks at.

## Logline

阿朵 wears a closed bud in her hair. She stands at a fork in a white field with a tiny white insect in her palm —
the kind that makes fine rouge. Through a sunless winter, a paper house that folds shut into a bridal box, a fall
into spring flowers she would rather die in, a bed shared with a stranger and a desk where the seasons turn into
paperwork, the red keeps creeping in. In June snow she pulls the bud out of her hair, and it opens anyway — one
smear of red on an unwatched branch. The music stops dead; the same branch already carries a new closed bud.

## Arc and colour script

| section | time (s) | arc | colour | key images |
|---|---|---|---|---|
| Intro | 0–15.89 | fragile promise | paper white + ice blue, one carmine pinpoint | bare branch with a closed bud on a white page; frost sparkle; her palm opens on a white cochineal; title lockup on the stops |
| Refrain 1 | 15.89–32.09 | bewildered question | frost white / glacier blue; carmine only in her palm | the fork in a snowfield, the left/right split as typography; the insect ↔ bud match cut in her palm |
| Verse | 32.09–48.09 | cold memory | slate blue-grey, desaturated; a pale sun disc that never rises | empty alley, long cold shadow, a tiny figure walking away; hugging her knees under the eaves |
| B1 | 48.09–64.07 | wanting | paper white warmed a little; carmine as rouge | a paper house folds up around her; a curtain lifted; rouge pressed on the lip by a stained fingertip (the crushed insect); the court-poem compliment as an empty, elegant type card |
| B2 | 64.07–80.09 | ending on her own terms; first-half peak | the only green before the outro, muted; mud brown | slow-motion fall backward into red flowers; seen from above among petals; roots in spring mud; silverfish eating the page |
| Refrain 2 | 80.09–96.08 | the question becomes an accusation | glacier blue, carmine stains creeping in from the edges | faster cuts, singing close-up, the match cut again with the bud cracked open a little |
| B3 | 96.08–112.09 | intimate breakdown | night blue, one warm lamp | a hand reaching for someone who forgets; one bed in a split frame — two halves, two dreams |
| B4 | 112.09–127.87 | mechanical drive | fluorescent cyan-white; carmine as stamp ink | solar-term calendar pages flip on the beat from 惊蛰 to 霜降; desk strobing day/night; the same desk repeated |
| Refrain 3 | 127.87–143.59 | the last question; snow in June | white-out, heavy snow, strongest CA sparkle | snowfield; she pulls the bud hairpin out of her hair |
| Outro | 143.59–160.19 | release without resolution | first fully saturated carmine | the bud opens petal by petal on a bare branch; her face; **hard cut on the dead stop at 160.19 s** |
| Tail | 160.19–end | the cycle | paper white | silence: the same branch with a new closed bud; credits |

## Shapes and motifs

- **Master shape — the closed bud / drop** (bud, cochineal, a drop of rouge, a tear). State changes: closed (intro)
  → swelling (B1) → cracked with red showing (refrain 2) → pulled out (refrain 3) → open (outro) → a new closed bud
  (tail).
- **Secondary shape — the box** (house, bridal box, bed, desk, calendar page, type cards). Boxes close around her.
- **Materials:** paper (page, paper-cut, calendar), frost and glass (sparkle, chromatic aberration), carmine dye
  (stains that spread like ink in water).
- **Motion prop:** the ice-blue shawl. The wind tells the mood: steady breeze, dead calm in the alley, a gale in
  refrain 3.

## Typography voice

- Chinese lyrics in a thin serif (Noto Serif SC light), small and elegant, mostly vertical side bands that keep her
  face clear; carmine brush faces (Ma Shan Zheng / Zhi Mang Xing) only for the キメ words; Long Cang handwriting for
  memory lines.
- The refrain's left/right question becomes architecture: the two directions split to either side of the fork.
- B4's solar terms as a flip calendar. Credits as small, elegant type in the title lockup and the end card.

## Signature moments

1. 11.00–11.38 and 14.85–15.54 (the intro stops): frost freezes in mid-air; the 花骨朵 lockup; slam into refrain 1
   at 15.89.
2. 22.85 → 26.45: insect ↔ bud match cut in her palm.
3. 48.09: the paper house folds up around her on the B1 downbeat.
4. ≈56.9: rouge pressed on the lip — a carmine smear spreads across the frame.
5. 62.85 → 64.07: slow-motion fall backward, landing in flowers on the B2 downbeat, petal burst.
6. ≈74.9: silverfish eat the page; the image is eaten into holes.
7. 80.09: refrain 2 slam, carmine blooming in from the edges.
8. 112.09–127.87: the solar-term flip calendar, one page per beat.
9. 127.87: June-snow white-out; she pulls the hairpin out.
10. 143.59–160.19: the bud opens; hard cut; silent tail with a new bud.

## Animation (not a slideshow)

Every pose is a NovelAI key drawing. Motion comes from:
1. **Deformation with physics:** mesh warps on each drawing — breathing, small head tilts, hair, braid and shawl on
   damped springs driven by the body's acceleration (secondary motion that lags and overshoots).
2. **Pose to pose:** cuts between key drawings on the beat with smear and impact frames, drawn motion on 2s/3s
   (12 fps); camera, light and particles at 30 fps.
3. **Physical actions:** the fall (a rigid-body pendulum about the heels under gravity, then a squash on impact),
   walking bob at the step rate, snow, petals and dust with closed-form physics.
4. **Camera:** multiplane parallax, dolly, rack focus, beat-locked kicks.

## Different from the original PV and from 残光

- **Original PV:** cool high-key palette with frost/glass sparkle instead of warm grey and orange-red; one
  protagonist, no doubles; no cat's cradle, sedan chair or rows of brides; the arm motif becomes stained fingertips;
  the cycle is the branch re-budding, not a repeated painting.
- **残光:** high-key daylight (not dusk/night); bud and box (not circle and crack); paper and dye (not glass and
  light); a hard cut to a silent new bud (not an afterimage).
