/* JIZURA style probe for 花骨朵: the film's plans over the paper / winter / night / carmine grounds they will sit on. */
(() => { const Z = window.Z, G = Z.HGD, C = G.C;
  Z.scene('hJzBg', { init: async () => { await G.ready(); }, draw(ctx, S) {
    const a = S.args; G.drawPaper(ctx, a.paper || 'xuan');
    if (a.wash) { ctx.save(); ctx.globalCompositeOperation = a.comp || 'multiply'; ctx.fillStyle = a.wash; ctx.fillRect(0, 0, 1920, 1080); ctx.restore(); }
    if (a.snow) G.snow(ctx, S.t, { n: 140, size: 4 });
    if (a.bud) G.bud(ctx, { x: 960, y: 1180, len: 700, size: 170, nod: 0.8, open: a.open || 0.1, pal: a.bud, t: S.t, sway: 0.05 * Math.sin(S.t) });
  } });
  Z.setup = async (audio) => {
    await G.loadLyrics(); const { B, nb } = G.grid(audio);
    Z.LOOK_DEFAULT = { boil: 0.8, bloom: 0.15, bloomThreshold: 0.93, grain: 0.05, vignette: 0.12, lutMix: 0 };
    let lrc = ''; try { const r = await fetch(Z.ROOT + 'analysis/lyrics_mv.lrc'); if (r.ok) lrc = await r.text(); } catch (e) {}
    JZ.setAudio({ duration: audio.duration, beats: audio.beats, energy: null, energyRate: 0 });
    const DENY = {
      layout: 'scatter ring wave labels pill knSeesaw knGearWords knTumble knPadGrid knPathRide zigzag arcTop gridCells bubble ticker searchBar chat notification ticket hanging wordCloud bounceLine elastic stickerBomb keycaps bubbles slotMachine flipBoard dotMatrix equalizer tape contents numbered poster ema ransom newspaper vinyl cassette bookSpine stampSheet calendar chochin routeMap stationSign noren tanzaku omikuji kakejiku shoji clapper warningLabel priceTag nameTag stickyNotes karuta cube flipCards accordion pile blocks balloons magnets tiles bulbs ledScroll billboard crowdBubbles crossword wordSearch puzzle dominoes burst fisheye origami zipper mosaicTiles stencil tyIndexTable tyStatCount typeSpecimen dictionary proofread magazine headlineDeck footnote ribbon flag pendulum knCollide knSlamStack halftoneBig tySquare tyRotBlock subtitleBar tile kaleido polaroid postcard letterPaper genkou panels splitScreen splitHalves wall cylinder cube shadowPlay glitchGrid',
      fx: 'panelWipe irisTrans doors blindsTrans splitSlide gridRepeat whiteFrame blackFrame strobe colorBars mirrorFlash starGlint focusLines speedLines halftone duotone kaleido bulge squash snapshot loopScroll crtOff tvStatic zoomStutter negativeRing edgeDetect hueShift posterize ditherBit rotateSnap invert bandInvert flash bloomFlash',
      decor: 'dots arrows shapes qrBlock triangleSpin checkerStrip confetti petals heartsStars kamon seigaiha asanoha hanabi chochin shimenawa sensu momiji namiGashira memphis zigzagRibbon polkaPatch stripeCircle starburst cursorClick windowChrome progressBar toggleSwitch notifBell likeCounter mediaControls volumeBars musicNotes bubbles dandelion vines cloudPuffs tapePieces highlightMark staple paperClip indexTabs punchHoles swatches spinner tally qrBlock bracketsJP loopArrows halfCircles decoCorners tyColophon dateStamp tyTypeScale tyTextRule dataColumns timecodeBar rainStreaks',
      cam: 'knCardFlip jelly bounce knJumpCut knTiltKick knReadPan knShearKick knRushIn',
      treat: 'boxed marker knWordPlate circled sticker splitColor rainbow chrome',
      enter: 'bubbles stickerPeel crumple loadingBar tokoroten', exit: 'balloonOff crumpleOut peelOff',
      bg: 'argyle tartan chevron houndstooth herringbone polka checker retroGrid eqBars kaleidoscope fireworks sunburst bigStripes isoCubes seigaiha asanoha tvBars splitDiag spiralArms squareTunnel moire',
      trans: 'knCornerSwing knStripSlam checker cubeTurn spinOut doorsOpen pixelate knStutterCut',
    };
    const enabled = {};
    for (const g of J.GROUP_KEYS) { enabled[g] = {}; const deny = new Set((DENY[g] || '').split(/\s+/).filter(Boolean));
      for (const k of J.order(g)) { const d = J.registry(g)[k] || {}; enabled[g][k] = k === 'none' || (!deny.has(k) && !/^hr[A-Z]/.test(k) && d.set !== 'horror'); } }
    const common = { enabled, lyrics: lrc, fps: 30, res: 1080, aspect: '16:9', seed: 507, unify: true, typeset: true, extra: true, wa: false, horror: false,
      fx: { motion: 0.65, glitch: 0.3, chroma: 0.45, decor: 0.35, density: 0.5, texture: 0.5, flash: false, koma: 12, hud: 'off', bgSwitch: 0.3 } };
    const ink = { enabled: true, bg: '#F4EEE4', fg: '#1B1420', sub: '#5E5560', accentOn: true, accent: '#C8183C', ghostA: '#C8183C', ghostB: '#8D8489' };
    const winter = { enabled: true, bg: '#E6ECF2', fg: '#2B3446', sub: '#6F7E93', accentOn: true, accent: '#C8183C', ghostA: '#6F7E93', ghostB: '#A9BDD1' };
    const P = (name, o) => JZ.addPlan(name, Object.assign({}, common, o));
    await P('paper', { style: 'paper', schemes: [0], colors: ink });
    await P('paperCF', { style: 'paper', schemes: [0], colors: ink, centerFree: true });
    await P('winter', { style: 'paper', schemes: [0], colors: winter });
    await P('winterCF', { style: 'paper', schemes: [0], colors: winter, centerFree: true });
    await P('spec', { style: 'specimen', schemes: [1], colors: { accentOn: true, accent: '#A4505A', ghostA: '#B9B4AD', ghostB: '#A4505A' } });
    await P('night', { style: 'crimson', schemes: [2], colors: { accentOn: true, accent: '#FFFFFF', ghostA: '#FF3D6E', ghostB: '#7A5CFF' } });
    await P('nightCF', { style: 'crimson', schemes: [2], colors: { accentOn: true, accent: '#FFFFFF', ghostA: '#FF3D6E', ghostB: '#7A5CFF' }, centerFree: true });
    await P('climax', { style: 'crimson', schemes: [0], seed: 508, colors: { accentOn: true, accent: '#1B1420', ghostA: '#FFFFFF', ghostB: '#1B1420' }, fx: Object.assign({}, common.fx, { motion: 0.85, chroma: 0.7 }) });
    const S = [], shot = (id, t0, t1, args, plan) => S.push({ id, t0, t1, scene: 'hJzBg', args, plan, lyric: 'front' });
    shot('a', 17.89, 22.56, { paper: 'blush' }, 'paper');
    shot('b', 30.03, 34.10, { paper: 'snow', snow: true }, 'winter');
    shot('c', 42.08, 46.40, { paper: 'snow', bud: 'snow' }, 'winterCF');
    shot('d', 66.10, 70.09, { paper: 'green', wash: '#7FAF66' }, 'paperCF');
    shot('e', 81.56, 86.87, { paper: 'night' }, 'night');
    shot('f', 90.37, 94.04, { paper: 'night', bud: 'night', open: 0.45 }, 'nightCF');
    shot('g', 98.59, 102.57, { paper: 'xuan' }, 'spec');
    shot('h', 129.84, 134.56, { paper: 'green', wash: '#4F8F45', snow: true }, 'paper');
    shot('i', 146.07, 150.58, { paper: 'red', wash: '#B0102E' }, 'climax');
    Z.SHOTS = S; window.__zankoMeta.duration = 150.58;
  }; })();
