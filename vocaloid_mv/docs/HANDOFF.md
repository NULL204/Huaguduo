# 花骨朵 PV — handoff to a local session

The cloud session that worked on branch `ccr-168236f7-kgmujb` (repo github.com/null204/huaguduo) could not reach
NovelAI or the user's computer. The user now wants a session on their own machine to make the PV **from scratch, in
the style of Japanese 2D animation (a Vocaloid / 手書き anime PV)**, with NovelAI-generated art. This file gives that
session the background, the reusable pieces and the rules.

## 1. What the user wants (condensed from the whole conversation)

- A fan-made **animated** PV for 《花骨朵》 (vocal 洛天依): expressive, dramatic, impactful, high quality, a distinctive
  style — not a filler video, not a slideshow.
- **Japanese 2D anime look**, Vocaloid-MV style. Their style reference is a clean, high-key modern anime illustration:
  thin loose lineart, muted cool palette, lots of white space, chromatic-aberration sparkle, glassy elements, small
  elegant typography (they can attach the image).
- Use **NikusonP's vocaloid-style-mv-pipeline** (https://github.com/EGSECDA/vocaloid-style-mv-pipeline): "use his
  skills to create the PV for 花骨朵" — the method, engine, JIZURA lyric layer, beat-locked editing, post pass and the
  review loop, applied to this song's own material. **Not** a replica of the kit's example film (残光).
- From their anime brief: (1) the character stays visually consistent across shots; (2) motion respects force,
  centre of gravity and perspective; (3) high-quality character visuals that actively perform, while text and effects
  carry the narrative; (4) expressive, striking images.
- **Character art comes from NovelAI** (the user's key). Claude's own procedurally drawn characters were rejected
  ("children's book illustration", "distinctly different from your art style") — don't hand-draw characters in code.
- Which character: the song is sung by 洛天依; the user once offered a slightly modified 洛天依 as the protagonist. The
  cloud session used an original singer instead, 阿朵 (`vocaloid_mv/docs/CHARACTER.md`). **Ask the user at the concept
  checkpoint which design to use.**
- Save the project and the finished video in the repository.

## 2. The song and its reading (no lyrics here — use the user's LRC at runtime)

Audio facts (from the cloud analysis, `vocaloid_mv/analysis/audio.json`, `docs/AUDIO_MAP.md`): 170.4 s file, 120.4 BPM,
4/4, 80 bars, bar 1 at 0.09 s; intro stops at 11.00–11.38 and 14.85–15.54 (vocal pickup 15.85); a gap at 46.40; the
music **stops dead at 160.19 s** (reverb tail after). Sections (`analysis/sections.json`): intro 0–15.9 · refrain 1
15.9–32.1 · verse "last winter" 32.1–48.1 · B1 "a house" 48.1–64.1 · B2 "to die in spring" 64.1–80.1 · refrain 2
80.1–96.1 · B3 "the skin" (breakdown) 96.1–112.1 · B4 "workaholic" 112.1–127.9 · refrain 3 127.9–143.6 · outro
143.6–160.2. Per-glyph vocal onsets for every lyric line: `analysis/char_timing.json` (numbers only).

The user's interpretation (they supplied a long text; summary): the song criticises how people trade their ideals
for "usefulness" — set against a feudal-era bride who has no say over her life. Cochineal (胭脂虫) must be crushed to
become useful rouge; a bud must be forced open to become a flower people like to look at. The original PV shows a cycle
(the same painting opens and closes it), a grey-haired 洛天依 (reality) and a red-haired one (her ideals) crossing,
children playing cat's cradle with a red string (innocence), red arms = ideals still alive, white arms = ideals lost.
Verse: a winter that killed the bud's companions; B1: "a house" that is really the wedding as a funeral (a bride lying
in flowers, a queue of brides), rouge made from crushed insects, an empty court poem by Li Bai; B2: wishing to die in
spring before being corrupted, spring mud that feeds silverfish; refrain 2: the question becomes an accusation; B3:
"don't forget me", the same bed with different dreams; B4: waiting from 惊蛰 to 霜降, a workaholic who betrayed the
youth in her heart (faceless brides on an assembly line); refrain 3: snow in June (injustice), she pulls the branch out
of herself; outro: the bloom opens anyway, like a joke, on a branch nobody cares about — and the song simply stops.

## 3. Reusable pieces in the repo (optional — the new film starts from scratch)

- `vocaloid_mv/tools/novelai_gen.py` — NovelAI client (V4.5 payload with V4/V3 fallbacks, sequential, 429 retries,
  free-tier sizes, auto chroma key + trim of cut-outs via the pipeline's `tools/alpha_matte.py`); key from
  `NOVELAI_API_KEY` or `~/.config/novelai/key`. **Untested against the live API** — run `--check`, then one job, and fix
  the payload if NovelAI answers 400. `tools/build_nai_jobs.py` + `assets/char/jobs_nai.jsonl` are a first prompt set
  (Danbooru tags) for the original singer.
- `vocaloid_mv/analysis/*` — audio analysis, curated sections, per-glyph onsets, JIZURA markup positions
  (`lyrics_markup.json`) + `tools/build_lyrics_mv.py` (writes the marked-up LRC from the user's LRC).
- `vocaloid_mv/engine/fonts/manifest.json` + `tools/fetch_fonts_gfonts.py` — adds Chinese display faces (Ma Shan
  Zheng, ZCOOL XiaoWei / QingKe HuangYou / KuaiLe, Zhi Mang Xing, Long Cang, Liu Jian Mao Cao); JIZURA's zh-Hans
  styles use the first four. Without them Chinese lyrics fall back to the wrong faces.
- `vocaloid_mv/engine/tests/hgd_jz.js` — showed that JIZURA's `paper` (light scheme, our colours via
  `colors.enabled`), `specimen` (light scheme) and `crimson` (night / climax) styles render the Chinese lyrics well.
- `vocaloid_mv/` as a whole is the cloud session's typography-led fallback (the poppy bud as protagonist, procedural
  scenes on a rice-paper look). Treat it as reference only, not as the film to finish.

## 4. Setup on the local machine

1. Pipeline: clone https://github.com/EGSECDA/vocaloid-style-mv-pipeline; follow `skills/vocaloid-style-mv/SKILL.md`
   (phases: scaffold → listen → concept checkpoint → assets → storyboard → build → review → deliver) and its
   `references/` (01 workflow · 02 creative direction incl. §13 bright films · 03 audio & lyrics · 04 asset generation
   · 05 engine · 06 JIZURA · 08 render · 09 QA · effect-cookbook).
2. Scaffold a new project inside this repo (for example `anime_mv/`) with the song and the user's LRC; run its setup
   (Playwright, fonts, JIZURA at the pinned commit); check that WebGL names the GPU (`python tools/check_env.py --webgl`).
3. Song and lyrics come from the user's files; keep both out of git (the scaffold's `.gitignore` already ignores
   `audio/` and the lyric files — check before committing).
4. NovelAI key in the environment (`NOVELAI_API_KEY`); never print it or commit it.

## 5. Rules that held

- No lyric text committed or pasted into code / docs; read lines from the LRC at runtime.
- Every frame a pure function of song time (seeded randomness, no wall clock) — the renderer splits the film across
  workers.
- ≤ 3 full-frame flashes per second; no lyric over the character's face (centre-free plans or text behind her).
- End on the dead stop at 160.19 s (a hard cut), not a fade.
- Credits: song 《花骨朵》, vocal 洛天依, fan-made; the pipeline (NikusonP, MIT) and JIZURA (hakoniwa, MIT). Ask the user
  for the exact on-screen credit line.
- Commit and push to `ccr-168236f7-kgmujb`; no pull request unless asked. The repo also holds the user's earlier
  shadow-puppet PV (`pv/`, `videos/huaguduo_shadow_puppet_pv_1080p.mp4`) and its cover — leave them alone.
- Final video for the repo: `videos/<name>_1080p.mp4` under 100 MB (GitHub's file limit); keep the high-quality
  master locally.
