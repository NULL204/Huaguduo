# 花骨朵 — character bible: 阿朵 (A-Duo), cool retune

Original virtual singer for this fan PV. **Not 洛天依, not Hatsune Miku, not any existing character**: no grey or
silver hair, no jade/green ornaments, no twin tails, no teal. The song is sung by 洛天依 (credited as the vocal);
the on-screen performer is this original character. Internal name 阿朵 — "the bud".

Retuned from `vocaloid_mv/docs/CHARACTER.md` (the cloud session's design) to the user's style reference:
clean high-key modern anime illustration, thin loose lineart, muted cool palette, lots of white space. Carmine is
the film's only saturated colour; on her it lives only in the hair's inner colour, the bud, the forehead mark, the
knot button, the hem line and her stained fingertips.

| part | spec |
|---|---|
| silhouette | slim, upright; long straight hair + a long floating shawl give a tall vertical shape that reads in silhouette |
| hair | waist-length straight hair, cool blue-black (#1A1D26), **carmine inner colour** on the underside and tips (#C8183C → #E85A74); blunt bangs with a few see-through strands; one thin braid on her **LEFT** side |
| eyes | garnet red (#8E1B2E) lightening to rose at the bottom of the iris; calm, slightly downcast default |
| signature | a closed **carmine poppy-bud hairpin with silver sepals** on her **LEFT** side above the braid; a small carmine **花钿** (three-petal mark) on her forehead |
| outfit | frost-white sleeveless top, high mandarin collar, one carmine knot button (盘扣); white sheer detached sleeves; **fingertips stained carmine** (the rouge-maker's hands); slate blue-grey pleated knee skirt with a thin carmine hem line; white socks; dark navy Mary Janes |
| motion prop | a long translucent **ice-blue silk shawl (披帛)** over both elbows and across her back, one carmine edge line, streaming in the wind — the free secondary motion of every shot |
| palette | ink #1A1D26 · carmine #C8183C · rouge #E85A74 · frost white #F4F7FA · ice blue #D7E3EE · slate #8D9BAD · skin #FFF1EA · silver #C9CED6 |
| key colour | **green #00FF00** for cut-out jobs (nothing in the design is green) |
| do-nots | grey/silver/aqua hair; green hair ornaments; twin tails; headphones-with-teal; any existing-character likeness |

Asymmetric details (braid, hairpin) are on her LEFT. A generation that flips them is mirrored as a whole image in
post (no text in the art), so the sides stay consistent on screen.

## NovelAI blocks (pasted verbatim, see `assets/nai/jobs.jsonl`)

NovelAI V4.5 reads Danbooru-style tags. Character tags (every character job):

```text
1girl, solo, original, black hair, colored inner hair, red inner hair, very long hair, straight hair, blunt bangs,
single braid, side braid, red flower bud hair ornament, silver hairpin, forehead mark, red eyes, white chinese
clothes, sleeveless, high collar, mandarin collar, chinese knot button, detached sleeves, white see-through sleeves,
red fingernails, grey-blue pleated skirt, knee-length skirt, red trim, white socks, navy mary janes, light blue
see-through shawl, floating shawl
```

Style tags (characters, close-ups, props):

```text
thin lineart, clean lineart, delicate linework, flat color, soft cel shading, muted colors, pale colors, cool color
palette, high key, anime coloring, white and light blue theme, red accents
```

Cut-out suffix: `simple background, green background` · negative additions: `gradient background, shadow, floor`.
