/* engine/timeline.js -- THE EDIT of 《花骨朵》 (HUAGUDUO), a fan-made Vocaloid-style lyric MV (vocal: 洛天依).
 *
 * Built with NikusonP's vocaloid-style-mv-pipeline (engine, JIZURA lyric layer, beat-locked editing, post pass) on the
 * song's own material: there is no drawn singer -- the protagonist is the poppy bud (花骨朵) itself, printed in sumi ink
 * and carmine on rice paper (docs/CONCEPT.md, docs/STORYBOARD.md). No image assets: every frame is drawn by the scenes
 * in engine/scenes/hgd_*.js on top of the shared kit Z.HGD (hgd_core.js).
 *
 * Lyrics never live in this repository: Z.HGD.loadLyrics() reads the user's LRC at runtime (analysis/lyrics_source.lrc,
 * and analysis/lyrics_mv.lrc = the same file with JIZURA markup, built by tools/build_lyrics_mv.py); scenes address
 * lines by index. Without the files the film still renders, with placeholder glyphs and no JIZURA layer.
 *
 * Contract with engine/core/main.js: Z.setup(audio) fills Z.SHOTS and window.__zankoMeta.duration; every frame is a
 * pure function of song time.
 */
(() => {
  'use strict';
  const Z = window.Z, D = Z.draw, E = Z.ease;
  const W = 1920, H = 1080;

  // ------------------------------------------------------------------ film identity
  Z.TITLE = '花骨朵';
  Z.TITLE_SUB = 'HUAGUDUO';
  Z.ARTIST = '洛天依';
  Z.CREDIT = 'Vocal：洛天依 · Fan-made MV';

  Z.setup = async (audio) => {
    const G = Z.HGD, C = G.C;
    await G.loadLyrics();
    const { B, nb } = G.grid(audio);
    const CUT = audio.music_cut;                           // 160.19: the music stops dead -> hard cut to the end card
    const END = CUT + 7.4;                                 // silent end card (render_final pads the audio)

    // ================================================================ sections -> looks (paper daylight by default)
    const secs = audio.sections || [];
    const LOOK_BY_SECTION = ['intro', 'refrain1', 'verse', 'b1', 'b2', 'refrain2', 'b3', 'b4', 'refrain3', 'outro', 'tail'];
    secs.forEach((s, i) => { s.look = LOOK_BY_SECTION[i] || 'tail'; });
    Z.sectionAt = t => { let s = secs[0] || null; for (const x of secs) if (x.start <= t + 1e-6) s = x; return s; };
    // bloom keys on max(R,G,B): on paper the threshold stays high or every white pixel blooms (02 §13)
    Z.LOOK_DEFAULT = { boil: 0.85, boilFps: 12, bloom: 0.12, bloomThreshold: 0.93, grain: 0.05, vignette: 0.12, lutMix: 0 };
    Z.LOOKS = {
      intro: { boil: 0.75 },
      refrain1: { boil: 0.9, beatCA: 0.8 },
      verse: { boil: 0.7, grain: 0.06, lutA: 'P2', lutMix: 0.06 },
      b1: { boil: 0.9, beatCA: 0.6 },
      b2: { boil: 1.0, beatCA: 0.9 },
      refrain2: { boil: 1.1, bloom: 0.34, bloomThreshold: 0.72, beatBloom: 0.12, beatCA: 2.2, vignette: 0.26, lutA: 'P3', lutMix: 0.05 },
      b3: { boil: 0.6, grain: 0.07, vignette: 0.2 },
      b4: { boil: 0.8, beatCA: 1.0, lutA: 'P4', lutMix: 0.05 },
      refrain3: { boil: 1.0, bloom: 0.16, bloomThreshold: 0.9, beatCA: 1.6 },
      outro: { boil: 1.15, bloom: 0.28, bloomThreshold: 0.8, beatBloom: 0.1, beatCA: 2.6, vignette: 0.2 },
      tail: { boil: 0.5, grain: 0.05, vignette: 0.14 },
    };

    // ================================================================ global punctuation: section hits + kick shake
    // one place owns full-frame flashes (<= 3 per second; colour flashes on paper, never white on white)
    const FLASH = [
      [B(9), 0.20, [0.78, 0.09, 0.24]],                    // 15.89 refrain 1: a carmine pulse on blush paper
      [B(25), 0.24, [0.70, 0.07, 0.18]],                   // 48.09 B1 thickens: lantern red
      [B(33), 0.42, [1, 1, 1]],                            // 64.07 B2: 死 on green
      [B(41), 0.42, [1, 0.24, 0.43]],                      // 80.09 refrain 2: rouge neon on indigo
      [B(65), 0.45, [1, 0.95, 0.78]],                      // 127.87 refrain 3: warm light on green snow
      [B(73), 0.55, [1, 1, 1]],                            // 143.59 outro: white on carmine
    ];
    const SHAKE = [[B(41), B(49), 4], [B(65), B(73), 4], [B(73), CUT, 6]];
    Z.globalFX = (P, t) => {
      for (const [ft, a, col] of FLASH) {
        const d = t - ft;
        if (d >= 0 && d < 0.4) { const k = a * Math.exp(-d * 10); if (k > (P.flash || 0)) { P.flash = k; P.flashColor = col; } }
      }
      for (const [t0, t1, amp] of SHAKE) {
        if (t < t0 || t >= t1) continue;
        const q = Math.floor(t * 12), a = amp * Math.pow(Z.env.low(t), 3);
        P.shake = [(P.shake ? P.shake[0] : 0) + Z.rnds(q, 91) * a, (P.shake ? P.shake[1] : 0) + Z.rnds(q, 92) * a];
      }
    };

    // ================================================================ JIZURA lyric layer (9 narrative lines)
    let lrc = '';
    try { const r = await fetch(Z.ROOT + 'analysis/lyrics_mv.lrc'); if (r.ok) lrc = await r.text(); } catch (e) { /* no lyrics yet */ }
    lrc = lrc.replace(/^﻿/, '').replace(/^\[ti:.*\]\s*$/m, '');
    if (lrc.trim() && window.J) {
      JZ.setAudio({ duration: audio.duration, beats: audio.beats, energy: null, energyRate: 0 });
      // Curation (references/06 §5): the 残光-tested deny-lists (novelty objects, UI gimmicks, horror, opaque plates,
      // kinetic cards, full-frame fx owned by our post pass) + this film's extras. Any change re-rolls the cuts.
      const DENY = {
        layout: 'scatter ring wave labels pill knSeesaw knGearWords knTumble knPadGrid knPathRide zigzag arcTop gridCells bubble ticker searchBar chat notification ticket hanging wordCloud bounceLine elastic stickerBomb keycaps bubbles slotMachine flipBoard dotMatrix equalizer tape contents numbered poster ema ransom newspaper vinyl cassette bookSpine stampSheet calendar chochin routeMap stationSign noren tanzaku omikuji kakejiku shoji clapper warningLabel priceTag nameTag stickyNotes karuta cube flipCards accordion pile blocks balloons magnets tiles bulbs ledScroll billboard crowdBubbles crossword wordSearch puzzle dominoes burst fisheye origami zipper mosaicTiles stencil tyIndexTable tyStatCount typeSpecimen dictionary proofread magazine headlineDeck footnote ribbon flag pendulum knCollide knSlamStack halftoneBig tySquare tyRotBlock subtitleBar tile kaleido polaroid postcard letterPaper genkou panels splitScreen splitHalves wall cylinder shadowPlay glitchGrid',
        fx: 'panelWipe irisTrans doors blindsTrans splitSlide gridRepeat whiteFrame blackFrame strobe colorBars mirrorFlash starGlint focusLines speedLines halftone duotone kaleido bulge squash snapshot loopScroll crtOff tvStatic zoomStutter negativeRing edgeDetect hueShift posterize ditherBit rotateSnap invert bandInvert flash bloomFlash',
        decor: 'dots arrows shapes qrBlock triangleSpin checkerStrip confetti petals heartsStars kamon seigaiha asanoha hanabi chochin shimenawa sensu momiji namiGashira memphis zigzagRibbon polkaPatch stripeCircle starburst cursorClick windowChrome progressBar toggleSwitch notifBell likeCounter mediaControls volumeBars musicNotes bubbles dandelion vines cloudPuffs tapePieces highlightMark staple paperClip indexTabs punchHoles swatches spinner tally bracketsJP loopArrows halfCircles decoCorners tyColophon dateStamp tyTypeScale tyTextRule dataColumns timecodeBar rainStreaks',
        cam: 'knCardFlip jelly bounce knJumpCut knTiltKick knReadPan knShearKick knRushIn',
        treat: 'boxed marker knWordPlate circled sticker splitColor rainbow chrome',
        enter: 'bubbles stickerPeel crumple loadingBar tokoroten',
        exit: 'balloonOff crumpleOut peelOff',
        bg: 'argyle tartan chevron houndstooth herringbone polka checker retroGrid eqBars kaleidoscope fireworks sunburst bigStripes isoCubes seigaiha asanoha tvBars splitDiag spiralArms squareTunnel moire',
        trans: 'knCornerSwing knStripSlam checker cubeTurn spinOut doorsOpen pixelate knStutterCut',
      };
      const enabled = {};
      for (const g of J.GROUP_KEYS) {
        enabled[g] = {}; const deny = new Set((DENY[g] || '').split(/\s+/).filter(Boolean));
        for (const k of J.order(g)) {
          const d = J.registry(g)[k] || {};
          enabled[g][k] = k === 'none' || (!deny.has(k) && !/^hr[A-Z]/.test(k) && d.set !== 'horror');
        }
      }
      const common = {
        enabled, lyrics: lrc, fps: 30, res: 1080, aspect: '16:9', seed: 507, unify: true, typeset: true, extra: true, wa: false, horror: false,
        fx: { motion: 0.65, glitch: 0.3, chroma: 0.45, decor: 0.35, density: 0.5, texture: 0.5, flash: false, koma: 12, hud: 'off', bgSwitch: 0.3 },
      };
      // light text schemes on paper (02 §13): our own ink / carmine through colors.enabled; crimson for the night and the climax
      const INK = { enabled: true, bg: '#F4EEE4', fg: '#1B1420', sub: '#5E5560', accentOn: true, accent: '#C8183C', ghostA: '#C8183C', ghostB: '#8D8489' };
      const WINTER = { enabled: true, bg: '#E6ECF2', fg: '#2B3446', sub: '#6F7E93', accentOn: true, accent: '#C8183C', ghostA: '#6F7E93', ghostB: '#A9BDD1' };
      const NIGHT = { accentOn: true, accent: '#FFFFFF', ghostA: '#FF3D6E', ghostB: '#7A5CFF' };
      const plan = (name, o) => JZ.addPlan(name, Object.assign({}, common, o));
      await plan('paper', { style: 'paper', schemes: [0], colors: INK });
      await plan('paperCF', { style: 'paper', schemes: [0], colors: INK, centerFree: true });
      await plan('winter', { style: 'paper', schemes: [0], colors: WINTER });
      await plan('winterCF', { style: 'paper', schemes: [0], colors: WINTER, centerFree: true });
      await plan('spec', { style: 'specimen', schemes: [1], colors: { accentOn: true, accent: '#A4505A', ghostA: '#B9B4AD', ghostB: '#A4505A' } });
      await plan('night', { style: 'crimson', schemes: [2], colors: NIGHT });
      await plan('nightCF', { style: 'crimson', schemes: [2], colors: NIGHT, centerFree: true });
      await plan('climax', { style: 'crimson', schemes: [0], seed: 508, colors: { accentOn: true, accent: '#1B1420', ghostA: '#FFFFFF', ghostB: '#1B1420' },
        fx: Object.assign({}, common.fx, { motion: 0.85, chroma: 0.7 }) });
    }
    // faces used outside the scenes' own init (HUD)
    await Promise.all(['400 17px "DotGothic16"', '500 18px "Noto Sans SC"', '700 18px "Noto Serif SC"'].map(f => document.fonts.load(f, Z.TITLE + Z.TITLE_SUB + '标本引晚春去冬一座房春天里胭脂夜皮囊惊蛰霜降六月雪绽0123456789No.:/♩=·—')));

    // ================================================================ shots (docs/STORYBOARD.md)
    // shot(id, t0, t1, scene, args, extra) -- extra = { lyric, plan, post, trans, text, hud, dark }
    // lyric defaults to 'none' (the scene draws its own typography); JIZURA shots pass lyric 'front' + a plan.
    const S = [];
    const shot = (id, t0, t1, scene, args, extra = {}) => { if (t1 > t0 + 1e-3) S.push(Object.assign({ id, t0, t1, scene, args, lyric: 'none' }, extra)); };
    const JZF = plan => ({ lyric: 'front', plan });

    // ---- INTRO (bars 1-8): the herbarium sheet waits; two stops = the seal and the title in silence
    shot('s01', 0, 11.00, 'hPage', { mode: 'intro' }, { hud: false, post: { boil: 0.6 } });
    shot('s02', 11.00, 14.85, 'hPage', { mode: 'stamp' }, { hud: false, post: { boil: 0.6 } });
    shot('s03', 14.85, B(9), 'hType', { mode: 'title' }, { hud: false, post: { boil: 0.3, grain: 0.06 } });

    // ---- REFRAIN 1 (bars 9-16): the question, bewildered -- late spring
    shot('s04', B(9), B(10), 'hForget', { mode: 'paper', line: 0 }, {});
    shot('s05', B(10), nb(22.6), 'hCross', { mode: 'day' }, JZF('paper'));
    shot('s06', nb(22.6), B(14), 'hInsect', { mode: 'crush', line: 2 }, {});
    shot('s07', B(14), B(16), 'hBud', { mode: 'refrain', line: 3 }, { trans: { type: 'budIris', dur: 0.45, cx: 960, cy: 560 } });
    shot('s08', B(16), B(18), 'hWinter', { mode: 'frost' }, Object.assign(JZF('winter'), { trans: { type: 'xfade', dur: 0.4 } }));

    // ---- VERSE (bars 17-24): last winter
    shot('s09', B(18), B(20), 'hWinter', { mode: 'sun', line: 5 }, {});
    shot('s10', B(20), B(22), 'hWinter', { mode: 'lane', line: 6 }, { trans: { type: 'push', dur: 0.35, dx: -1 } });
    shot('s11', B(22), 46.40, 'hWinter', { mode: 'branch' }, JZF('winterCF'));
    shot('s12', 46.40, B(25), 'hType', { mode: 'want', line: 8 }, { dark: true });

    // ---- B1 (bars 25-32): "I want a house" -> a box, a shroud, rouge, a veil over nobody
    shot('s13', B(25), nb(50.6), 'hHouse', { mode: 'house', line: 9 }, {});
    shot('s14', nb(50.6), B(28), 'hHouse', { mode: 'box', line: 10 }, {});
    shot('s15', B(28), nb(56.56), 'hHouse', { mode: 'wrap', line: 11 }, {});
    shot('s16', nb(56.56), B(30), 'hHouse', { mode: 'rouge', line: 12 }, { dark: true });
    shot('s17', B(30), B(32), 'hHouse', { mode: 'veil', line: 13 }, { dark: true, trans: { type: 'wipe', dur: 0.3, angle: -0.35, color: '#C9A04E' } });
    shot('s18', B(32), B(33), 'hType', { mode: 'want2', line: 14 }, {});

    // ---- B2 (bars 33-40): "I want to die in spring"
    shot('s19', B(33), B(34), 'hSlam', { mode: 'death', line: 15 }, { hud: false });
    shot('s20', B(34), B(36), 'hSpring', { mode: 'bed' }, JZF('paperCF'));
    shot('s21', B(36), B(38), 'hSpring', { mode: 'grow', line: 17 }, {});
    shot('s22', B(38), nb(79.6), 'hSilverfish', { line: 18 }, {});

    // ---- REFRAIN 2 (bars 41-48): the question, accusing -- rouge night
    shot('s23', nb(79.6), nb(81.56), 'hForget', { mode: 'neon', line: 19 }, { dark: true });
    shot('s24', nb(81.56), nb(86.87), 'hCross', { mode: 'night' }, Object.assign(JZF('night'), { dark: true }));
    shot('s25', nb(86.87), nb(90.37), 'hInsect', { mode: 'press', line: 21 }, { dark: true });
    shot('s26', nb(90.37), B(48), 'hBud', { mode: 'night', line: 22 }, Object.assign(JZF('nightCF'), { dark: true }));
    shot('s27', B(48), B(49), 'hType', { mode: 'dont', line: 23 }, { dark: true, trans: { type: 'black', dur: 0.25 } });

    // ---- B3 (bars 49-56): "don't forget me" -- old photo, glassine skin, one bed two dreams
    shot('s28', B(49), nb(98.6), 'hPage', { mode: 'photo', line: 24 }, { trans: { type: 'xfade', dur: 0.4 } });
    shot('s29', nb(98.6), nb(102.57), 'hPage', { mode: 'glassine' }, JZF('spec'));
    shot('s30', nb(102.57), nb(106.57), 'hBed', { mode: 'bed', line: 26 }, { trans: { type: 'xfade', dur: 0.35 } });
    shot('s31', nb(106.57), nb(110.57), 'hBed', { mode: 'dream', line: 27 }, {});
    shot('s32', nb(110.57), B(57), 'hType', { mode: 'dont2', line: 28 }, {});

    // ---- B4 (bars 57-64): time as stamps, the bud as a factory part, the child's handwriting dissolves
    shot('s33', B(57), nb(114.6), 'hOffice', { mode: 'grid', line: 29 }, {});
    shot('s34', nb(114.6), nb(118.58), 'hOffice', { mode: 'seals', line: 30 }, {});
    shot('s35', nb(118.58), B(62), 'hOffice', { mode: 'conveyor', line: 31 }, {});
    shot('s36', B(62), 127.58, 'hYouth', { line: 32 }, {});

    // ---- REFRAIN 3 (bars 65-72): the question, final -- June snow; the bud lifts its head and tears free
    shot('s37', 127.58, B(66), 'hForget', { mode: 'snow', line: 33 }, {});
    shot('s38', B(66), nb(134.56), 'hCross', { mode: 'snow' }, JZF('paper'));
    shot('s39', nb(134.56), nb(138.09), 'hInsect', { mode: 'release', line: 35 }, {});
    shot('s40', nb(138.09), B(72), 'hBud', { mode: 'lift', line: 36 }, {});
    shot('s41', B(72), B(73), 'hBud', { mode: 'crack', line: 36 }, { hud: false });

    // ---- OUTRO (bars 73-80): refusal -> the bloom; the music stops dead at CUT
    shot('s42', B(73), nb(146.07), 'hSlam', { mode: 'refuse', line: 37 }, { hud: false, dark: true });
    shot('s43', nb(146.07), nb(150.58), 'hTunnel', { pages: [['s09', 37.0], ['s13', 50.0], ['s20', 68.0], ['s34', 117.5], ['s28', 97.5]] }, Object.assign(JZF('climax'), { dark: true }));
    shot('s44', nb(150.58), B(78) - 0.0, 'hWisp', { line: 39 }, { dark: true });
    shot('s45', B(78), nb(155.06), 'hBloom', { mode: 'pop', line: 40 }, { dark: true });
    shot('s46', nb(155.06), CUT, 'hBloom', { mode: 'open', line: 41 }, { hud: false });

    // ---- END CARD (silence): the same herbarium sheet, the bloom pressed and filed
    shot('s47', CUT, END, 'hPage', { mode: 'end' }, { hud: false, post: { boil: 0.4, bloom: 0.08 } });

    Z.SHOTS = S;
    window.__zankoMeta.duration = END;

    // ================================================================ HUD: the specimen catalogue in the corners
    const SEC_NAME = ['引', '晚春', '去冬', '一座房', '春天里', '胭脂夜', '皮囊', '惊蛰—霜降', '六月雪', '绽', '—'];
    const lastBar = audio.bars.length ? audio.bars[audio.bars.length - 1].index : 80;
    Z.hud = (ctx, St) => {
      const t = St.t, fade = Z.clamp((t - B(9)) / 0.6) * Z.clamp((CUT - t) / 0.2);
      if (fade <= 0) return;
      const sec = Z.sectionAt(t), si = Math.max(0, secs.indexOf(sec)), bar = Math.max(1, St.clock.bar(t) + 1);
      const dark = !!(St.shot && St.shot.dark), col = dark ? '#F4EEE4' : '#1B1420';
      const f = Math.floor(t * 30), tc = [Math.floor(t / 60) % 60, Math.floor(t) % 60, f % 30].map(n => String(n).padStart(2, '0')).join(':');
      ctx.globalAlpha = (dark ? 0.62 : 0.56) * fade; ctx.fillStyle = col; ctx.strokeStyle = col; ctx.lineWidth = 1;
      ctx.shadowColor = dark ? 'rgba(0,0,0,0.45)' : 'rgba(244,238,228,0.7)'; ctx.shadowBlur = 3; ctx.textBaseline = 'top';
      ctx.textAlign = 'left';
      G.font(ctx, 18, 'song', 700); ctx.fillText(Z.TITLE, 44, 34);
      G.font(ctx, 15, 'dot', 400); ctx.fillText(Z.TITLE_SUB, 104, 37);
      ctx.beginPath(); ctx.moveTo(44, 60); ctx.lineTo(44 + 150 + 30 * St.clock.pulse(t, 6), 60); ctx.stroke();
      G.font(ctx, 15, 'dot', 400); ctx.fillText('No.0507', 44, 68);
      G.font(ctx, 15, 'hei', 500); ctx.fillText(SEC_NAME[si] || '', 112, 67);
      ctx.textAlign = 'right'; G.font(ctx, 15, 'dot', 400);
      ctx.fillText(tc, W - 44, 36);
      ctx.fillText(`BAR ${String(bar).padStart(3, '0')} / ${String(lastBar).padStart(3, '0')}`, W - 44, 58);
      ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
      ctx.fillText('♩=' + (60 / (St.clock.spb || 0.5)).toFixed(1), 44, H - 38);
      const ib = St.clock.inBar(t);
      for (let i = 0; i < 4; i++) { const x = W - 44 - (4 - i) * 16; ctx.strokeRect(x, H - 52, 10, 10); if (i === ib) ctx.fillRect(x, H - 52, 10, 10); }
      ctx.globalAlpha = 0.3 * fade; ctx.fillRect(44, H - 30, (W - 88) * Z.clamp(t / CUT), 1);
    };

    // ================================================================ 9:16 build (engine/vertical.html): graphic shots keep the whole frame
    Z.VERTICAL_CFG = {
      full: ['s01', 's02', 's03', 's09', 's16', 's19', 's34', 's36', 's41', 's42', 's46', 's47'],
      planMap: { paper: 'v_paper', paperCF: 'v_paper', winter: 'v_winter', winterCF: 'v_winter', spec: 'v_spec', night: 'v_night', nightCF: 'v_night', climax: 'v_climax' },
      title: Z.TITLE, sub: Z.TITLE_SUB, artist: Z.ARTIST, credits: [B(9), CUT],
      schemes: 'light', ambience: [238, 232, 222],
    };
  };
})();
