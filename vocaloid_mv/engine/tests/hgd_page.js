(() => { const Z = window.Z, G = Z.HGD;
  Z.TITLE = '花骨朵'; Z.TITLE_SUB = 'HUAGUDUO'; Z.ARTIST = '洛天依'; Z.CREDIT = 'Vocal：洛天依 · Fan-made MV';
  Z.setup = async (audio) => {
    await G.loadLyrics(); const { B, nb } = G.grid(audio);
    Z.LOOK_DEFAULT = { boil: 0.7, bloom: 0.12, bloomThreshold: 0.93, grain: 0.05, vignette: 0.12, lutMix: 0 };
    const S = [], shot = (id, t0, t1, scene, args, extra = {}) => S.push(Object.assign({ id, t0, t1, scene, args, lyric: 'none' }, extra));
    shot('s01', 0, 11.00, 'hPage', { mode: 'intro' });
    shot('s02', 11.00, 14.85, 'hPage', { mode: 'stamp' });
    shot('s03', 14.85, B(9), 'hType', { mode: 'title' }, { post: { boil: 0.3 } });
    shot('s12', 46.40, B(25), 'hType', { mode: 'want', line: 8 });
    shot('s18', B(32), B(33), 'hType', { mode: 'want2', line: 14 });
    shot('s27', B(48), B(49), 'hType', { mode: 'dont', line: 23 });
    shot('s28', B(49), nb(98.6), 'hPage', { mode: 'photo', line: 24 });
    shot('s29', nb(98.6), nb(102.57), 'hPage', { mode: 'glassine' });
    shot('s32', nb(110.57), B(57), 'hType', { mode: 'dont2', line: 28 });
    shot('s47', 160.19, 167.59, 'hPage', { mode: 'end' }, { post: { boil: 0.4 } });
    Z.SHOTS = S; window.__zankoMeta.duration = 167.59;
  }; })();
