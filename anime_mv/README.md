# 《花骨朵》 — fan-made animated PV (vocal 洛天依)

A hand-drawn-anime style PV (Vocaloid 手書き / anime MV) for 《花骨朵》, made with NikusonP's
[vocaloid-style-mv-pipeline](https://github.com/EGSECDA/vocaloid-style-mv-pipeline) (MIT). The performer is an original
character, **阿朵** (`docs/CHARACTER.md`), not 洛天依's character design; 洛天依 is credited as the vocal.

- Concept, arc and colour script: `docs/CONCEPT.md` · shot list: `docs/STORYBOARD.md` · art plan: `docs/ASSETS.md`
- Finished video: `../videos/huaguduo_anime_pv_1080p.mp4`

The song and the lyrics are **not** in this repository. Put your own copy of the song at `audio/song.wav` and the
timed lyrics at `analysis/lyrics_mv.lrc` (both git-ignored); the engine reads the words at runtime. Nothing in the
code or docs contains lyric text — lines are referred to by number, glyphs by index.

## How the film is made

| phase | what was done here |
|---|---|
| listen | `tools/analyze_audio.py` → `analysis/audio.json`; the song is a steady 120 BPM, so `tools/lock_grid.py` locks the beat grid to it (checked against the kick drum; the tracker had drifted by a beat in 116–146 s). Bar *n* starts at 0.09 + 2(*n*−1) s; the music stops dead at 160.19 s. `analysis/char_timing.json` = per-glyph vocal onsets (numbers only). |
| concept | `docs/CONCEPT.md`: things only get colour when they are crushed or forced open — a high-key, cool, almost colourless world where carmine appears only where something is crushed, pressed or forced open. |
| character & art | 阿朵 master chosen from three candidates; every pose, background and prop generated with the Codex image tool (`tools/imagegen.py`) against the master (`tools/build_asset_jobs.py`, `assets/gen/*.jsonl`). Cut-outs keyed with `tools/key_unmix.py` (colour-difference unmix that keeps the sheer shawl translucent; despill). Extra key drawings for animation: a 3-drawing run cycle, mouth-closed / blink variants for lip sync and blinks, second poses for the turn, the reach, the fall and the hairpin pull. |
| build | `engine/timeline.js` is the edit (shots on the beat grid). Film code: `engine/scenes/hgd_core.js` (puppet deformer, physics, fx, transitions), `hgd_type.js` (lyric typography), `hgd_scenes.js` (the film's scenes). |
| review | stills at shot midpoints (`tools/stills.mjs`), motion clips, full renders, review sheets (`tools/review_sheets.py`). |

### Animation

- **Puppet deformer** (WebGL mesh warp on each key drawing): head tilt about the neck, breathing, hair / braid /
  shawl driven by wind and by a damped spring that lags behind the body's acceleration, skirt flutter; the face stays
  rigid and the feet stay planted; drawn motion on 12 fps (2コマ打ち).
- **Performance**: run cycles on the beat, mouth on each sung syllable (from the per-glyph onsets), seeded blinks, pose
  switches with smears, rim light.
- **Impact**: impact frames with 集中線 on the big hits, per-beat close-up montages in the choruses, zoom punches,
  whip pans, shockwaves, petals and snow passing the lens, light shafts and leaks, carmine dye soaking in from the
  edges as the film goes on.

### Typography

Every line is designed for its own image and meaning and appears glyph by glyph on its sung onset: snow gathering into
the words, the two directions pressed into the two footpaths, words along her palm lines, a shadow on the alley wall,
the veil's silver beads, rouge stamps, words falling with her, roots in the mud, the page the silverfish eat, the line
on the calendar, captions burning with the prints, flakes melting into rouge in her palm, a thread of rouge up to the
bud. The pipeline's JIZURA lyric layer was tried first and replaced by this bespoke layer (its auto-layouts looked
like a template on this film); `jizura/` stays in the project as part of the kit.

## Rebuild

Requirements: Node 20+, Python 3.10+ with `numpy pillow scipy librosa soundfile opencv-python-headless`, ffmpeg,
Microsoft Edge (Playwright drives it headless; run `npm install` once).

```bash
python tools/analyze_audio.py && python tools/lock_grid.py
python tools/fetch_fonts_subset.py              # Google Fonts subsets of only the glyphs used (needs the LRC)
node tools/stills.mjs --times 16.5,57.5,128.2 --sheet check
node tools/render_frames.mjs --start 0 --workers 3 --codec x264 --crf 16 --preset slow --audio audio/song.wav --out render/master.mp4
```
On Windows set `PYTHON` to your interpreter if `python` is not on PATH. Without an NVIDIA GPU use `--codec x264`.

## Credits

- Song 《花骨朵》 — vocal 洛天依. This is an unofficial fan work.
- PV: original character 阿朵; art generated with the Codex image tool; animation, typography and edit in this project.
- vocaloid-style-mv-pipeline — NikusonP (MIT). JIZURA 字面 — (c) 2026 hakoniwa (github.com/852wa), MIT.
- Fonts (SIL OFL): Noto Serif SC, Noto Sans SC, Ma Shan Zheng, Zhi Mang Xing, Long Cang, ZCOOL XiaoWei / QingKe
  HuangYou / KuaiLe, LXGW Marker Gothic, IBM Plex Mono.
