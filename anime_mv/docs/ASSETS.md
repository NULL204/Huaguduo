# 花骨朵 — asset plan (30 NovelAI generations, made by hand on novelai.net)

The NovelAI key is a free-trial account: trial generations need the site's reCAPTCHA, so the user generates every
image on novelai.net from the prompt sheet (`assets/nai/sheet.html`, jobs in `assets/nai/jobs.jsonl`) and saves the
PNGs to `assets/nai_raw/`. NovelAI writes prompt and seed into each PNG, so files need no renaming: the importer
(`tools/nai_import.py`) matches them to jobs by seed, keys the cut-outs (green #00FF00 → RGBA, trimmed) and writes
`assets/char/*.png`, `assets/bg/*.png`, `assets/prop/*.png`.

Settings for every job: **NAI Diffusion V4.5 Full** · steps 28 · prompt guidance 5.5 · sampler Euler Ancestral ·
noise schedule karras · quality tags on · UC preset Heavy · portrait 832×1216 or landscape 1216×832 (≤ 1 MP).

Budget: 30 images = 3 master candidates + 14 poses + 9 backgrounds + 1 prop sheet + **3 reserved for retakes**.
Every image is re-used many times (camera moves, crops, grades, silhouettes, deformation), about one image per
2–3 shots.

| batch | id | kind | size | used for |
|---|---|---|---|---|
| 1 | master_a | full body, front, arms loose, wind | 832×1216 | REF master candidate; title lockup, establishing shots |
| 1 | master_b | full body, ¾, cupped hands, looking at palm | 832×1216 | master candidate; refrain palm shots, B1 |
| 1 | master_c | full body, low angle, hand at the bud hairpin | 832×1216 | master candidate; bud motif, refrain 3 |
| 2 | palm | close-up, open palm with a tiny white insect (opaque 16:9) | 1216×832 | intro, refrains: insect ↔ bud match cut |
| 2 | bust_sing | bust, singing, eyes half closed | 832×1216 | refrains, lyric shots |
| 2 | turn_back | full body from behind, looking back over the shoulder | 832×1216 | refrain 1 fork, verse |
| 2 | back_walk | full body from behind, walking away | 832×1216 | verse alley, refrain 3 snow |
| 2 | sit_knees | sitting, hugging knees | 832×1216 | verse (sunless winter) |
| 2 | curtain | lifting a curtain, peeking | 832×1216 | B1 (the house) |
| 2 | bride_bust | bust in a white bridal veil, rouge on lips, fingertip at the lip | 832×1216 | B1 rouge moment |
| 2 | fall_back | falling backward, arms loose, shawl flying | 832×1216 | B2 fall (physics) |
| 2 | lying_top | lying on her back among red flowers, from above (opaque) | 1216×832 | B2 landing |
| 2 | sing_power | low angle, singing out, hand to chest | 832×1216 | refrains 2–3 |
| 2 | reach | reaching toward the viewer, foreshortened hand | 832×1216 | B3 |
| 2 | desk | slumped over a desk, paper everywhere | 1216×832 | B4 |
| 2 | pull_pin | pulling the bud hairpin out, hair loosening, snow | 832×1216 | refrain 3 |
| 2 | face_close | face close-up, tear, calm (opaque) | 1216×832 | outro |
| 3 | bg_branch | bare branch with one closed bud on a white page, frost | 1216×832 | intro, outro, tail |
| 3 | bg_field | white snowfield fork, two paths, pale sky | 1216×832 | refrains 1/3 |
| 3 | bg_alley | empty winter alley, sunless, long shadows | 1216×832 | verse |
| 3 | bg_room | white paper room, sheer curtain, window light | 1216×832 | B1 |
| 3 | bg_flowers | field of red poppies, muted green, from above | 1216×832 | B2 |
| 3 | bg_bedroom | dim bedroom, one bed, night blue, small lamp | 1216×832 | B3 |
| 3 | bg_office | rows of identical desks, fluorescent cyan-white | 1216×832 | B4 |
| 3 | bg_sky | pale sky with a weak sun disc (sky only) | 1216×832 | verse, inserts |
| 3 | bg_snow | June snow over the field, white-out | 1216×832 | refrain 3 |
| 3 | props | prop sheet: cochineal, silverfish, rouge dish, bud / half-open / open poppy | 1216×832 | match cuts, bloom, B2 |
| – | reserve ×3 | retakes for hard poses (fall, lying, reach) | – | – |

Batch 2/3 prompts are written after the master is chosen (they repeat its exact character tags).
