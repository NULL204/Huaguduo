/* engine/timeline.js -- 《花骨朵》 fan-made anime PV (vocal 洛天依), the edit. docs/STORYBOARD.md is the shot list.
 *
 * Structure follows the pipeline template (film identity, timing helpers, looks, global FX, shots, vertical config).
 * Typography is bespoke: every lyric line is designed for its own image and meaning (engine/scenes/hgd_type.js) and
 * every glyph appears on its own sung onset — no auto-layout lyric layer, no HUD. Lyrics are read at runtime from
 * analysis/lyrics_mv.lrc (the user's file, never committed); per-glyph vocal onsets (numbers only) come from
 * analysis/char_timing.json. Specs below refer to lines by number and to glyphs by index only.
 * Grid: steady 120 BPM, bar n at 0.09 + 2 (n - 1) s (tools/lock_grid.py); the music stops dead at 160.19 s.
 */
(() => {
  'use strict';
  const Z = window.Z, D = Z.draw, E = Z.ease, G = Z.HGD, P = G.P;
  const W = 1920, H = 1080;
  const A = 'assets/char/', BG = 'assets/bg/', PR = 'assets/prop/';

  // ------------------------------------------------------------------ film identity
  Z.TITLE = '花骨朵';
  Z.TITLE_SUB = 'HUA GU DUO';
  Z.ARTIST = '洛天依';
  Z.CREDIT = 'Vocal：洛天依 · fan-made PV';

  // ------------------------------------------------------------------ rigs: neck pivot, waist, body column, face box, feet (fractions of each drawing)
  const rig = (neck, waist, core, face, feet = 2, skirt = null) => ({ neck, waist, core, face, feet, skirt });
  Object.assign(G.RIG, {
    [A + 'REF_master.png']: rig([0.45, 0.19], 0.37, [0.45, 0.13], [0.32, 0.03, 0.58, 0.17], 0.93, [0.38, 0.66]),
    [A + 'master_a.png']: rig([0.45, 0.19], 0.37, [0.45, 0.13], [0.32, 0.03, 0.58, 0.17], 0.93, [0.38, 0.66]),
    [A + 'master_b.png']: rig([0.47, 0.18], 0.36, [0.45, 0.13], [0.33, 0.03, 0.58, 0.16], 0.93, [0.36, 0.7]),
    [A + 'master_c.png']: rig([0.55, 0.19], 0.37, [0.55, 0.13], [0.42, 0.04, 0.66, 0.18], 0.92, [0.37, 0.62]),
    [A + 'bust_calm.png']: rig([0.47, 0.42], 1.2, [0.47, 0.2], [0.3, 0.1, 0.62, 0.42]),
    [A + 'bust_sing.png']: rig([0.5, 0.4], 1.2, [0.5, 0.2], [0.34, 0.1, 0.64, 0.4]),
    [A + 'sing_power.png']: rig([0.45, 0.25], 0.62, [0.45, 0.18], [0.26, 0.0, 0.56, 0.26], 2, [0.62, 1.0]),
    [A + 'back_walk.png']: rig([0.38, 0.17], 0.42, [0.38, 0.13], [0.27, 0.02, 0.48, 0.15], 0.93, [0.42, 0.68]),
    [A + 'turn_back.png']: rig([0.47, 0.18], 0.42, [0.47, 0.12], [0.33, 0.03, 0.55, 0.16], 0.94, [0.42, 0.68]),
    [A + 'sit_knees.png']: rig([0.5, 0.28], 0.62, [0.5, 0.2], [0.36, 0.08, 0.62, 0.3], 0.95),
    [A + 'curtain.png']: rig([0.6, 0.2], 0.44, [0.58, 0.12], [0.5, 0.06, 0.68, 0.2], 0.95, [0.44, 0.7]),
    [A + 'bride_bust.png']: rig([0.46, 0.46], 1.2, [0.46, 0.22], [0.3, 0.12, 0.62, 0.46]),
    [A + 'run.png']: rig([0.8, 0.22], 0.5, [0.72, 0.12], [0.74, 0.03, 0.92, 0.22], 2, [0.48, 0.72]),
    [A + 'fall_back.png']: rig([0.3, 0.45], 0.62, [0.45, 0.15], [0.12, 0.3, 0.36, 0.5]),
    [A + 'reach.png']: rig([0.5, 0.38], 1.2, [0.5, 0.2], [0.32, 0.08, 0.62, 0.36]),
    [A + 'lying_side.png']: rig([0.28, 0.22], 0.5, [0.42, 0.2], [0.12, 0.04, 0.34, 0.26]),
    [A + 'pull_pin.png']: rig([0.42, 0.38], 1.2, [0.42, 0.18], [0.26, 0.1, 0.54, 0.38]),
    [A + 'kneel_snow.png']: rig([0.42, 0.27], 0.5, [0.42, 0.15], [0.28, 0.08, 0.56, 0.27], 0.95),
    [A + 'turn_mid.png']: rig([0.47, 0.18], 0.42, [0.47, 0.12], [0.33, 0.03, 0.55, 0.16], 0.94, [0.42, 0.68]),
    [A + 'pull_pin_b.png']: rig([0.45, 0.42], 1.2, [0.45, 0.18], [0.28, 0.14, 0.58, 0.42]),
    [A + 'reach_b.png']: rig([0.5, 0.38], 1.2, [0.5, 0.2], [0.32, 0.08, 0.62, 0.36]),
    [A + 'fall_b.png']: rig([0.3, 0.45], 0.62, [0.45, 0.15], [0.1, 0.3, 0.34, 0.52]),
  });

  // ================================================================== setup
  Z.setup = async (audio) => {
    const lastBar = audio.bars.length ? audio.bars[audio.bars.length - 1].index : 0;
    const B = n => { const b = audio.bars.find(x => x.index === n); return b ? b.start : n > lastBar ? audio.music_cut : 0; };
    const bt = (n, k) => B(n) + 0.5 * k;                       // beat k (0..3) of bar n
    const CUT = audio.music_cut;                                // 160.19 dead stop
    const END = Math.min(audio.duration, CUT + 2.2);            // silent tail with the new bud

    G.FREEZE = (audio.stops || []).filter(s => s.kind === 'stop' && s.start < 20).map(s => [s.start, s.end]);

    // ---- sections -> looks (high-key film: low bloom, high threshold, almost no vignette)
    const secs = audio.sections || [];
    for (const s of secs) s.look = s.label;
    Z.sectionAt = t => { let s = secs[0] || null; for (const x of secs) if (x.start <= t + 1e-6) s = x; return s; };
    Z.LOOK_DEFAULT = { boil: 0.9, boilFps: 12, bloom: 0.12, bloomThreshold: 0.93, grain: 0.035, vignette: 0.06, lutMix: 0, ca: 0.5 };
    Z.LOOKS = {
      intro: { boil: 0.7, ca: 0.4 },
      verse: { boil: 0.8, saturation: 0.86 },
      'pre-chorus': { boil: 1.0, beatCA: 1.2 },
      chorus: { boil: 1.1, beatCA: 2.5, beatBloom: 0.06 },
      break: { boil: 0.9, bloom: 0.28, bloomThreshold: 0.78, vignette: 0.28, ca: 0.8 },
      'last-chorus': { boil: 1.2, beatCA: 3.2, beatBloom: 0.08, ca: 1.0 },
      outro: { boil: 1.1, beatCA: 2.5, ca: 1.2, saturation: 1.08 },
      tail: { boil: 0.5, ca: 0.3 },
    };

    // ---- global punctuation: few coloured flashes (white vanishes on white frames), kick shake in the loud parts
    const PALE_RED = [1.0, 0.86, 0.88], ICE = [0.86, 0.92, 1.0];
    const FLASH = [[B(9), 0.35, ICE], [B(25), 0.3, ICE], [B(34), 0.45, PALE_RED], [B(41), 0.5, PALE_RED], [B(65), 0.5, ICE], [B(73), 0.45, PALE_RED], [B(78), 0.55, PALE_RED]];
    const LOUD = [[B(9), B(17)], [B(41), B(49)], [B(65), CUT]];
    Z.globalFX = (P2, t) => {
      for (const [ft, a, col] of FLASH) { const d = t - ft; if (d >= 0 && d < 0.35) { const v = a * Math.exp(-d * 10); if (v > (P2.flash || 0)) { P2.flash = v; P2.flashColor = col; } } }
      const im = G.impactAt(t);
      if (im) {
        if (im.style === 'neg') { P2.invert = 1; P2.saturation = 0.15; P2.contrast = 1.35; P2.ca = (P2.ca || 0) + 6; }
        else if (im.style === 'red') { P2.flash = Math.max(P2.flash || 0, 0.55); P2.flashColor = [0.78, 0.09, 0.24]; P2.contrast = 1.4; P2.ca = (P2.ca || 0) + 5; }
        else { P2.ca = (P2.ca || 0) + 4; P2.contrast = 1.15; }
      }
      if (LOUD.some(([a, b]) => t >= a && t < b)) {
        const q = Math.floor(t * 12), amp = 3 * Math.pow(Z.env.low(t), 3);
        P2.shake = [(P2.shake ? P2.shake[0] : 0) + Z.rnds(q, 91) * amp, (P2.shake ? P2.shake[1] : 0) + Z.rnds(q, 92) * amp];
      }
    };

    // ---- lyrics + per-glyph onsets: runtime only
    let lrc = '';
    try { const r = await fetch(Z.ROOT + 'analysis/lyrics_mv.lrc'); if (r.ok) lrc = await r.text(); } catch (e) { /* none */ }
    G.LYR = G.parseLrc(lrc.replace(/^﻿/, ''));
    try { const r = await fetch(Z.ROOT + 'analysis/char_timing.json'); if (r.ok) G.CT = await r.json(); } catch (e) { G.CT = []; }
    const LEFT = '左', RIGHT = '右', FLOWER = '花', SUN = '日';
    const idx = (n, ch) => { const L = G.lineInfo(n); return L ? L.chars.indexOf(ch) : -1; };
    const onOf = (n, ch, fb) => { const L = G.lineInfo(n), i = idx(n, ch); return L && i >= 0 ? L.on[i] : fb; };
    await Promise.all(G.FONTS_TO_LOAD.map(f => document.fonts.load(f, Z.TITLE + Z.TITLE_SUB + Z.CREDIT + G.LYR.map(l => l.text).join('') + '惊蛰春分清明谷雨立夏小满芒种夏至小暑大暑立秋处暑白露秋分寒露霜降DONE0123456789/').catch(() => null)));

    // ---- carmine dye: how far it has soaked in from the edges at time t
    const stainAmt = t => t < B(41) ? 0 : t < B(49) ? Z.lerp(0.15, 0.45, Z.inv(B(41), B(49), t)) : t < B(57) ? 0.22 : t < B(65) ? 0.3 : t < B(73) ? Z.lerp(0.45, 0.7, Z.inv(B(65), B(73), t)) : Z.lerp(0.7, 0.95, Z.inv(B(73), CUT, t));
    const stains = (scale = 1) => ({ type: 'stains', amount: S => stainAmt(S.t), realTime: true, scale });
    const snowL = (n = 40, extra = {}) => Object.assign({ type: 'snow', n, size: 2.6, speed: 46, alpha: 0.65 }, extra);
    const sparkAt = (area, extra = {}) => Object.assign({ type: 'sparkle', n: 6, size: 22, area }, extra);

    // ---- typography layouts tied to the images
    const fnLay = fn => ({ type: 'fn', fn });
    const pts = list => fnLay((k) => { const p = list[Math.min(k, list.length - 1)]; return [p[0], p[1], p[2] || 0, p[3] || 1]; });
    const along = (path, u) => { const f = u * (path.length - 1), q = Math.min(path.length - 2, Math.floor(f)), r = f - q; return [Z.lerp(path[q][0], path[q + 1][0], r), Z.lerp(path[q][1], path[q + 1][1], r)]; };
    // the two directions and their words pressed into the two footpaths of the field (perspective: flattened, smaller far away)
    const forkLay = (n) => fnLay((k, cnt, S, st) => {
      if (!S.toScr) return [W / 2, H * 0.8, 0, 1];
      const iL = idx(n, LEFT), iR = idx(n, RIGHT), i = st.i;
      let f, ang = 0;
      if (i === iL - 1 || i === iL) { f = along(S.pathL, i === iL ? 0.5 : 0.18); ang = 0.35; }
      else if (i === iR - 1 || i === iR) { f = along(S.pathR, i === iR ? 0.5 : 0.18); ang = -0.3; }
      else f = [0.47, 0.9];
      const [x, y] = S.toScr(f[0], f[1]), depth = Z.clamp((f[1] - 0.45) / 0.55);
      return [x, y, ang, 0.32 + 0.78 * depth, 1, 0.48];
    });
    // words streaming off behind the runner like her shawl
    const trailLay = (ex, ey, speed = 300) => fnLay((k, n, S, st) => { const age = Math.max(0, S.t - st.on); return [ex - age * speed, ey + 34 * Math.sin(age * 4 + st.i), 0.08 * Math.sin(age * 3 + st.i), 1]; });
    const palmPt = (fx, fy) => fnLay((k, n, S) => (S.palm ? [...S.palm.toScr(fx, fy), 0, 1] : [W / 2, H / 2, 0, 1]));
    void palmPt;

    // ================================================================== shots
    const S = [];
    // every shot carries the impact overlay (集中線) on its text layer
    const shot = (id, t0, t1, scene, args, extra = {}) => { if (t1 > t0 + 1e-3) S.push(Object.assign({ id, t0, t1, scene, args, lyric: 'none', text: (ctx, St) => G.impactOverlay(ctx, St) }, extra)); };
    const NIGHT_FILL = ['#1B2742', '#0D1322'];
    const INK = '#2E3850', SLATE = '#4A5872';
    const RIM_ICE = { color: '#FFFFFF', blur: 10, a: 0.9, scale: 1.015 }, RIM_RED = { color: '#FF5A78', blur: 12, a: 0.75, scale: 1.02 }, RIM_WARM = { color: '#FFD9A8', blur: 10, a: 0.8, scale: 1.015 };
    const RUN = { frames: [A + 'run.png', A + 'run_pass.png', A + 'run_b.png', A + 'run_pass.png'], perBeat: 3 };
    const beatsBetween = (a, b) => audio.beats.filter(x => x >= a - 1e-6 && x < b - 1e-6);

    // ---- impact frames (negative / carmine punch + 集中線) on the film's biggest hits (<= 3 per second)
    G.IMPACTS = [
      { t: B(9), dur: 0.1, style: 'neg', y: 600 }, { t: onOf(2, LEFT, 20.55), dur: 0.08, style: 'lines', x: 560, y: 900 }, { t: onOf(2, RIGHT, 21.55), dur: 0.08, style: 'lines', x: 1360, y: 880 },
      { t: B(25), dur: 0.1, style: 'lines', y: 620 }, { t: B(34), dur: 0.12, style: 'red', y: 900 },
      { t: B(41), dur: 0.12, style: 'red', y: 420 }, { t: onOf(21, LEFT, 84.15), dur: 0.08, style: 'lines', x: 560, y: 900 }, { t: onOf(21, RIGHT, 85.94), dur: 0.08, style: 'lines', x: 1360, y: 880 },
      { t: B(65), dur: 0.12, style: 'neg', y: 420 }, { t: B(71), dur: 0.14, style: 'red', x: 1150, y: 260 }, { t: B(73), dur: 0.12, style: 'red', y: 420 }, { t: B(78) + 0.05, dur: 0.12, style: 'red', x: 960, y: 420 },
    ];

    // ===== INTRO
    const BR = { branch: { x: 900, y: 600, h: 720, rot: 0 }, tip: [940 / 1169, 22 / 929], budH: 150 };
    shot('s01', 0, B(3), 'hgdBranch', Object.assign({ mode: 'intro', reveal: [0.3, 3.0], budAt: 3.0, zoom: { from: 0.94, to: 1.1, cx: W / 2, cy: H / 2 } }, BR), { post: { boil: 0.6 } });
    shot('s02', B(3), B(5), 'hgdPalm', { mode: 'intro', palm: [0.63, 0.52], view: { from: { zoom: 1.0, x: -0.4, y: 0.3 }, to: { zoom: 1.2, x: -0.9, y: -0.1 } } }, { trans: { type: 'whiteout', dur: 0.4 } });
    shot('s03', B(5), 11.38, 'hgdShot', { chars: [{ img: A + 'bust_calm.png', blink: { img: A + 'bust_calm_blink.png', every: 2.4 }, x: 980, y: 1150, h: 1180, h2: 1360, tilt: 0.03, wind: 12, lag: false, rim: RIM_ICE }],
      fxBack: [{ type: 'leak', blobs: [[0.2, 0.25, '214,228,255'], [0.85, 0.7, '255,226,214']], r: 760, alpha: 0.5, comp: 'multiply' }], fx: [snowL(36), { type: 'fgSnow', n: 8, size: 70, speed: 160, wind: 0.3, alpha: 0.8 }] },
      { trans: { type: 'xfade', dur: 0.35 } });
    shot('s04', 11.38, 15.54, 'hgdTitle', { glyphTimes: [bt(7, 0), bt(7, 1), bt(7, 2)] }, { post: { boil: 0.5 } });

    // ===== REFRAIN 1 — the bewildered question
    shot('s05', 15.54, 17.85, 'hgdShot', { bg: BG + 'field_fork.png', view: { from: { zoom: 1.55, y: -0.9 }, to: { zoom: 1.12, y: 0.25 }, ease: 'outExpo' }, punch: [B(9)], kick: 0.02,
      chars: [{ img: A + 'turn_mid.png', poses: [{ at: bt(9, 1), img: A + 'turn_back.png' }], x: 1060, y: 990, h: 560, wind: 30, gust: 30, lag: false, tilt: 0.02, rim: RIM_ICE }],
      fx: [snowL(90, { wind: 0.6, speed: 90 }), { type: 'fgSnow', n: 12, size: 60, speed: 420, wind: 0.9 }, { type: 'shock', at: [B(9)], y: 640, r: 1200 }],
      lyrics: [{ line: 1, z: 'front', fx: 'snow', lay: { type: 'col', x: 470, y: 230, pitch: 1.1 }, size: 96, weight: 500, color: SLATE, wind: 1.3, points: 220, solid: 0.55, lead: 0.3, inDur: 0.6, until: 17.45, outDur: 0.45 }] });
    shot('s06', 17.85, 20.09, 'hgdShot', { bg: BG + 'field_fork.png', view: { from: { zoom: 1.45, x: 0.9, y: 0.45, rot: -0.03 }, to: { zoom: 1.45, x: -0.9, y: 0.45, rot: 0.02 }, ease: 'linear' },
      chars: [{ img: A + 'run.png', seq: RUN, x: 1000, y: 1035, h: 660, bob: { amp: 16, steps: 1.5, sway: 0.012 }, wind: 40, lag: false, flutter: 1.2, rim: RIM_ICE }],
      fx: [{ type: 'speed', a: 0.4 }, snowL(110, { wind: -1.6, speed: 90 }), { type: 'fgSnow', n: 10, size: 80, speed: 300, wind: -2.4 }],
      lyrics: [{ line: 2, from: 0, to: 5, z: 'back', fx: 'trail', lay: trailLay(860, 540), size: 88, weight: 500, color: INK, life: 2.4, inDur: 0.2 }] },
      { trans: { type: 'whip', dur: 0.16, dir: -1 } });
    shot('s07', 20.09, 22.59, 'hgdFork', { mode: 'ask', line: 2, slams: [onOf(2, LEFT, bt(11, 1)), onOf(2, RIGHT, bt(11, 3))],
      lyrics: [{ line: 2, from: 5, to: 10, z: 'back', fx: 'emboss', lay: forkLay(2), size: 300, weight: 500, inDur: 0.3, until: 22.4, alpha: 1.6 }] });
    shot('s08', 22.59, 26.09, 'hgdPalm', { mode: 'look', palm: [0.63, 0.52], view: { from: { zoom: 1.1, x: -0.8, rot: -0.02 }, to: { zoom: 1.3, x: -1, rot: 0.02 } },
      lyrics: [{ line: 3, from: 0, to: 7, z: 'back', fx: 'ink', fam: 'hand', size: 60, color: '#7A2E3A', lay: fnLay((k, n, S) => { const pp = [[0.31, 0.47], [0.355, 0.44], [0.4, 0.44], [0.44, 0.47], [0.47, 0.52], [0.505, 0.555], [0.545, 0.53]]; const [x, y] = S.palm.toScr(...pp[k]); return [x, y, (k - 3) * 0.08, 1]; }) },
        { line: 3, from: 7, to: 10, z: 'front', fx: 'ink', size: 44, weight: 700, color: P.carmine, lay: fnLay((k, n, S) => { const b = S.bug; const [x, y] = b.pathAt(b.walkT - 0.42 * (k + 1)); return [x, y + 40 * S.palm.unit, 0, 1]; }) }] },
      { trans: { type: 'whiteout', dur: 0.3 } });
    const morphAt = onOf(4, FLOWER, bt(14, 2));
    shot('s09', 26.09, 30.59, 'hgdPalm', { mode: 'morph', morphAt, palm: [0.63, 0.52], view: { from: { zoom: 1.3, x: -1 }, to: { zoom: 1.55, x: -1, y: -0.2 } },
      lyrics: [{ line: 4, z: 'front', fx: 'ink', size: 54, weight: 400, colors: [INK, INK, INK, INK, INK, INK, INK, P.carmine, P.carmine, P.carmine],
        lay: fnLay((k, n, S, st) => { const [bx, by] = S.bug.pathAt(morphAt); const unfurl = E.outCubic(Z.clamp((S.t - st.on) / 1.2)); const an = -Math.PI * 0.95 + k * 0.42, r = (150 + 24 * k) * (0.7 + 0.3 * unfurl) * S.palm.unit * 1.25; return [bx + Math.cos(an) * r, by - 90 * S.palm.unit + Math.sin(an) * r * 0.8, an + Math.PI / 2, k >= 7 ? 1.35 : 1]; }) }] });

    // ===== VERSE — last winter (quiet, cold, deep)
    shot('s10', 30.59, 34.59, 'hgdShot', { bg: BG + 'sky.png', view: { from: { zoom: 1.3, y: 0.6 }, to: { zoom: 1.08, y: -0.3 }, ease: 'inOutCubic' },
      fxBack: [{ type: 'custom', fn: (ctx, St) => { const k = Math.sin(Math.PI * St.p); G.fx(ctx, St, { type: 'sun', x: 560, y: 430 - 110 * k, r: 64 }); } }],
      chars: [{ img: A + 'back_walk.png', x: 1320, y: 1110, h: 300, sil: '#7D8BA2', wind: 10, lag: false }], fx: [snowL(40), { type: 'fgSnow', n: 6, size: 90, speed: 120, wind: 0.4, alpha: 0.7 }],
      lyrics: [{ line: 5, z: 'front', fx: 'frost', lay: { type: 'row', x: 1040, y: 330, spacing: 1.28 }, size: 92, weight: 300, inDur: 0.6, hold: 0.3 }] },
      { trans: { type: 'xfade', dur: 0.4 } });
    const iSun = idx(6, SUN);
    shot('s11', 34.59, 38.59, 'hgdShot', { bg: BG + 'alley.png', view: { from: { zoom: 1.04, x: 0.2 }, to: { zoom: 1.2, x: 0.35 } },
      fxBack: [{ type: 'custom', fn: (ctx, St) => { ctx.save(); ctx.globalAlpha = 1 - St.p * 0.85; G.fx(ctx, St, { type: 'sun', x: 1180, y: 250 + 120 * St.p, r: 50 }); ctx.restore(); } }, { type: 'shafts', x: 1500, y: -80, angle: 2.0, n: 5, alpha: 0.28, gap: 110, width: 70 }],
      chars: [{ img: A + 'back_walk.png', x: 1150, y: 655, x2: 1165, y2: 640, h: 170, h2: 140, bob: { amp: 2, steps: 1 }, wind: 3, lag: false }], fx: [snowL(46), { type: 'fgSnow', n: 6, size: 70, speed: 140, wind: 0.3 }],
      lyrics: [{ line: 6, z: 'back', fx: 'wall', skip: iSun >= 0 ? [iSun] : [], lay: { type: 'col', x: 1760, y: 250, pitch: 1.08, per: 4, gap: 1.35 }, size: 104, weight: 600, alpha: 0.85, color: '#4E5A72' },
        ...(iSun >= 0 ? [{ line: 6, from: iSun, to: iSun + 1, z: 'back', fx: 'ink', lay: fnLay((k, n, S) => [1180, 250 + 120 * S.p, 0, 1]), size: 58, weight: 300, color: '#8D9BAD' }] : [])] },
      { trans: { type: 'xfade', dur: 0.3 } });
    shot('s12', 38.59, 42.59, 'hgdShot', { bg: BG + 'alley.png', view: { from: { zoom: 1.28, x: 0.3, y: 0.3 }, to: { zoom: 1.42, x: 0.38, y: 0.3 } },
      chars: [{ img: A + 'back_walk.png', x: 1000, y: 1090, x2: 1070, y2: 1040, h: 720, h2: 620, bob: { amp: 10, steps: 1 }, wind: 12, shadow: { dx: -330, dy: -10, skewX: 1.15, sy: 0.5, a: 0.22 } }],
      fx: [snowL(50), { type: 'fgSnow', n: 8, size: 90, speed: 200, wind: 0.5 }],
      lyrics: [{ line: 7, z: 'back', fx: 'shadow', lay: { type: 'col', x: 420, y: 240, pitch: 1.08, per: 4, gap: -1.4 }, size: 100, weight: 600, skew: -0.35, sy: 1, alpha: 0.4, soft: 1, color: '#3E4B63' }] });
    shot('s13', 42.59, 46.40, 'hgdShot', { bg: BG + 'alley.png', view: { from: { zoom: 1.4, x: -0.7, y: 0.45 }, to: { zoom: 1.62, x: -0.85, y: 0.5 } },
      chars: [{ img: A + 'sit_knees.png', x: 780, y: 1020, h: 560, wind: 6, lag: false, breathe: 1.6, shadow: { dx: 120, dy: 0, skewX: -1.2, sy: 0.25, a: 0.18 } }],
      fx: [snowL(50, { speed: 30 }), { type: 'fgSnow', n: 6, size: 110, speed: 90, wind: 0.2, alpha: 0.8 }],
      lyrics: [{ line: 8, z: 'front', fx: 'settle', lay: pts([[380, 990, 0.2], [470, 1030, -0.1], [560, 985, 0.15], [1010, 1000, -0.2], [1100, 1040, 0.1], [1190, 995, -0.05], [1280, 1030, 0.2], [1370, 990, -0.15]]), size: 56, weight: 500, color: SLATE, stroke: 'rgba(255,255,255,0.9)', strokeW: 5, fallT: 1.8, drop: 620, hold: 1.0 }] },
      { trans: { type: 'xfade', dur: 0.4 } });
    shot('s14', 46.40, B(25), 'hgdShot', { fill: ['#FBF6F1', '#ECE4DC'], chars: [{ img: A + 'bust_calm.png', blink: { img: A + 'bust_calm_blink.png', every: 1.4 }, x: 900, y: 1160, h: 1320, h2: 1180, tilt: 0.03, tiltF: 0.25, wind: 14, lag: false, rim: RIM_WARM }],
      fxBack: [{ type: 'leak', blobs: [[0.75, 0.3, '255,214,180'], [0.2, 0.8, '255,232,214']], r: 800, alpha: 0.55, comp: 'multiply' }],
      lyrics: [{ line: 9, z: 'front', fx: 'ink', fam: 'brush', lay: { type: 'col', x: 1420, y: 330, pitch: 1.05 }, size: 118, color: P.carmine }] },
      { trans: { type: 'whiteout', dur: 0.14 } });

    // ===== B1 — a house
    shot('s15', B(25), bt(26, 1), 'hgdHouse', { line: 10, beats: [B(25), bt(25, 1), bt(25, 2), B(26)], punch: [B(25), bt(25, 1), bt(25, 2), B(26)] });
    shot('s16', bt(26, 1), bt(28, 1), 'hgdShot', { bg: BG + 'room.png', view: { from: { zoom: 1.04, x: -0.2 }, to: { zoom: 1.2, x: 0.15 } },
      fxBack: [{ type: 'shafts', x: 1760, y: -120, angle: 2.25, n: 7, alpha: 0.5, gap: 120, width: 80, rgb: '255,246,228' }],
      chars: [{ img: A + 'curtain.png', x: 760, y: 1050, h: 920, wind: 16, flutter: 1, lag: false, tilt: 0.015 }],
      fx: [{ type: 'leak', blobs: [[0.9, 0.2, '255,236,210']], r: 900, alpha: 0.45 }],
      lyrics: [{ line: 11, z: 'back', fx: 'veil', lay: { type: 'col', x: 965, y: 140, pitch: 1.08, per: 5, gap: 1.15 }, size: 90, weight: 600, color: '#1E2638', soft: 1.1, alpha: 1 }] },
      { trans: { type: 'xfade', dur: 0.3 } });
    shot('s17', bt(28, 1), bt(29, 1), 'hgdShot', { fill: ['#F7F9FC', '#E6ECF3'], chars: [{ img: A + 'bride_bust.png', x: 980, y: 1170, h: 1200, h2: 1300, wind: 10, lag: false, tilt: 0.012, rim: RIM_ICE }],
      fx: [sparkAt([500, 150, 1450, 700], { n: 14, size: 34, rate: 1.2 })],
      lyrics: [{ line: 12, z: 'front', fx: 'beads', lay: pts([[360, 360, -0.12], [470, 610, -0.06], [1490, 360, 0.12], [1580, 610, 0.06]]), size: 180, weight: 900, points: 520 }] });
    shot('s18', bt(29, 1), bt(30, 1), 'hgdRouge', { lip: [0.44, 0.4], floodAt: 56.85, recedeAt: bt(30, 0) + 0.1,
      lyrics: [{ line: 13, z: 'front', fx: 'smear', fam: 'brush', lay: { type: 'row', x: 1430, y: 760, spacing: 0.95 }, size: 210, color: '#FFE4EA', smear: 0.9 }] });
    shot('s19', bt(30, 1), bt(32, 1), 'hgdCard', { line: 14 }, { post: { boil: 0.4 } });
    shot('s20', bt(32, 1), B(33), 'hgdShot', { fill: ['#F8FAFC', '#E4EAF1'], view: {}, punch: [bt(32, 2)],
      chars: [{ img: A + 'master_c.png', x: 1080, y: 1040, h: 960, h2: 1080, wind: 50, gust: 60, lag: false, flutter: 1.4, rim: RIM_ICE }],
      fx: [{ type: 'petals', n: 18, size: 12, speed: 90, wind: -1.2 }, { type: 'fgPetals', n: 3, size: 110, speed: 700, dir: -1, alpha: 0.8 }],
      lyrics: [{ line: 15, z: 'front', fx: 'blow', fam: 'brush', lay: { type: 'col', x: 560, y: 300, pitch: 1.05 }, size: 124, color: P.carmine, wind: 520, lift: 60, delay: 0.3 }] },
      { trans: { type: 'xfade', dur: 0.25 } });

    // ===== B2 — to die in spring
    shot('s21', B(33), bt(34, 1), 'hgdFall', { land: B(34), slow: 0.34, x: 1120, y: 1060, h: 1240, pose2: { at: bt(33, 2) + 0.2, img: A + 'fall_b.png' },
      lyrics: [{ line: 16, z: 'front', fx: 'fall', lay: fnLay((k, n, S) => { const f = S.fall || { hx: 900, hy: 1010 }; return [f.hx - 380 + k * 170, 260 + (k % 2) * 90, 0, 1]; }), size: 100, weight: 500, color: INK, delay: 0.5, gravity: 520, life: 3 }] });
    shot('s22', bt(34, 1), bt(36, 1), 'hgdShot', { bg: A + 'lying_flowers.png', view: { from: { zoom: 1.12, rot: -0.05 }, to: { zoom: 1.4, rot: 0.05, x: -0.3, y: -0.3 } },
      fx: [{ type: 'petals', n: 36, size: 12, speed: 50, wind: 0.2 }, { type: 'fgPetals', n: 4, size: 150, speed: 260, alpha: 0.75 }, { type: 'leak', blobs: [[0.8, 0.15, '255,236,220']], r: 800, alpha: 0.4 }],
      lyrics: [{ line: 17, z: 'back', fx: 'ink', lay: pts([[260, 760, 0.3], [430, 900, -0.25], [700, 1000, 0.15], [1060, 250, -0.2], [1320, 380, 0.35], [1530, 560, -0.1], [1680, 300, 0.25], [1760, 760, -0.3]]), size: 88, weight: 700, color: '#FFFFFF', stroke: 'rgba(60,70,90,0.55)', strokeW: 4 }] },
      { trans: { type: 'xfade', dur: 0.35 } });
    shot('s23', bt(36, 1), bt(38, 1), 'hgdMud', { lyrics: [{ line: 18, z: 'front', fx: 'roots', lay: { type: 'row', x: 960, y: 450, spacing: 1.3 }, size: 110, weight: 700, color: '#241B19', grow: 1.6 }] },
      { trans: { type: 'xfade', dur: 0.3 } });
    shot('s24', bt(38, 1), bt(40, 3), 'hgdPage', { page: A + 'lying_flowers.png', under: BG + 'mud.png', bugs: 5,
      lyrics: [{ line: 19, z: 'page', fx: 'ink', lay: { type: 'row', x: 960, y: 520, spacing: 1.18 }, size: 100, weight: 600, color: '#242424', lead: 0.05 }] });

    // ===== REFRAIN 2 — the question as accusation (rouge, montage, impacts)
    shot('s25', bt(40, 3), B(42), 'hgdShot', { fill: ['#F8FAFC', '#E6ECF3'], punch: [B(41)], kick: 0.035,
      chars: [{ img: A + 'sing_power.png', lips: { closed: A + 'sing_power_closed.png', line: 20 }, x: 1000, y: 1200, h: 1250, h2: 1340, wind: 60, gust: 40, lag: false, flutter: 1.4, rim: RIM_RED }],
      fx: [stains(), { type: 'fgPetals', n: 4, size: 140, speed: 900, alpha: 0.85 }, { type: 'shock', at: [B(41)], y: 420, r: 1300, rgb: '255,220,228' }],
      lyrics: [{ line: 20, z: 'front', fx: 'stamp', lay: pts([[380, 420], [470, 210], [660, 110], [1340, 110], [1530, 210], [1620, 420], [1640, 660]]), size: 140 }] });
    shot('s26', B(42), bt(42, 3), 'hgdShot', { bg: BG + 'field_fork.png', view: { from: { zoom: 1.5, x: 0.9, y: 0.45, rot: 0.03 }, to: { zoom: 1.5, x: -0.5, y: 0.45, rot: -0.02 }, ease: 'linear' },
      chars: [{ img: A + 'run.png', seq: RUN, x: 1000, y: 1035, h: 680, bob: { amp: 17, steps: 1.5, sway: 0.012 }, wind: 46, lag: false, flutter: 1.3, rim: RIM_RED }],
      fx: [{ type: 'speed', a: 0.5 }, snowL(90, { wind: -1.6, speed: 100 }), stains(), { type: 'fgPetals', n: 4, size: 120, speed: 1100, dir: -1, alpha: 0.8 }],
      lyrics: [{ line: 21, from: 0, to: 5, z: 'back', fx: 'trail', lay: trailLay(860, 540, 340), size: 96, fam: 'brush', color: P.carmine, life: 2.0, inDur: 0.15 }] },
      { trans: { type: 'whip', dur: 0.16, dir: -1 } });
    shot('s27', bt(42, 3), bt(44, 1), 'hgdFork', { mode: 'accuse', line: 21, slams: [onOf(21, LEFT, bt(43, 0)), onOf(21, RIGHT, bt(43, 3))],
      lyrics: [{ line: 21, from: 5, to: 10, z: 'back', fx: 'stamp', lay: forkLay(21), size: 250, inDur: 0.2, until: 86.4 }] });
    shot('s28', bt(44, 1), bt(45, 1), 'hgdPalm', { mode: 'crush', crushAt: bt(44, 2), palm: [0.63, 0.52], view: { from: { zoom: 1.15, x: -0.8 }, to: { zoom: 1.35, x: -1 } },
      lyrics: [{ line: 22, from: 0, to: 5, z: 'front', fx: 'bleed', lay: fnLay((k, n, S) => { const pm = S.palm; return [pm.px + (k - 2) * 90 * pm.unit * 1.2, pm.py + (110 + 40 * (k % 2)) * pm.unit, 0, 1]; }), size: 64, weight: 600, drip: 36 }] });
    // montage on the beats: her eyes, the rouge, the hand — each glyph of the insect's name stamped on its beat
    const L22 = G.lineInfo(22);
    const mt = beatsBetween(bt(45, 1), B(46));
    shot('s28b', bt(45, 1), B(46), 'hgdBurst', { times: mt.length ? mt : [bt(45, 1)], cuts: [
        { img: A + 'face_close.png', plate: true, view: { zoom: 1.9, x: -0.15, y: -0.25 }, viewTo: { zoom: 2.05, x: -0.15, y: -0.25 }, lines: true, flash: '#FFFFFF', glyph: L22 ? { line: 22, i: L22.chars.length - 3, x: 1520, y: 560, size: 380 } : null },
        { img: A + 'bust_sing.png', bg: [P.carmine, '#7A0E22'], x: 1000, y: 1250, h: 1500, rim: RIM_ICE, lines: true, lineColor: 'rgba(255,240,244,0.7)', glyph: L22 ? { line: 22, i: L22.chars.length - 2, x: 420, y: 560, size: 380, color: '#FFFFFF' } : null },
        { img: A + 'palm_close.png', plate: true, view: { zoom: 1.7, x: -1, y: 0.1 }, viewTo: { zoom: 1.85, x: -1, y: 0.1 }, tint: { color: P.carmine, a: 0.35, comp: 'multiply' }, glyph: L22 ? { line: 22, i: L22.chars.length - 1, x: 1480, y: 540, size: 400 } : null },
      ] }, { post: { boil: 1.2, ca: 2 } });
    shot('s29', B(46), bt(47, 1), 'hgdPalm', { mode: 'crack', crackAt: bt(46, 1), palm: [0.63, 0.52], view: { from: { zoom: 1.35, x: -1 }, to: { zoom: 1.6, x: -1 } },
      lyrics: [{ line: 23, from: 0, to: 6, z: 'front', fx: 'float', lay: fnLay((k, n, S) => { const pm = S.palm; const an = -Math.PI / 2 + (k - 2.5) * 0.5; return [pm.px + Math.cos(an) * 260 * pm.unit, pm.py - 120 * pm.unit + Math.sin(an) * 230 * pm.unit, an + Math.PI / 2, 1]; }), size: 70, weight: 600, color: P.carmine, rise: 24 }] },
      { trans: { type: 'whiteout', dur: 0.2 } });
    shot('s30', bt(47, 1), bt(48, 1), 'hgdShot', { fill: ['#F8FAFC', '#E6ECF3'], kick: 0.03, chars: [{ img: A + 'bust_sing.png', lips: { closed: A + 'bust_sing_closed.png', line: 23, open: 0.45, pre: 0.2 }, x: 960, y: 1170, h: 1220, h2: 1330, wind: 24, gust: 20, lag: false, tilt: 0.02, rim: RIM_RED }],
      fx: [stains(0.8), { type: 'fgPetals', n: 3, size: 130, speed: 600, alpha: 0.8 }],
      lyrics: [{ line: 23, from: 6, to: 10, z: 'front', fx: 'float', lay: pts([[420, 640], [560, 420], [1380, 420], [1520, 640]]), size: 100, weight: 600, color: P.carmine, rise: 40 }] });
    shot('s31', bt(48, 1), B(49), 'hgdShot', { fill: ['#F2F5F9', '#DCE3EC'], chars: [{ img: A + 'turn_back.png', x: 1080, y: 1060, h: 900, wind: 22, out: { at: 0.7, dur: 0.6, dx: 760, ease: 'inCubic' } }], fx: [stains(0.8)],
      lyrics: [{ line: 24, z: 'back', fx: 'ink', lay: { type: 'col', x: 760, y: 250, pitch: 1.12 }, size: 146, weight: 300, color: SLATE }] },
      { trans: { type: 'smear', dur: 0.1 } });

    // ===== B3 — the skin (night blue, intimate)
    shot('s32', B(49), bt(50, 1), 'hgdShot', { fill: NIGHT_FILL, chars: [{ img: A + 'reach.png', poses: [{ at: (G.lineInfo(25) || { end: 98.0 }).end + 0.1, img: A + 'reach_b.png' }], x: 960, y: 1180, h: 1150, h2: 1320, wind: 10, lag: false, rim: { color: '#9CB8FF', blur: 14, a: 0.7, scale: 1.02 } }],
      fx: [sparkAt([300, 250, 1100, 800], { dark: true, n: 8 }), { type: 'grain', a: 0.05 }, { type: 'leak', blobs: [[0.2, 0.45, '255,200,140']], r: 600, alpha: 0.35 }], grain: false,
      lyrics: [{ line: 25, z: 'front', fx: 'ink', lay: pts([[300, 430], [400, 380], [470, 470], [360, 540]]), size: 74, weight: 500, color: '#FFE9C8', glow: '#F2C48C', glowR: 26, hold: 0.2, outDur: 0.6 }] },
      { trans: { type: 'xfade', dur: 0.5 } });
    shot('s33', bt(50, 1), bt(52, 1), 'hgdDoll', { char: A + 'bust_calm.png', lyrics: [{ line: 26, z: 'xray', fx: 'whisper', lay: { type: 'col', x: 1000, y: 360, pitch: 1.12, per: 5, gap: 1.4 }, size: 58, weight: 500, color: '#55627C', alpha: 0.9 }] });
    shot('s34', bt(52, 1), bt(54, 1), 'hgdBed', { mode: 'warm', lie: { x: 1070, y: 650, h: 300, rot: -0.03 },
      lyrics: [{ line: 27, z: 'bed', fx: 'ink', lay: { type: 'path', pts: [[700, 770], [960, 790], [1220, 785], [1480, 770]] }, size: 56, weight: 500, colors: ['#E0A266', '#E0A266', '#E0A266', '#E0A266', '#9DBCF0', '#9DBCF0', '#9DBCF0', '#9DBCF0'] }] },
      { trans: { type: 'xfade', dur: 0.5 } });
    shot('s35', bt(54, 1), bt(56, 1), 'hgdBed', { mode: 'split', lie: { x: 1070, y: 650, h: 300, rot: -0.03 }, splitAt: 106.85, mid: 1060,
      lyrics: [{ line: 28, z: 'bed', fx: 'ink', lay: { type: 'row', x: 1060, y: 470, spacing: 1.75 }, size: 72, weight: 500, colors: ['#E0A266', '#E0A266', '#E0A266', '#E8EEF6', '#9DBCF0', '#9DBCF0', '#9DBCF0'] }] });
    shot('s36', bt(56, 1), B(57), 'hgdShot', { fill: NIGHT_FILL, chars: [{ img: A + 'bust_calm.png', blink: { img: A + 'bust_calm_blink.png', every: 0.9 }, x: 960, y: 1500, y2: 1900, h: 1500, h2: 2300, wind: 8, lag: false, ease: 'inCubic' }], tint: [{ color: '#24365F', a: 0.35, comp: 'multiply' }], grain: 0.06,
      lyrics: [{ line: 29, z: 'back', fx: 'ink', lay: fnLay((k, n, S) => [960 + (k - 1) * 520 * (1 + 0.5 * S.p), 520, 0, 1 + 0.7 * E.inCubic(S.p)]), size: 360, weight: 200, color: 'rgba(232,238,246,0.28)' }] });

    // ===== B4 — workaholic (mechanical: a punch on every beat)
    shot('s37', B(57), bt(58, 1), 'hgdShot', { bg: BG + 'office.png', view: { from: { zoom: 1.0 }, to: { zoom: 1.6 }, ease: 'inCubic' }, punch: beatsBetween(B(57), bt(58, 1)), fx: [{ type: 'flicker', a: 0.3 }, { type: 'speed', a: 0.25 }],
      lyrics: [{ line: 30, z: 'front', fx: 'recede', lay: pts([[520, 820], [960, 900], [1400, 820]]), size: 150, weight: 600, color: INK, copies: 8, shrink: 0.7, toward: (k) => [[440, -340], [0, -420], [-440, -340]][k] }] },
      { trans: { type: 'whiteout', dur: 0.2 } });
    shot('s38', bt(58, 1), bt(60, 1), 'hgdCalendar', { from: bt(58, 1), lyrics: [{ line: 31, z: 'note', fx: 'ink', fam: 'hand', lay: { type: 'row', x: 0, y: 0, spacing: 0.98, align: 'left' }, size: 52, color: '#2A3550', hold: 2 }] });
    shot('s39', bt(60, 1), bt(62, 1), 'hgdShot', { bg: A + 'desk.png', view: { from: { zoom: 1.05 }, to: { zoom: 1.2, x: -0.3 } }, punch: beatsBetween(bt(60, 1), bt(62, 1)).filter((b, i) => i % 2 === 0),
      fx: [{ type: 'custom', fn: (ctx, St) => { const night = ((St.clock.beat(St.t) % 2) + 2) % 2 === 0; D.fill(ctx, night ? '#101A33' : '#FFF4E2', night ? 0.42 : 0.14, night ? 'multiply' : 'screen'); } }, { type: 'flicker', a: 0.2 }],
      lyrics: [{ line: 32, z: 'front', fx: 'stamp', lay: pts([[230, 380], [380, 520], [260, 690], [540, 610], [720, 730], [900, 650], [1080, 770], [1260, 690], [1440, 790], [1600, 700]]), size: 128, hold: 2 }] });
    shot('s40', bt(62, 1), B(64), 'hgdMemory', { shots: [['s08', 24.2], ['s06', 19.2], ['s16', 52.5]], burns: [bt(62, 3) + 0.9, bt(63, 1) + 0.9, bt(63, 3) + 0.9],
      lyrics: [0, 1, 2].map(j => ({ line: 33, from: j * 3, to: j * 3 + 3, z: 'print' + j, fx: 'ink', fam: 'hand', lay: { type: 'row', x: 0, y: 0, spacing: 1.05 }, size: 46, color: '#2A3550', hold: 4 })) });
    shot('s41', B(64), bt(64, 3), 'hgdShot', { bg: BG + 'snow.png', view: { from: { zoom: 1.3 }, to: { zoom: 1.0 }, ease: 'inCubic' }, fx: [snowL(240, { size: 5, speed: 200, wind: 0.8, alpha: 0.9 }), { type: 'fgSnow', n: 20, size: 70, speed: 700, wind: 1.2 }, { type: 'custom', fn: (ctx, St) => D.fill(ctx, '#F7F9FC', 0.6 * St.p) }],
      lyrics: [{ line: 33, from: 6, to: 9, z: 'front', fx: 'float', lay: pts([[820, 620], [960, 560], [1100, 620]]), size: 78, weight: 400, color: '#8D9BAD', rise: 90, lead: 0.4 }] },
      { trans: { type: 'whiteout', dur: 0.3 } });

    // ===== REFRAIN 3 — snow in June (maximum)
    shot('s42', bt(64, 3), B(66), 'hgdShot', { bg: BG + 'snow.png', view: { from: { zoom: 1.3, rot: -0.03 }, to: { zoom: 1.12, rot: 0.02 } }, punch: [B(65)], kick: 0.035,
      chars: [{ img: A + 'sing_power.png', lips: { closed: A + 'sing_power_closed.png', line: 34 }, x: 1080, y: 1200, h: 1260, h2: 1360, wind: 80, gust: 60, lag: false, flutter: 1.5, rim: RIM_ICE }],
      fx: [snowL(340, { size: 5, speed: 240, wind: 1.0, alpha: 0.95 }), { type: 'fgSnow', n: 18, size: 90, speed: 800, wind: 1.6 }, stains(), { type: 'shock', at: [B(65)], y: 420, r: 1300 }],
      lyrics: [{ line: 34, z: 'front', fx: 'snow', lay: { type: 'col', x: 430, y: 190, pitch: 1.12 }, size: 112, weight: 500, color: SLATE, wind: 1.8, points: 240, solid: 0.5, lead: 0.3, inDur: 0.5 }] });
    shot('s43', B(66), bt(66, 3), 'hgdShot', { bg: BG + 'snow.png', view: { from: { zoom: 1.5, x: 0.9, y: 0.3, rot: -0.04 }, to: { zoom: 1.5, x: -0.4, y: 0.3, rot: 0.02 }, ease: 'linear' },
      chars: [{ img: A + 'run.png', seq: RUN, x: 1000, y: 1035, h: 680, bob: { amp: 17, steps: 1.5 }, wind: 50, lag: false, flutter: 1.4, rim: RIM_ICE }],
      fx: [{ type: 'speed', a: 0.55 }, snowL(340, { size: 5, speed: 280, wind: -1.8, alpha: 0.95 }), { type: 'fgSnow', n: 16, size: 100, speed: 600, wind: -3 }],
      lyrics: [{ line: 35, from: 0, to: 5, z: 'back', fx: 'trail', lay: trailLay(860, 540, 360), size: 92, weight: 500, color: SLATE, life: 1.8, inDur: 0.15 }] },
      { trans: { type: 'whip', dur: 0.16, dir: -1 } });
    shot('s44', bt(66, 3), bt(68, 1), 'hgdFork', { mode: 'snow', line: 35, slams: [onOf(35, LEFT, bt(67, 0)), onOf(35, RIGHT, bt(67, 3))],
      lyrics: [{ line: 35, from: 5, to: 10, z: 'back', fx: 'emboss', lay: forkLay(35), size: 300, weight: 500, inDur: 0.3, until: 133.9, outDur: 0.6, alpha: 1.6 }] });
    shot('s45', bt(68, 1), bt(69, 1), 'hgdPalm', { mode: 'snow', palm: [0.63, 0.52], landings: [bt(68, 2), bt(68, 3), bt(69, 0)], view: { from: { zoom: 1.15, x: -0.8 }, to: { zoom: 1.35, x: -1 } },
      lyrics: [{ line: 36, from: 0, to: 6, z: 'front', fx: 'flake', lay: fnLay((k, n, S) => { const q = [[0.33, 0.5], [0.37, 0.46], [0.41, 0.5], [0.45, 0.55], [0.49, 0.6], [0.54, 0.6]][k]; return [...S.palm.toScr(q[0], q[1]), 0, 1]; }), size: 56, weight: 700, fallT: 1.0, drop: 640, hold: 0.6 }] },
      { trans: { type: 'whiteout', dur: 0.25 } });
    const L36 = G.lineInfo(36);
    shot('s45b', bt(69, 1), B(70), 'hgdBurst', { times: beatsBetween(bt(69, 1), B(70)), cuts: [
        { img: A + 'pull_pin.png', bg: ['#F4F7FA', '#D7E3EE'], x: 980, y: 1280, h: 1500, rim: RIM_ICE, lines: true, lineColor: 'rgba(74,88,114,0.55)', glyph: L36 ? { line: 36, i: L36.chars.length - 3, x: 1540, y: 520, size: 360 } : null },
        { img: A + 'face_close.png', plate: true, view: { zoom: 1.8, x: 0.1, y: -0.3 }, viewTo: { zoom: 1.95, x: 0.1, y: -0.3 }, lines: true, glyph: L36 ? { line: 36, i: L36.chars.length - 2, x: 420, y: 540, size: 360 } : null },
        { img: A + 'palm_close.png', plate: true, view: { zoom: 1.6, x: -1, y: 0 }, viewTo: { zoom: 1.75, x: -1, y: 0 }, tint: { color: P.carmine, a: 0.3, comp: 'multiply' }, glyph: L36 ? { line: 36, i: L36.chars.length - 1, x: 1500, y: 540, size: 380 } : null },
      ] }, { post: { boil: 1.2, ca: 2.5 } });
    const PIN = { u: 0.56, v: 0.17 };
    shot('s46', B(70), bt(71, 2), 'hgdShot', { fill: ['#FAFBFD', '#E8EDF4'], extra: [PR + 'bud_closed.png'], punch: [B(71)], view: {},
      chars: [{ img: A + 'pull_pin.png', poses: [{ at: B(71), img: A + 'pull_pin_b.png' }], x: 980, y: 1200, h: 1200, h2: 1300, wind: 70, gust: 60, lag: false, flutter: 1.5, rim: RIM_ICE }],
      fx: [snowL(260, { size: 4.5, speed: 220, wind: 0.9, alpha: 0.9 }), { type: 'fgSnow', n: 14, size: 90, speed: 700, wind: 1.4 }, { type: 'shock', at: [B(71)], x: 1150, y: 260, r: 1300, rgb: '255,210,220' },
        { type: 'petals', n: 30, size: 12, speed: 160, wind: 1.4, alpha: 0.9 }],
      lyrics: [{ line: 37, from: 0, to: 6, z: 'front', fx: 'blow', lay: { type: 'col', x: 1500, y: 180, pitch: 1.08 }, size: 80, weight: 500, color: SLATE, wind: 620, lift: 110, delay: 0.35 }] });
    shot('s47', bt(71, 2), bt(72, 3), 'hgdShot', { bg: BG + 'snow.png', view: { from: { zoom: 1.12, y: 0.3 }, to: { zoom: 1.24, y: 0.3 } }, focus: [0.9, 0.1], extra: [PR + 'bud_closed.png'],
      chars: [{ img: A + 'kneel_snow.png', x: 1180, y: 1000, h: 700, wind: 34, lag: false, breathe: 2 }],
      fx: [snowL(220, { size: 4, speed: 150, wind: 0.5, alpha: 0.9 }), { type: 'custom', fn: (ctx, St) => {
        const im = Z.imgSync(PR + 'bud_closed.png'), f = 1 - St.p;
        ctx.save(); ctx.translate(520, 930); ctx.rotate(1.35);
        D.sprite(ctx, f > 0.5 ? G.blurred(im, 8) : im, 0, 0, 380, { anchor: [0.5, 0.5] }); ctx.restore();
      } }, { type: 'fgSnow', n: 10, size: 110, speed: 300, wind: 0.6 }],
      lyrics: [{ line: 37, from: 6, to: 10, z: 'front', fx: 'settle', lay: pts([[250, 1000, 0.2], [380, 1035, -0.1], [680, 1030, 0.15], [800, 990, -0.2]]), size: 60, weight: 500, color: SLATE, stroke: 'rgba(255,255,255,0.9)', strokeW: 5, fallT: 1.4, drop: 560, hold: 1 }] });

    // ===== OUTRO — the bloom
    shot('s48', bt(72, 3), B(74), 'hgdShot', { fill: ['#F8FAFC', '#E6ECF3'], punch: [B(73)], kick: 0.035,
      chars: [{ img: A + 'sing_power.png', lips: { closed: A + 'sing_power_closed.png', line: 38 }, x: 1000, y: 1200, h: 1280, h2: 1380, wind: 70, gust: 50, lag: false, flutter: 1.5, rim: RIM_RED }],
      fx: [{ type: 'petals', n: 90, size: 14, speed: 160, wind: 1.1 }, { type: 'fgPetals', n: 6, size: 150, speed: 1000, alpha: 0.85 }, snowL(60, { size: 4, speed: 160, wind: 0.8 }), stains(), { type: 'shock', at: [B(73)], y: 420, r: 1300, rgb: '255,210,220' }],
      lyrics: [{ line: 38, z: 'front', fx: 'float', lay: pts([[360, 760], [440, 520], [560, 320], [1440, 320], [1560, 520], [1640, 760], [1000, 150]]), size: 92, weight: 600, color: P.carmine, rise: 70 }] });
    shot('s49', B(74), bt(76, 1), 'hgdShot', { bg: A + 'face_close.png', view: { from: { zoom: 1.0 }, to: { zoom: 1.2, y: -0.25 } },
      fx: [{ type: 'petals', n: 28, size: 12, speed: 60, wind: 0.4 }, { type: 'leak', blobs: [[0.85, 0.2, '255,214,224'], [0.1, 0.9, '214,228,255'], [0.05, 0.1, '255,222,230']], r: 900, alpha: 0.5 }],
      lyrics: [{ line: 39, z: 'front', fx: 'whisper', lay: { type: 'path', pts: [[1124, 610], [1130, 740], [1121, 870], [1104, 1010]] }, size: 36, weight: 600, color: P.blood, alpha: 0.9, hold: 0.4 }] },
      { trans: { type: 'xfade', dur: 0.4 } });
    const L40 = G.lineInfo(40);
    const THREAD = [[160, 990], [420, 770], [700, 700], [930, 540], [1100, 360], [1170, 270]];
    shot('s50', bt(76, 1), B(78), 'hgdBranch', Object.assign({ mode: 'swell', crack: B(77), zoom: { from: 1.1, to: 1.7, cx: 900, cy: 480, ease: 'inOutSine' },
      thread: { pts: THREAD, t0: (L40 ? L40.t0 : 150.85) - 0.3, t1: L40 ? L40.end : 153.9, w: 2.6 },
      lyrics: [{ line: 40, z: 'world', fx: 'ink', lay: { type: 'path', pts: THREAD.map(([x, y]) => [x + 14, y - 34]), a0: 0.04, a1: 0.86, orient: true }, size: 44, weight: 600, color: P.carmine }] }, BR),
      { trans: { type: 'whiteout', dur: 0.3 } });
    shot('s51', B(78), 155.35, 'hgdBranch', Object.assign({ mode: 'pop', pop: B(78) + 0.05, zoom: { from: 2.6, to: 1.9, ease: 'outExpo' },
      lyrics: [{ line: 41, z: 'world', fx: 'pop', lay: fnLay((k, n, S) => { const [tx, ty] = S.tip || [1175, 254]; const o = [[-210, -70], [-130, -210], [0, -265], [140, -200], [225, -60]][k]; return [tx + o[0], ty + o[1], (k - 2) * 0.14, 1]; }), size: 50, weight: 700, colors: [P.carmine, '#4AA8FF', P.carmine, P.rouge, '#4AA8FF'] }] }, BR));
    shot('s52', 155.35, CUT, 'hgdBranch', Object.assign({ mode: 'ignored', zoom: { from: 1.9, to: 0.42, ease: 'inOutCubic' },
      figure: { x: 2380, y: 1150, x2: 2500, y2: 1140, h: 150 },
      lyrics: [{ line: 42, z: 'world', fx: 'whisper', lay: { type: 'path', pts: [[930, 470], [1050, 380], [1125, 305], [1160, 275]] }, size: 24, weight: 600, color: SLATE, alpha: 0.85, hold: 3 }] }, BR));
    shot('s53', CUT, END, 'hgdBranch', Object.assign({ mode: 'tail', zoom: { from: 1.06, to: 1.06, cx: W / 2, cy: H / 2 },
      credits: [Z.CREDIT, 'movie: anime_mv · vocaloid-style-mv-pipeline (NikusonP, MIT) · JIZURA (hakoniwa, MIT)'] }, BR), { post: { boil: 0.4 } });

    Z.SHOTS = S;
    window.__zankoMeta.duration = END;
    Z.hud = null;
    Z.VERTICAL_CFG = { full: ['s01', 's04', 's53'], planMap: {}, title: Z.TITLE, sub: Z.TITLE_SUB, artist: Z.ARTIST, credits: [B(9), CUT], schemes: 'light', ambience: [236, 242, 248] };
  };
})();
