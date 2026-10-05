# 花骨朵 — art set (Codex image tool, master-referenced)

NovelAI was planned first, but the key turned out to be a free-trial account whose generations need the site's
reCAPTCHA; the user chose ChatGPT image generation through the Codex CLI instead — the pipeline's own route
(`tools/imagegen.py`). The NovelAI prompt sheet (`assets/nai/`) is kept for reference only.

Every pose is generated with the chosen master attached as a reference (`assets/gen/ref_master_white.png`) plus a
fixed character sentence and style block (`tools/build_asset_jobs.py`); key drawings for animation also attach the
drawing they continue from. Cut-outs are generated on a flat green screen (nothing in 阿朵's design is green) and keyed
with `tools/key_unmix.py` (colour-difference unmix: the sheer shawl, sleeves and curtain stay translucent; global
despill turns any mint drift into ice blue). Plant props use a magenta screen (their stems and sepals are green).
Raw screen images stay local (`*.raw.png`, git-ignored).

| group | files (`assets/...`) | used for |
|---|---|---|
| masters | `char/master_a` (= `REF_master`), `master_b`, `master_c` | reference; title, wind shots |
| poses | `char/bust_calm`, `bust_sing`, `sing_power`, `back_walk`, `turn_back`, `sit_knees`, `curtain`, `bride_bust`, `run`, `fall_back`, `reach`, `lying_side`, `pull_pin`, `kneel_snow` | every character shot |
| key drawings (animation) | `char/run_pass`, `run_b` (run cycle) · `bust_sing_closed`, `sing_power_closed` (lip sync) · `bust_calm_blink` (blinks) · `turn_mid`, `reach_b`, `fall_b`, `pull_pin_b` (second poses) | pose-to-pose performance |
| full-frame shots | `char/palm_close`, `face_close`, `lying_flowers`, `desk` | palm motif, close-ups, montages |
| backgrounds | `bg/field_fork`, `alley`, `sky`, `room`, `flowers_eye`, `bedroom`, `office`, `snow`, `mud` | every location |
| props | `prop/branch`, `bud_closed`, `bud_half`, `bloom`, `cochineal`, `silverfish` | the bud's life, the palm, the page |

Jobs: `assets/gen/jobs_master.jsonl`, `jobs_assets.jsonl`, `jobs_keys.jsonl`; manifests in `assets/manifest.json` and
`assets/char/manifest.json`. 45 generations in total (3 masters + 33 assets + 9 key drawings).
