(() => { const Z = window.Z, G = Z.HGD, C = G.C;
  Z.scene('hKitTest', { init: async () => { await G.ready(); }, draw(ctx, S) {
    const t = S.t, mode = S.args.mode;
    G.drawPaper(ctx, S.args.paper || 'xuan');
    if (mode === 'buds') {
      const states = [[0.95, 0, 'print'], [0.85, 0.15, 'plate'], [0.6, 0.45, 'plate'], [0.2, 0.85, 'plate'], [0.9, 0, 'snow'], [0.7, 0.3, 'dead']];
      states.forEach(([nod, open, pal], i) => G.bud(ctx, { x: 180 + i * 300, y: 1000, len: 560, size: 120, nod, open, pal, t, sway: 0.05 * Math.sin(t + i), crack: i === 3 ? 0.8 : 0, wither: pal === 'dead' ? 0.7 : 0 }));
      G.label(ctx, 1300, 60, [['科', '罂粟科 Papaveraceae'], ['种', '虞美人 Papaver rhoeas'], ['状态', '花骨朵（未开）', C.carmine], ['采集', '晚春']], { no: 'No.0507', k: 1, w: 560 });
      G.seal(ctx, 1700, 420, 140, '待开', { k: 1 }); G.seal(ctx, 1520, 420, 110, '花', { k: 1, style: 'yang', seed: 5 });
      G.sheetMarks(ctx, {});
    } else if (mode === 'poppy') {
      G.poppy(ctx, { x: 520, y: 540, r: 360, open: 1, t, seed: 2 });
      G.poppy(ctx, { x: 1180, y: 380, r: 200, open: 0.35, t, seed: 3 });
      G.poppy(ctx, { x: 1600, y: 700, r: 260, open: 1, t, pal: 'pressed', seed: 4 });
      G.cochineal(ctx, 1150, 850, 120, { t, rot: 0.3 }); G.cochineal(ctx, 1400, 900, 120, { t, crush: 0.7, rot: -0.2 });
      G.silverfish(ctx, 900, 980, -0.3, 160, t, 1); G.silverfish(ctx, 1750, 200, 2.4, 120, t, 2);
    } else if (mode === 'type') {
      G.text(ctx, G.L(3), 960, 300, { size: 110, fam: 'song', weight: 900, color: C.ink, misreg: [4, 3], under: C.carmine });
      G.text(ctx, G.L(12), 960, 560, { size: 220, fam: 'brush', weight: 400, color: C.carmine });
      G.text(ctx, G.L(5), 300, 540, { size: 80, fam: 'xw', weight: 400, color: C.ink, vertical: true });
      G.text(ctx, G.L(32), 960, 820, { size: 120, fam: 'hand', weight: 400, color: C.ink });
      G.text(ctx, G.L(31), 960, 980, { size: 70, fam: 'heavy', weight: 400, color: C.ink });
      G.text(ctx, G.L(41), 1650, 540, { size: 70, fam: 'cursive', weight: 400, color: C.ink, vertical: true });
      G.brush(ctx, G.smooth([[200, 200], [700, 160], [1200, 260], [1700, 180]]), { w: 120, color: C.carmine, dry: 0.6, seed: 3, prog: 1 });
      G.splat(ctx, 1500, 700, 90, { prog: 1, seed: 8 }); G.bleed(ctx, 400, 850, 140, { prog: 1 });
    } else if (mode === 'frost') {
      G.drawPaper(ctx, 'snow'); G.drawPaper(ctx,'snow'); ctx.fillStyle='rgba(60,80,110,0.25)'; ctx.fillRect(0,0,1920,1080); G.frost(ctx, 0.8, {}); G.snow(ctx, t, { color: '#FFFFFF', n: 200, size: 4 });
      G.bud(ctx, { x: 960, y: 1100, len: 700, size: 130, nod: 0.95, open: 0.05, pal: 'snow', t });
    }
  } });
  Z.setup = async () => {
    const r = await fetch(Z.ROOT + 'analysis/lyrics_source.lrc'); const lrc = r.ok ? await r.text() : '';
    Z.LYR = lrc.split(/\r?\n/).map(l => l.match(/^\[(\d+):(\d+(?:\.\d+)?)\](.*)$/)).filter(Boolean).map(m => ({ t: +m[1] * 60 + +m[2], text: m[3].trim() }));
    try { Z.CT = await (await fetch(Z.ROOT + 'analysis/char_timing.json')).json(); } catch (e) { Z.CT = []; }
    Z.LOOK_DEFAULT = { boil: 1.0, bloom: 0.15, bloomThreshold: 0.93, grain: 0.04, vignette: 0.1, lutMix: 0 };
    Z.SHOTS = ['buds', 'poppy', 'type', 'frost'].map((m, i) => ({ id: 'k' + i, t0: i * 2, t1: i * 2 + 2, scene: 'hKitTest', args: { mode: m }, lyric: 'none' }));
    window.__zankoMeta.duration = 8; }; })();
