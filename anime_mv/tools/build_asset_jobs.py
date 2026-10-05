#!/usr/bin/env python3
"""build_asset_jobs.py -- write assets/gen/jobs_assets.jsonl: every pose, background and prop of the 花骨朵 PV for
tools/imagegen.py (Codex image tool). The character sentence and the style blocks are fixed here and pasted
verbatim into every prompt (04-asset-generation: consistency comes from the master reference + identical blocks).

  python tools/build_asset_jobs.py
  python tools/imagegen.py assets/gen/jobs_assets.jsonl --out-dir assets --concurrency 4
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ["assets/gen/ref_master_white.png"]

CHAR = ("The same original character as in the reference image (ORIGINAL Chinese virtual singer girl, not Luo Tianyi, not "
        "Hatsune Miku, not any existing character: waist-length straight cool blue-black hair with a carmine-red inner colour on "
        "the underside and the tips, blunt bangs, one thin braid on her LEFT side, a closed carmine poppy-bud hairpin with silver "
        "sepals on her LEFT side, a small carmine three-petal mark on her forehead, garnet-red eyes, frost-white sleeveless top "
        "with a high mandarin collar, one carmine knot button and a carmine tassel at the waist, white sheer detached sleeves, "
        "carmine-stained fingertips, plain slate blue-grey pleated knee-length skirt with a thin carmine hem line, white socks, "
        "dark navy Mary Jane shoes, a long translucent PALE ICE-BLUE silk shawl (not mint, not green) with one thin carmine edge "
        "line). All fabrics are plain, with no prints or patterns")
STYLE = ("Style: clean, high-key modern Japanese anime illustration, like a key frame of a Vocaloid music video: thin, loose, "
         "delicate lineart with a slight sketchy overshoot (coloured lines in cool grey-blue and dark carmine-brown, not pure "
         "black), flat cel colours with one soft cool shadow tone, airy and luminous, muted cool palette (frost white, ice blue, "
         "pale slate, silver) with carmine as the only saturated accent, crisp readable silhouette, delicate and melancholic, "
         "correct anatomy and hands. No text, no watermark, no signature.")
BGSTYLE = ("Style: clean, high-key modern Japanese anime background art for a Vocaloid music video: thin delicate coloured line "
           "art on architecture and objects (cool grey-blue lines, not black), flat soft colour areas with gentle cool shadows, "
           "luminous and airy, lots of white space and soft white haze, muted cool palette (paper white, frost, ice blue, pale "
           "slate, silver), subtle chromatic-aberration sparkle on the brightest highlights. Wide 16:9 landscape composition. "
           "No people, no characters, no text, no readable signs, no watermark.")
PROPSTYLE = ("Style: clean anime prop illustration with thin delicate coloured lineart, flat cel colours with one soft shadow "
             "tone, muted cool palette with carmine accents. A single isolated object, no text, no watermark.")

JOBS: list[dict] = []


def cut(jid: str, pose: str) -> None:
    JOBS.append({"id": jid, "out": f"char/{jid}.png", "transparent": True, "key": "#00FF00", "trim": True, "images": REF,
                 "prompt": f"{pose} {CHAR}. {STYLE}"})


def frame(jid: str, scene: str) -> None:
    JOBS.append({"id": jid, "out": f"char/{jid}.png", "transparent": False, "images": REF,
                 "prompt": f"{scene} {CHAR}. {STYLE} Wide 16:9 landscape image, full bleed, no border."})


def bg(jid: str, scene: str) -> None:
    JOBS.append({"id": jid, "out": f"bg/{jid}.png", "transparent": False, "prompt": f"{scene} {BGSTYLE}"})


def prop(jid: str, obj: str, key: str = "#00FF00") -> None:
    JOBS.append({"id": jid, "out": f"prop/{jid}.png", "transparent": True, "key": key, "trim": True,
                 "prompt": f"{obj} {PROPSTYLE}"})


# ---------------------------------------------------------------- character cut-outs (green screen, master as reference)
cut("bust_calm", "Bust shot (from the chest up), facing the viewer, head tilted slightly, eyes looking down and to the side, "
    "calm and melancholic, lips closed; a gentle breeze moves loose strands of hair across her cheek.")
cut("bust_sing", "Bust shot (from the chest up), three-quarter view, singing softly with her mouth half open, eyes half closed, "
    "one hand raised near her collarbone, hair drifting in a breeze.")
cut("sing_power", "Upper body seen from a low angle, singing out with full voice, mouth open, head lifted, eyes nearly shut with "
    "emotion, her right hand pressed flat against her chest; strong wind from the left throws her hair and the shawl to the right.")
cut("back_walk", "Full body seen from directly behind, walking away from the viewer, mid-stride: her left foot forward on the "
    "ground carrying her weight, the right heel lifted, arms relaxed and swinging slightly; long hair and the ends of the shawl "
    "trail behind her in the wind. Her face is not visible.")
cut("turn_back", "Full body, her body facing away from the viewer, turning her head and shoulders to look back over her LEFT "
    "shoulder at the viewer, weight on her right leg, uncertain, lips slightly parted; hair swinging with the turn.")
cut("sit_knees", "Full body, sitting on the ground hugging her knees tightly to her chest, chin resting on her knees, eyes open "
    "and empty; the shawl pooled around her; cold, small and lonely. Seen from the front at a slight high angle.")
cut("curtain", "Full body, side view facing right, standing, her right hand lifting the edge of a tall sheer white curtain that "
    "hangs in front of her, peeking past it with a hopeful, shy expression; the curtain is translucent white.")
cut("bride_bust", "Bust shot (from the chest up), facing the viewer, a long sheer silver-white bridal veil draped over her hair "
    "and shoulders, embroidered with tiny silver beads; her lips are painted vivid carmine rouge; she touches her lower lip with "
    "a carmine-stained fingertip, eyes lowered, expressionless and still, like a doll.")
cut("fall_back", "Full body, falling backward through the air, seen from the side and slightly below: her body tilted about 45 "
    "degrees back, arms loose and lifted by the fall, legs slightly bent, eyes closed, a peaceful face; hair and the shawl fly "
    "upward above her because she is falling. No ground.")
cut("run", "Full body, running to the right in profile, strong forward lean, left leg extended back, right knee driving forward, "
    "arms swinging; hair and the shawl stream straight out behind her; urgent expression.")
cut("reach", "Upper body, reaching one hand straight toward the viewer with strong foreshortening: the open hand with "
    "carmine-stained fingertips is large in the foreground, her face behind it pleading, eyes glistening, lips parted; hair "
    "blown forward.")
cut("lying_side", "Full body, lying on her side (seen from above at an angle), knees slightly bent, both hands tucked under her "
    "cheek, eyes open, staring sadly into the distance; hair spread out behind her. No bed, no ground drawn.")
cut("pull_pin", "Upper body, three-quarter view, pulling the carmine bud hairpin out of her hair with her LEFT hand, the hair on "
    "that side loosening and lifting in a strong wind, tears in her eyes, jaw set with resolve; a few snowflakes around her.")
cut("kneel_snow", "Full body, kneeling with her hands resting on her thighs, head bowed, hair falling forward over her face, "
    "exhausted; a few snowflakes drifting. No ground drawn.")

# ---------------------------------------------------------------- full-frame character shots (opaque 16:9)
frame("palm_close", "Close-up of her two cupped hands held together in front of her chest, palms up and EMPTY (nothing in them), "
      "carmine-stained fingertips, the white sheer sleeves at the wrists; only her hands, wrists and a hint of the white top are "
      "visible. High-key soft white light, shallow depth of field, pale blurred background of white and ice blue.")
frame("face_close", "Extreme close-up of her face from the forehead to the lips, filling the frame, eyes half open looking down, "
      "one tear on her cheek, calm acceptance; the carmine forehead mark visible; fine eyelashes; high-key soft white light.")
frame("lying_flowers", "Seen from directly above: she lies on her back among red poppies, eyes closed, arms loosely at her sides, "
      "hair spread out like a fan over the grass and petals, the shawl spread around her; peaceful. Muted spring green and carmine "
      "flowers, high-key soft light.")
frame("desk", "At night in an empty office: she sits slumped asleep over a desk piled high with paper, her head on her folded "
      "arms, a cold fluorescent desk lamp, rows of identical empty desks fading into the background; cyan-white and grey-blue "
      "light.")

# ---------------------------------------------------------------- backgrounds (opaque 16:9, no people)
bg("field_fork", "A vast white snowfield under a pale sky; two faint footpaths diverge to the left and to the right from the "
   "foreground; a few bare thin trees far away; lots of empty white space; soft cold light.")
bg("alley", "An empty narrow old Chinese alley (hutong) in winter: grey brick walls, closed wooden doors, bare branches over the "
   "walls, a thin layer of snow, a pale sunless sky, long cool shadows, deserted and silent.")
bg("sky", "Only sky: a pale overcast winter sky with a weak white sun disc behind thin cloud, a low horizon line at the very "
   "bottom, very high key.")
bg("room", "A bright empty traditional Chinese room with white paper walls and lattice windows, tall sheer white curtains hanging "
   "in the middle of the room, soft window light, a pale wooden floor, minimal and quiet.")
bg("flowers_eye", "A field of red poppies under a pale spring sky, seen at eye level, muted soft green leaves and stems, a few "
   "petals drifting; the poppies are the only saturated colour, vivid carmine.")
bg("bedroom", "A dim bedroom at night: one double bed with white sheets and two pillows in the centre, a small warm bedside lamp "
   "on one side, cold night-blue light through a window on the other side, quiet and lonely.")
bg("office", "Rows of identical white desks piled with paper stretching into the distance in an empty office at night, flat "
   "fluorescent ceiling lights, cyan-white and grey-blue, symmetrical one-point perspective, oppressive repetition.")
bg("snow", "A white snowfield in a heavy snowfall in early summer: big soft snowflakes, a few bare trees, a faint white sun, "
   "almost white-out, luminous and cold.")
bg("mud", "Close-up of dark spring soil after rain seen from above: fine pale roots, small sprouts, a few fallen carmine petals "
   "and drops of water; soft light.")

# ---------------------------------------------------------------- props (cut-outs; magenta screen for the plant props)
prop("cochineal", "A single tiny cochineal scale insect seen from above at macro scale: a soft oval body covered in white "
     "powdery wax with faint segment lines and tiny legs.")
prop("silverfish", "A single silverfish insect seen from above: a slender silver-grey tapered body with fine scales, long "
     "antennae and three tail bristles.")
prop("branch", "A single bare thin plum branch, dark grey-brown and ink-like, gracefully curving from the lower left to the "
     "upper right, with a few small twigs, no leaves, no flowers, no buds.", key="#FF00FF")
prop("bud_closed", "A single closed poppy bud on a short curved stem: pale silver-grey hairy sepals, a thin line of carmine "
     "petal showing at the tip.", key="#FF00FF")
prop("bud_half", "A single poppy bud half open on a short curved stem: crumpled carmine petals emerging, the silver-grey sepals "
     "splitting and falling away.", key="#FF00FF")
prop("bloom", "A single fully open carmine poppy flower on a short curved stem, four translucent crumpled petals, a dark centre, "
     "seen at a slight angle.", key="#FF00FF")


def main() -> int:
    out = ROOT / "assets" / "gen" / "jobs_assets.jsonl"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for j in JOBS:
            f.write(json.dumps(j, ensure_ascii=False) + "\n")
    print(f"{len(JOBS)} jobs -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
