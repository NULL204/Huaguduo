/* engine/scenes/hgd_core.js — 花骨朵 (HUAGUDUO) shared art kit, used by every hgd_*.js scene.
 *
 * The film has no drawn singer: the protagonist is the poppy bud itself (花骨朵), printed in two inks — sumi ink and
 * carmine — on rice paper, with one seasonal tint per section. Everything here is a pure function of its arguments;
 * caches hold immutable art only (paper sheets, seal stamps, glyph masks, frost / crack geometry).
 *
 *   Z.HGD.C              palette (ink, carmine, paper + seasonal sets)
 *   Z.HGD.font(ctx, px, fam, weight)      Chinese faces: song hei brush xw heavy cursive hand wild dot
 *   Z.HGD.ready()        await in scene init: every face loaded (frame 0 never falls back)
 *   Z.HGD.L(i) / LT(i) / LE(i) / CT(i)   lyric line i (from the user's LRC at runtime) / start / end / char onsets
 *   Z.HGD.paper(kind)    cached 1920x1080 sheet: xuan snow aged office red night green ink
 *   Z.HGD.vstroke / brush / splat / bleed   ink marks
 *   Z.HGD.text(ctx, str, x, y, o)          per-glyph typography (horizontal / vertical, reveal per glyph)
 *   Z.HGD.bud(ctx, o) / poppy(ctx, o)      the protagonist: nodding bud on a hairy stem / the open flower
 *   Z.HGD.cochineal / silverfish / seal / label / petals / snow / frost
 *   transitions: tear, budIris, bleed, stamp
 */
(() => {
  'use strict';
  const Z = window.Z, D = Z.draw, E = Z.ease;
  const W = 1920, H = 1080, TAU = Math.PI * 2;
  const G = (Z.HGD = {});

  // ================================================================== palette
  G.C = {
    paper: '#F4EEE4', paper2: '#EDE3D3', ink: '#1B1420', ink2: '#3B3039', grey: '#8D8489', mist: '#C9C2C0',
    carmine: '#C8183C', deep: '#8E1028', rouge: '#E85A74', pink: '#F2B8C0', blush: '#F7D9DA',
    sepal: '#8DB07A', sepalD: '#5C8656', stem: '#7FA46E', gold: '#C9A04E',
    winter: { snow: '#E6ECF2', frost: '#D5E0EA', slate: '#6F7E93', deep: '#2B3446', ice: '#A9BDD1', night: '#1A2130' },
    spring: { grass: '#5E9A4E', young: '#B9D27A', mud: '#3B2A22', poppy: '#D7263D', sky: '#E4EFD8' },
    night: { indigo: '#141433', deep: '#0A0A1E', neon: '#FF3D6E', violet: '#3A2366', haze: '#2A1F4A' },
    sepia: { paper: '#E3D3B8', s: '#CBB79A', dusk: '#6D6470', red: '#A4505A', brown: '#5A4636' },
    office: { white: '#EEF2F2', cyan: '#A9BCC4', steel: '#5D6B73', alarm: '#E0243C', line: '#C9D4D8' },
    june: { green: '#4F8F45', deep: '#2E5A2B', light: '#FFF3C8', sky: '#CFE3EA' },
    bloom: { field: '#B0102E', hot: '#E8203F', pink: '#FF6B88', black: '#1A0810' },
  };
  const C = G.C;

  // ================================================================== fonts (Chinese faces; engine/fonts/fonts.css)
  const FAM = {
    song: '"Noto Serif SC"', hei: '"Noto Sans SC"', brush: '"Ma Shan Zheng"', xw: '"ZCOOL XiaoWei"', heavy: '"ZCOOL QingKe HuangYou"',
    cursive: '"Zhi Mang Xing"', hand: '"Long Cang"', wild: '"Liu Jian Mao Cao"', kuaile: '"ZCOOL KuaiLe"', dot: '"DotGothic16"',
  };
  G.FAM = FAM;
  G.font = (ctx, px, fam = 'song', weight = 700) => {
    ctx.font = `${weight} ${px}px ${FAM[fam] || fam}, "Noto Serif SC", "Noto Sans SC", serif`;
  };
  let readyP = null;
  G.ready = () => readyP || (readyP = (async () => {
    const txt = (Z.LYR || []).map(l => l.text).join('') + '花骨朵虞美人罂粟科标本采集号状态未开已开晚春去冬春泥胭脂虫衣鱼惊蛰春分清明谷雨立夏小满芒种夏至小暑大暑立秋处暑白露秋分寒露霜降待开无人问津合格已阅工作狂少年郎日不升房死皮囊0123456789No.ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz·：:/—';
    const faces = ['300', '500', '700', '900'].map(w => `${w} 64px "Noto Serif SC"`).concat(['400', '500', '700', '900'].map(w => `${w} 64px "Noto Sans SC"`),
      ['400 64px "Ma Shan Zheng"', '400 64px "ZCOOL XiaoWei"', '400 64px "ZCOOL QingKe HuangYou"', '400 64px "Zhi Mang Xing"', '400 64px "Long Cang"',
        '400 64px "Liu Jian Mao Cao"', '400 64px "ZCOOL KuaiLe"', '400 64px "DotGothic16"']);
    await Promise.all(faces.map(f => document.fonts.load(f, txt).catch(() => null)));
  })());

  // ================================================================== lyrics (runtime only: Z.LYR is filled by the timeline from the user's LRC)
  G.L = i => (Z.LYR && Z.LYR[i] ? Z.LYR[i].text : '〇〇〇〇');
  G.LT = i => (Z.LYR && Z.LYR[i] ? Z.LYR[i].t : 0);
  G.LE = i => (Z.LYR && Z.LYR[i + 1] ? Math.min(Z.LYR[i + 1].t, (Z.CT && Z.CT[i] ? Z.CT[i].end + 0.6 : 1e9)) : G.LT(i) + 4);
  // onset of each visible glyph of line i (spaces skipped); falls back to an even spread over the line
  G.CT = i => {
    const txt = [...G.L(i)].filter(c => c.trim()), ct = Z.CT && Z.CT[i] ? Z.CT[i].chars : null;
    if (ct && ct.length === txt.length) return ct;
    const t0 = G.LT(i), t1 = Z.CT && Z.CT[i] ? Z.CT[i].end : t0 + txt.length * 0.3;
    return txt.map((_, k) => t0 + (t1 - t0) * k / Math.max(1, txt.length));
  };
  // load the lyric lines (the user's LRC, never committed) and per-glyph onsets; call from Z.setup (timeline or test)
  G.loadLyrics = async () => {
    let lrc = '';
    for (const f of ['analysis/lyrics_source.lrc', 'analysis/lyrics_mv.lrc']) {
      try { const r = await fetch(Z.ROOT + f); if (r.ok) { lrc = await r.text(); break; } } catch (e) { /* next */ }
    }
    Z.LYR = lrc.replace(/^\uFEFF/, '').split(/\r?\n/).map(l => l.match(/^\[(\d+):(\d+(?:\.\d+)?)\](.*)$/)).filter(Boolean)
      .map(m => ({ t: +m[1] * 60 + +m[2], text: m[3].replace(/[\/*!]/g, '').trim() })).filter(l => l.text && !/^\[/.test(l.text));
    try { const r = await fetch(Z.ROOT + 'analysis/char_timing.json'); Z.CT = r.ok ? await r.json() : []; } catch (e) { Z.CT = []; }
    if (!Z.LYR.length) console.warn('no lyrics: put the LRC at analysis/lyrics_source.lrc');
    return Z.LYR.length;
  };
  // timing helpers from analysis/audio.json: B(n) = start of bar n (bars[].index), nb(t) = nearest beat
  G.grid = (audio) => {
    const lastBar = audio.bars.length ? audio.bars[audio.bars.length - 1].index : 0;
    const B = n => { const b = audio.bars.find(x => x.index === n); return b ? b.start : n > lastBar ? audio.music_cut : 0; };
    const nb = t => audio.beats.reduce((b, x) => (Math.abs(x - t) < Math.abs(b - t) ? x : b), audio.beats[0] ?? t);
    return { B, nb };
  };
  // glyphs of line i without spaces; part(i, a, b) = a slice of them
  G.glyphs = i => [...G.L(i)].filter(c => c.trim());
  G.part = (i, a, b) => G.glyphs(i).slice(a, b).join('');

  // ================================================================== small math
  const hexRGB = h => Z.hex(h);
  G.mix = (a, b, k) => { const A = hexRGB(a), B = hexRGB(b); const m = A.map((v, i) => Math.round(v + (B[i] - v) * Z.clamp(k))); return '#' + m.map(v => v.toString(16).padStart(2, '0')).join(''); };
  G.rgba = Z.rgba;
  const bez = (x1, y1, x2, y2) => {
    const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx, cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
    const sx = u => ((ax * u + bx) * u + cx) * u, sy = u => ((ay * u + by) * u + cy) * u, dx = u => (3 * ax * u + 2 * bx) * u + cx;
    return x => { if (x <= 0) return 0; if (x >= 1) return 1; let u = x; for (let i = 0; i < 8; i++) { const e = sx(u) - x, d = dx(u); if (Math.abs(e) < 1e-5 || Math.abs(d) < 1e-6) break; u -= e / d; } return sy(Z.clamp(u)); };
  };
  G.EZ = { out: bez(0.16, 1, 0.3, 1), inn: bez(0.7, 0, 0.84, 0), io: bez(0.65, 0, 0.35, 1), soft: bez(0.33, 0, 0.2, 1) };
  G.damp = (u, amp, rate, hz) => (u < 0 ? 0 : amp * Math.exp(-u * rate) * Math.cos(u * TAU * hz));
  G.reset = x => { x.setTransform(1, 0, 0, 1, 0, 0); x.globalAlpha = 1; x.globalCompositeOperation = 'source-over'; x.filter = 'none'; x.shadowBlur = 0; x.shadowColor = 'rgba(0,0,0,0)'; };
  // 2-D value noise (deterministic) for shapes
  G.noise2 = (x, y, seed = 0) => {
    const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    const r = (a, b) => Z.rnds(a, b, seed);
    return Z.lerp(Z.lerp(r(xi, yi), r(xi + 1, yi), u), Z.lerp(r(xi, yi + 1), r(xi + 1, yi + 1), u), v);
  };
  // beats inside [t0, t1)
  G.beatsIn = (t0, t1) => (Z.clock ? Z.clock.beats.filter(b => b >= t0 - 1e-3 && b < t1 - 1e-3) : []);
  // index of the last beat <= t among `list`, -1 before
  G.lastIdx = (list, t) => { let k = -1; for (let i = 0; i < list.length; i++) if (list[i] <= t + 1e-6) k = i; return k; };

  // ================================================================== paper sheets (cached, deterministic)
  const PAPERS = {
    xuan: { base: '#F4EEE4', fib: [120, 96, 80], blot: [190, 172, 150], grain: 10, blotA: 0.16, fibA: 0.13 },
    snow: { base: '#E4EAF0', fib: [90, 110, 130], blot: [160, 175, 195], grain: 8, blotA: 0.14, fibA: 0.1 },
    aged: { base: '#E6D6BA', fib: [110, 84, 60], blot: [170, 140, 105], grain: 12, blotA: 0.24, fibA: 0.16 },
    office: { base: '#EEF2F2', fib: [120, 140, 150], blot: [200, 210, 215], grain: 5, blotA: 0.06, fibA: 0.04 },
    red: { base: '#B3122E', fib: [80, 10, 20], blot: [120, 8, 26], grain: 12, blotA: 0.22, fibA: 0.16 },
    night: { base: '#151536', fib: [60, 50, 110], blot: [12, 10, 40], grain: 9, blotA: 0.3, fibA: 0.14 },
    green: { base: '#DCE7CC', fib: [90, 120, 70], blot: [160, 185, 130], grain: 9, blotA: 0.16, fibA: 0.12 },
    ink: { base: '#1B1420', fib: [70, 60, 72], blot: [10, 6, 12], grain: 8, blotA: 0.3, fibA: 0.12 },
    blush: { base: '#F6E3E0', fib: [150, 90, 95], blot: [220, 170, 170], grain: 9, blotA: 0.14, fibA: 0.1 },
  };
  const paperCache = new Map();
  const noiseCanvas = (w, h, R) => {
    const c = Z.canvas(w, h), x = c.getContext('2d'), id = x.createImageData(w, h);
    for (let i = 0; i < w * h; i++) { const v = (R() * 255) | 0; id.data[i * 4] = v; id.data[i * 4 + 1] = v; id.data[i * 4 + 2] = v; id.data[i * 4 + 3] = 255; }
    x.putImageData(id, 0, 0); return c;
  };
  G.paper = (kind = 'xuan') => {
    let c = paperCache.get(kind); if (c) return c;
    const P = PAPERS[kind] || PAPERS.xuan, R = Z.rng(Z.hash(kind.length, kind.charCodeAt(0), 7));
    c = Z.canvas(W, H); const x = c.getContext('2d');
    x.fillStyle = P.base; x.fillRect(0, 0, W, H);
    // mottling: value noise at three scales (small random canvases scaled up with smoothing), soft-light
    x.imageSmoothingEnabled = true; x.imageSmoothingQuality = 'high';
    for (const [nw, a] of [[12, 0.5], [40, 0.35], [160, 0.22]]) {
      const nc = noiseCanvas(nw, Math.ceil(nw * H / W), R);
      x.globalCompositeOperation = 'soft-light'; x.globalAlpha = a; x.drawImage(nc, 0, 0, W, H);
    }
    x.globalAlpha = 1; x.globalCompositeOperation = 'multiply';
    for (let i = 0; i < 22; i++) {                                    // blotches (sizing, water marks)
      const bx = R() * W, by = R() * H, r = 120 + R() * 420, g = x.createRadialGradient(bx, by, 0, bx, by, r);
      g.addColorStop(0, `rgba(${P.blot[0]},${P.blot[1]},${P.blot[2]},${P.blotA * (0.4 + R() * 0.6)})`); g.addColorStop(1, `rgba(${P.blot[0]},${P.blot[1]},${P.blot[2]},0)`);
      x.fillStyle = g; x.fillRect(bx - r, by - r, 2 * r, 2 * r);
    }
    x.globalCompositeOperation = 'source-over'; x.lineCap = 'round';
    for (let i = 0; i < 2600; i++) {                                  // fibres (long + short, a few light ones)
      const fx = R() * W, fy = R() * H, a = R() * TAU, l = 6 + Math.pow(R(), 3) * 70, light = R() < 0.25;
      x.strokeStyle = light ? `rgba(255,255,255,${P.fibA * 0.9})` : `rgba(${P.fib[0]},${P.fib[1]},${P.fib[2]},${P.fibA * (0.4 + R() * 0.8)})`;
      x.lineWidth = 0.5 + R() * 0.9;
      x.beginPath(); x.moveTo(fx, fy);
      x.quadraticCurveTo(fx + Math.cos(a + 0.7) * l * 0.5, fy + Math.sin(a + 0.7) * l * 0.5, fx + Math.cos(a) * l, fy + Math.sin(a) * l); x.stroke();
    }
    // fine tooth
    const gc = noiseCanvas(W / 2, H / 2, R);
    x.globalCompositeOperation = 'overlay'; x.globalAlpha = P.grain / 100; x.drawImage(gc, 0, 0, W, H);
    G.reset(x);
    paperCache.set(kind, c); return c;
  };
  // draw a paper sheet with an optional sub-pixel offset jump (paper moves on cuts: pass a per-shot seed)
  G.drawPaper = (ctx, kind, seed = 0, alpha = 1) => {
    const p = G.paper(kind), ox = seed ? Z.rnds(seed, 3) * 60 : 0, oy = seed ? Z.rnds(seed, 5) * 40 : 0;
    ctx.save(); ctx.globalAlpha *= alpha;
    if (ox || oy) { ctx.translate(W / 2, H / 2); ctx.scale(1.07, 1.07); ctx.translate(-W / 2 + ox, -H / 2 + oy); }
    ctx.drawImage(p, 0, 0); ctx.restore();
  };

  // ================================================================== ink marks
  // Catmull-Rom densify
  G.smooth = (pts, per = 6) => {
    if (pts.length < 3) return pts.slice();
    const out = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
      for (let k = 0; k < per; k++) {
        const t = k / per, t2 = t * t, t3 = t2 * t;
        out.push([0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
          0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)]);
      }
    }
    out.push(pts[pts.length - 1]); return out;
  };
  const cumLen = pts => { const L = [0]; for (let i = 1; i < pts.length; i++) L.push(L[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])); return L; };
  // cut a polyline at fraction `prog` of its length
  G.cut = (pts, prog) => {
    if (prog >= 1) return pts; if (prog <= 0) return [pts[0]];
    const L = cumLen(pts), target = L[L.length - 1] * prog, out = [pts[0]];
    for (let i = 1; i < pts.length; i++) {
      if (L[i] >= target) { const f = (target - L[i - 1]) / Math.max(1e-6, L[i] - L[i - 1]); out.push([Z.lerp(pts[i - 1][0], pts[i][0], f), Z.lerp(pts[i - 1][1], pts[i][1], f)]); break; }
      out.push(pts[i]);
    }
    return out;
  };
  // variable-width stroke: width wf(u) with u in 0..1 along the full length; prog reveals the stroke (write-on)
  G.vstroke = (ctx, pts, wf, color, prog = 1) => {
    if (pts.length < 2) return;
    const L = cumLen(pts), tot = L[L.length - 1] || 1, upto = tot * Z.clamp(prog);
    const left = [], right = [];
    for (let i = 0; i < pts.length; i++) {
      if (L[i] > upto && i > 0) {
        const f = (upto - L[i - 1]) / Math.max(1e-6, L[i] - L[i - 1]);
        const px = Z.lerp(pts[i - 1][0], pts[i][0], f), py = Z.lerp(pts[i - 1][1], pts[i][1], f);
        const dx = pts[i][0] - pts[i - 1][0], dy = pts[i][1] - pts[i - 1][1], dl = Math.hypot(dx, dy) || 1, w = wf(upto / tot) / 2;
        left.push([px - dy / dl * w, py + dx / dl * w]); right.push([px + dy / dl * w, py - dx / dl * w]); break;
      }
      const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
      const dx = b[0] - a[0], dy = b[1] - a[1], dl = Math.hypot(dx, dy) || 1, w = wf(L[i] / tot) / 2;
      left.push([pts[i][0] - dy / dl * w, pts[i][1] + dx / dl * w]); right.push([pts[i][0] + dy / dl * w, pts[i][1] - dx / dl * w]);
    }
    ctx.beginPath(); ctx.moveTo(left[0][0], left[0][1]);
    for (let i = 1; i < left.length; i++) ctx.lineTo(left[i][0], left[i][1]);
    for (let i = right.length - 1; i >= 0; i--) ctx.lineTo(right[i][0], right[i][1]);
    ctx.closePath(); ctx.fillStyle = color; ctx.fill();
  };
  G.taper = (w, a = 0.15, b = 0.3) => u => w * Math.min(1, u / a + 0.15, (1 - u) / b + 0.1);
  // dry brush (飞白): a pressure-shaped body, ragged edges, dry streaks carved out toward the tail. pts already smooth.
  // o: { w, color, dry 0..1, seed, prog (write-on), alpha }. Drawn through Z.scratch[0] so the streaks only cut the stroke.
  G.brush = (ctx, pts, o = {}) => {
    const w = o.w || 60, seed = o.seed || 1, prog = o.prog ?? 1, dry = o.dry ?? 0.5, col = o.color || C.ink;
    if (prog <= 0 || pts.length < 2) return;
    const c = Z.scratch[0], x = c.getContext('2d'); G.reset(x); x.clearRect(0, 0, W, H); x.setTransform(ctx.getTransform());
    const wf = u => w * (0.3 + 0.7 * Math.min(1, u * 7)) * (1 - 0.5 * Math.pow(u, 2) * dry) * (1 + 0.09 * Z.noise1(u * 36, seed) + 0.05 * Z.noise1(u * 110, seed + 1));
    G.vstroke(x, pts, wf, col, prog);
    const L = cumLen(pts), tot = L[L.length - 1] || 1, sub = G.cut(pts, prog);
    x.globalCompositeOperation = 'destination-out'; x.lineCap = 'round';
    const n = Math.round(8 + w / 5);
    for (let b = 0; b < n; b++) {
      const v = Z.rnd(b, seed) - 0.5, edge = Math.abs(v) * 2, off = v * w * 0.92, bw = w * (0.008 + 0.028 * Z.rnd(b, seed + 1));
      x.lineWidth = bw; x.beginPath(); let pen = false, acc = 0;
      for (let i = 0; i < sub.length; i++) {
        if (i) acc += Math.hypot(sub[i][0] - sub[i - 1][0], sub[i][1] - sub[i - 1][1]);
        const u = acc / tot, a = sub[Math.max(0, i - 1)], c2 = sub[Math.min(sub.length - 1, i + 1)], dx = c2[0] - a[0], dy = c2[1] - a[1], dl = Math.hypot(dx, dy) || 1;
        const px = sub[i][0] - dy / dl * off * wf(u) / w, py = sub[i][1] + dx / dl * off * wf(u) / w;
        const dryness = dry * (0.15 + 1.1 * Math.pow(u, 1.5)) * (0.55 + 0.9 * edge);
        const on = Z.noise1(u * (14 + 10 * Z.rnd(b, seed + 2)) + b * 7.1, seed + b) * 0.5 + 0.5 < dryness;
        if (on) { if (!pen) { x.moveTo(px, py); pen = true; } else x.lineTo(px, py); } else pen = false;
      }
      x.stroke();
    }
    for (let i = 0; i < 70 * dry; i++) {                              // bites out of the ragged edge
      const u = Z.rnd(i, seed + 9), sd = Z.rnd(i, seed + 10) < 0.5 ? -1 : 1, k = Math.min(sub.length - 1, Math.floor(u * (pts.length - 1)));
      if (L[k] > tot * prog) continue;
      const a = pts[Math.max(0, k - 1)], c2 = pts[Math.min(pts.length - 1, k + 1)], dx = c2[0] - a[0], dy = c2[1] - a[1], dl = Math.hypot(dx, dy) || 1;
      const hw = wf(L[k] / tot) / 2;
      x.beginPath(); x.ellipse(pts[k][0] - dy / dl * hw * sd, pts[k][1] + dx / dl * hw * sd, w * (0.02 + 0.05 * Z.rnd(i, seed + 11)), w * 0.012, Math.atan2(dy, dx), 0, TAU); x.fill();
    }
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha *= o.alpha ?? 1; ctx.drawImage(c, 0, 0); ctx.restore();
  };
  // irregular closed blob (radius r, noise amp, seed); continuous fBm around the circle; returns Path2D
  G.blobPath = (x, y, r, amp = 0.25, seed = 1, n = 72, freq = 1.6) => {
    const p = new Path2D();
    for (let i = 0; i <= n; i++) {
      const a = i / n * TAU, ca = Math.cos(a), sa = Math.sin(a);
      let nz = 0, f = freq, am = 1, norm = 0;
      for (let o = 0; o < 4; o++) { nz += am * G.noise2(ca * f + 5.3 * o + 11, sa * f + 1.7 * o + 7, seed + o * 13); norm += am; f *= 2.2; am *= 0.5; }
      const rr = r * (1 + amp * 1.7 * nz / norm), px = x + ca * rr, py = y + sa * rr;
      i ? p.lineTo(px, py) : p.moveTo(px, py);
    }
    p.closePath(); return p;
  };
  // liquid splat: core blob + tendrils + flying drops. prog 0..1 (outExpo inside), o: { seed, color, n, reach }
  G.splat = (ctx, x, y, r, o = {}) => {
    const seed = o.seed || 3, k = E.outExpo(Z.clamp(o.prog ?? 1)), col = o.color || C.carmine, R = Z.rng(seed);
    if (k <= 0) return;
    ctx.save(); ctx.fillStyle = col;
    ctx.fill(G.blobPath(x, y, r * (0.35 + 0.65 * k), 0.22, seed));
    const n = o.n || 14;
    for (let i = 0; i < n; i++) {
      const a = R() * TAU, len = r * (0.6 + R() * (o.reach || 1.4)) * k, wd = r * (0.08 + R() * 0.14);
      const ex = x + Math.cos(a) * len, ey = y + Math.sin(a) * len;
      ctx.beginPath(); ctx.moveTo(x + Math.cos(a + Math.PI / 2) * wd, y + Math.sin(a + Math.PI / 2) * wd);
      ctx.quadraticCurveTo(x + Math.cos(a) * len * 0.6, y + Math.sin(a) * len * 0.6, ex, ey);
      ctx.quadraticCurveTo(x + Math.cos(a) * len * 0.6, y + Math.sin(a) * len * 0.6, x + Math.cos(a - Math.PI / 2) * wd, y + Math.sin(a - Math.PI / 2) * wd);
      ctx.fill();
      ctx.beginPath(); ctx.arc(ex, ey, wd * (0.6 + R() * 0.6), 0, TAU); ctx.fill();
      const dn = 1 + Math.floor(R() * 3);
      for (let d = 0; d < dn; d++) { const dl = len * (1.15 + R() * 0.7) * k; ctx.beginPath(); ctx.arc(x + Math.cos(a + R() * 0.2 - 0.1) * dl, y + Math.sin(a + R() * 0.2 - 0.1) * dl, wd * (0.25 + R() * 0.45), 0, TAU); ctx.fill(); }
    }
    ctx.restore();
  };
  // watercolour bloom: layered washes + paper granulation + a darker drying rim. o: { seed, color, prog, edge, a }
  G.bleed = (ctx, x, y, r, o = {}) => {
    const seed = o.seed || 5, k = G.EZ.out(Z.clamp(o.prog ?? 1)), col = o.color || C.carmine, a = o.a ?? 0.85;
    if (k <= 0) return;
    const rr = r * k;
    ctx.save();
    for (let l = 0; l < 5; l++) { ctx.globalAlpha = a * (l ? 0.16 : 0.42); ctx.fillStyle = col; ctx.fill(G.blobPath(x + Z.rnds(l, seed) * rr * 0.08, y + Z.rnds(l, seed + 1) * rr * 0.08, rr * (1 - l * 0.13), 0.22 + l * 0.04, seed + l * 11)); }
    ctx.globalAlpha = a * 0.35; ctx.fillStyle = G.mix(col, '#FFFFFF', 0.35);          // granulation: pale specks inside the wash
    ctx.save(); ctx.clip(G.blobPath(x, y, rr, 0.22, seed));
    for (let i = 0; i < 160; i++) { const ga = Z.rnd(i, seed + 3) * TAU, gr = Math.sqrt(Z.rnd(i, seed + 4)) * rr; ctx.beginPath(); ctx.arc(x + Math.cos(ga) * gr, y + Math.sin(ga) * gr, 1 + Z.rnd(i, seed + 5) * rr * 0.02, 0, TAU); ctx.fill(); }
    ctx.restore();
    ctx.globalAlpha = a * (o.edge ?? 0.6); ctx.strokeStyle = G.mix(col, '#000000', 0.3); ctx.lineWidth = 1.5 + r * 0.01;
    ctx.stroke(G.blobPath(x, y, rr, 0.22, seed));
    ctx.restore();
  };

  // ================================================================== typography (per glyph)
  const PUNCT = new Set([...'，。、．！？：；,.!?']);
  // o: { size, fam, weight, color, align ('center'|'left'|'right'), vertical, pitch (em), spacing (em), reveal (i, n) => 0..1,
  //      anim 'fade'|'pop'|'drop'|'ink'|'type'|'slam'|'none', stroke, strokeW, under (draw under-colour offset = misregistration),
  //      misreg [dx, dy], alpha, sizes [per-glyph scale], colors [per-glyph], rot [per-glyph rad], outline (hollow glyph) }
  // returns glyph boxes [{ch, x, y, s}]
  G.layout = (ctx, chars, o) => {
    const size = o.size || 96, sp = (o.spacing ?? 0.04) * size, pitch = (o.pitch ?? 1.08) * size;
    G.font(ctx, size, o.fam || 'song', o.weight || 700);
    const sc = i => (o.sizes && o.sizes[i]) || 1;
    if (o.vertical) {
      const hs = chars.map((c, i) => (PUNCT.has(c) ? 0.5 : 1) * pitch * sc(i));
      const tot = hs.reduce((a, b) => a + b, 0);
      let y = o.align === 'top' ? 0 : o.align === 'bottom' ? -tot : -tot / 2;
      return chars.map((c, i) => { const b = { ch: c, x: 0, y: y + hs[i] / 2, s: sc(i) }; y += hs[i]; return b; });
    }
    const ws = chars.map((c, i) => ctx.measureText(c).width * sc(i) + sp);
    const tot = ws.reduce((a, b) => a + b, 0) - sp;
    let x = o.align === 'left' ? 0 : o.align === 'right' ? -tot : -tot / 2;
    return chars.map((c, i) => { const b = { ch: c, x: x + ws[i] / 2 - sp / 2, y: 0, s: sc(i) }; x += ws[i]; return b; });
  };
  G.text = (ctx, str, x, y, o = {}) => {
    const chars = [...str].filter(c => o.keepSpaces || c.trim()), n = chars.length; if (!n) return [];
    const size = o.size || 96, boxes = G.layout(ctx, chars, o), anim = o.anim || 'fade';
    ctx.save(); ctx.translate(x, y); if (o.rotate) ctx.rotate(o.rotate);
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.globalAlpha *= o.alpha ?? 1;
    boxes.forEach((b, i) => {
      const k = o.reveal ? Z.clamp(o.reveal(i, n)) : 1; if (k <= 0) return;
      const s = size * b.s;
      let gx = b.x, gy = b.y, sc = 1, al = 1, rot = (o.rot && o.rot[i]) || 0, blur = 0;
      if (anim === 'fade') { al = k; gy += (1 - G.EZ.out(k)) * s * 0.18; }
      else if (anim === 'pop') { al = Math.min(1, k * 3); sc = Z.lerp(0.4, 1, E.outBack(k, 1.6)); }
      else if (anim === 'drop') { al = Math.min(1, k * 4); gy -= (1 - E.outBack(k, 1.2)) * s * 0.9; }
      else if (anim === 'slam') { al = Math.min(1, k * 5); sc = Z.lerp(2.6, 1, E.outExpo(k)); rot += (1 - E.outExpo(k)) * 0.15 * (i % 2 ? 1 : -1); }
      else if (anim === 'ink') { al = Z.clamp(k * 1.6); blur = (1 - E.outCubic(k)) * s * 0.12; sc = 1 + (1 - k) * 0.06; }
      else if (anim === 'type') { al = k > 0 ? 1 : 0; }
      if (al <= 0.003) return;
      if (PUNCT.has(b.ch) && o.vertical) { gx += s * 0.32; gy -= s * 0.32; }
      ctx.save(); ctx.translate(gx, gy); if (rot) ctx.rotate(rot); if (sc !== 1) ctx.scale(sc, sc);
      ctx.globalAlpha *= al; if (blur > 0.4) ctx.filter = `blur(${blur.toFixed(1)}px)`;
      G.font(ctx, s, o.fam || 'song', o.weight || 700);
      const col = (o.colors && o.colors[i]) || o.color || C.ink;
      if (o.misreg && o.under) { ctx.fillStyle = o.under; ctx.fillText(b.ch, o.misreg[0], o.misreg[1]); }
      if (o.stroke) { ctx.lineJoin = 'round'; ctx.lineWidth = o.strokeW || s * 0.06; ctx.strokeStyle = o.stroke; ctx.strokeText(b.ch, 0, 0); }
      if (o.outline) { ctx.lineJoin = 'round'; ctx.lineWidth = o.outlineW || Math.max(1.2, s * 0.018); ctx.strokeStyle = col; ctx.strokeText(b.ch, 0, 0); }
      else { ctx.fillStyle = col; ctx.fillText(b.ch, 0, 0); }
      ctx.restore();
    });
    ctx.restore();
    return boxes.map(b => ({ ch: b.ch, x: x + b.x, y: y + b.y, s: size * b.s }));
  };
  // reveal driven by the vocal: glyph i appears `lead` s before its onset and takes `dur` s
  G.sung = (line, t, lead = 0.12, dur = 0.22, from = 0) => {
    const ct = G.CT(line);
    return (i) => Z.clamp((t - (ct[Math.min(ct.length - 1, i + from)] - lead)) / dur);
  };
  // glyph mask (white glyph on transparent) for clipping / particles; cached
  const maskCache = new Map();
  G.glyphMask = (ch, px, fam = 'brush', weight = 400) => {
    const key = ch + '|' + px + '|' + fam + '|' + weight; let c = maskCache.get(key); if (c) return c;
    c = Z.canvas(Math.ceil(px * 1.3), Math.ceil(px * 1.3)); const x = c.getContext('2d');
    G.font(x, px, fam, weight); x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillStyle = '#fff'; x.fillText(ch, c.width / 2, c.height / 2);
    maskCache.set(key, c); return c;
  };
  // sample n points inside a glyph (for dissolves)
  const ptsCache = new Map();
  G.glyphPoints = (ch, n, fam = 'brush', weight = 400) => {
    const key = ch + n + fam + weight; if (ptsCache.has(key)) return ptsCache.get(key);
    const s = 200, c = Z.canvas(s, s), x = c.getContext('2d', { willReadFrequently: true });
    G.font(x, s * 0.86, fam, weight); x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillStyle = '#fff'; x.fillText(ch, s / 2, s / 2);
    const d = x.getImageData(0, 0, s, s).data, pts = [], R = Z.rng(Z.hash(ch.codePointAt(0), n));
    for (let g = 0; pts.length < n && g < n * 120; g++) { const px = Math.floor(R() * s), py = Math.floor(R() * s); if (d[(py * s + px) * 4 + 3] > 120) pts.push([px / s - 0.5, py / s - 0.5]); }
    ptsCache.set(key, pts); return pts;
  };

  // ================================================================== the protagonist: a poppy bud on a hairy stem
  // stem: arc-length integration of curvature (a natural crook). o: { x, y (base), len, size (bud length), nod (0 upright ..
  // 1 hanging), open (0 closed .. 1 sepals apart, red petals showing), crack (0..1 light fissures), sway (rad, wind), t,
  // pal 'plate'|'print'|'night'|'snow'|'sil', hairs (density 0..1), lw (line width), alpha, wither (0..1 grey & shrivelled),
  // detach: 0..1 bud separated from the stem tip (with offset dx, dy, spin) }
  const PAL = {
    plate: { line: '#2A2321', sepal: '#9DBB86', shade: '#6E9562', stem: '#8CAF77', red: C.carmine, redD: C.deep, redL: C.rouge, hatch: 'rgba(42,35,33,0.55)' },
    print: { line: C.ink, sepal: '#F1EADD', shade: '#DCD2C2', stem: '#EAE1D2', red: C.carmine, redD: C.deep, redL: C.rouge, hatch: 'rgba(27,20,32,0.42)' },
    blush: { line: C.ink, sepal: '#F4DCDA', shade: '#E6BFC0', stem: '#EAE1D2', red: C.carmine, redD: C.deep, redL: C.rouge, hatch: 'rgba(27,20,32,0.42)' },
    snow: { line: '#22303F', sepal: '#DDE7EE', shade: '#AFC2D2', stem: '#C9D8E3', red: C.carmine, redD: C.deep, redL: C.rouge, hatch: 'rgba(34,48,63,0.55)' },
    night: { line: '#FF9DB6', sepal: '#2A2050', shade: '#1A1438', stem: '#241C48', red: '#FF3D6E', redD: '#B3123E', redL: '#FF8FB0', hatch: 'rgba(255,157,182,0.45)' },
    sil: { line: C.ink, sepal: C.ink, shade: C.ink, stem: C.ink, red: C.carmine, redD: C.deep, redL: C.rouge, hatch: 'rgba(0,0,0,0)' },
    spring: { line: '#26301F', sepal: '#A7C98A', shade: '#6F9A5C', stem: '#86AE6A', red: '#D7263D', redD: '#9A1229', redL: '#F0607A', hatch: 'rgba(38,48,31,0.5)' },
    dead: { line: '#5A524F', sepal: '#B7AEA4', shade: '#968C82', stem: '#A49A90', red: '#7A5A55', redD: '#5A4440', redL: '#8A6A64', hatch: 'rgba(90,82,79,0.5)' },
  };
  G.BUDPAL = PAL;
  G.stemPoints = (o) => {
    const N = 64, len = o.len || 600, ds = len / N, turn = (o.nod ?? 0.8) * 2.75 + (o.sway || 0);
    const wts = []; let sw = 0;
    for (let i = 0; i < N; i++) { const u = (i + 0.5) / N, w = Z.smooth(0.5, 1.0, u); wts.push(w); sw += w; }
    let th = -Math.PI / 2 + (o.lean || 0) + (o.sway || 0) * 0.25, x = o.x, y = o.y; const pts = [[x, y]], ang = [th];
    for (let i = 0; i < N; i++) {
      th += turn * wts[i] / sw + (o.bend || 0) / N; x += Math.cos(th) * ds; y += Math.sin(th) * ds; pts.push([x, y]); ang.push(th);
    }
    return { pts, ang, tip: pts[N], th };
  };
  // ovoid half-width along the axis (u 0 = receptacle, 1 = tip)
  const EGG_N = (() => { let m = 0; for (let i = 1; i < 200; i++) { const u = i / 200; m = Math.max(m, Math.pow(u, 0.5) * Math.pow(1 - u, 0.62)); } return m; })();
  const budHW = u => { u = Z.clamp(u); return Math.pow(u, 0.5) * Math.pow(1 - u, 0.62) / EGG_N; };
  const sepalPath = (Lb, Wb, side, gap) => {             // in bud-local coords: x along axis, y across; side = +1 / -1
    const p = new Path2D(), n = 26;
    p.moveTo(0, 0);
    for (let i = 1; i <= n; i++) { const u = i / n; p.lineTo(u * Lb, side * Wb / 2 * budHW(u)); }
    for (let i = n; i >= 0; i--) { const u = i / n; p.lineTo(u * Lb, side * (gap * Math.sin(Math.PI * u) + Wb * 0.035 * Math.sin(Math.PI * u * 2))); }
    p.closePath(); return p;
  };
  G.bud = (ctx, o) => {
    const P = PAL[o.pal || 'plate'] || PAL.plate, t = o.t || 0, size = o.size || 140, lw = o.lw || Math.max(1.4, size * 0.016);
    const wither = o.wither || 0, open = Z.clamp(o.open || 0), hairs = o.hairs ?? 1;
    const st = G.stemPoints(o);
    ctx.save(); ctx.globalAlpha *= o.alpha ?? 1; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    // ---- stem
    if (o.stem !== false) {
      const sw = o.stemW || size * 0.085, stemPts = st.pts, prog = o.grow ?? 1;
      G.vstroke(ctx, stemPts, u => sw * (1.25 - 0.45 * u) + lw * 2, P.line, prog);
      G.vstroke(ctx, stemPts, u => sw * (1.25 - 0.45 * u), P.stem, prog);
      if (o.pal !== 'sil') {                                        // a thin highlight down one side
        ctx.save(); ctx.globalAlpha *= 0.35; G.vstroke(ctx, stemPts.map((p, i) => [p[0] + Math.cos(st.ang[i] + Math.PI / 2) * sw * 0.25, p[1] + Math.sin(st.ang[i] + Math.PI / 2) * sw * 0.25]), () => sw * 0.22, '#FFFFFF', prog); ctx.restore();
      }
      if (hairs > 0) {                                              // spreading bristles, pointing up the stem
        ctx.strokeStyle = P.line; ctx.lineWidth = Math.max(0.8, lw * 0.55);
        const n = Math.floor(stemPts.length * prog);
        ctx.beginPath();
        for (let i = 3; i < n; i += 2) {
          if (Z.rnd(i, 71) > hairs) continue;
          const [px, py] = stemPts[i], a = st.ang[i], side = (i >> 1) % 2 ? 1 : -1, hl = size * (0.06 + 0.05 * Z.rnd(i, 72));
          const ha = a + side * (1.05 + 0.25 * Z.rnds(i, 73)) - side * 0.35;
          const bx = px + Math.cos(a + side * Math.PI / 2) * sw * 0.55, by = py + Math.sin(a + side * Math.PI / 2) * sw * 0.55;
          ctx.moveTo(bx, by); ctx.quadraticCurveTo(bx + Math.cos(ha) * hl * 0.6, by + Math.sin(ha) * hl * 0.6, bx + Math.cos(ha - side * 0.25) * hl, by + Math.sin(ha - side * 0.25) * hl);
        }
        ctx.stroke();
      }
    }
    // ---- bud at the tip, along the stem tangent
    const det = Z.clamp(o.detach || 0);
    const Lb = size * (1 - 0.25 * wither), Wb = size * (0.74 - 0.24 * wither);
    let bx = st.tip[0], by = st.tip[1], th = st.th;
    if (det > 0) { bx += (o.dx || 0) * det; by += (o.dy || 0) * det; th += (o.spin || 0) * det; }
    ctx.save(); ctx.translate(bx, by); ctx.rotate(th);
    // receptacle swell
    ctx.fillStyle = P.line; ctx.beginPath(); ctx.ellipse(size * 0.02, 0, size * 0.07, size * 0.06, 0, 0, TAU); ctx.fill();
    ctx.fillStyle = P.stem; ctx.beginPath(); ctx.ellipse(size * 0.02, 0, size * 0.055, size * 0.045, 0, 0, TAU); ctx.fill();
    // red petals pushing out of the seam
    const gap = Wb * (0.02 + 0.3 * open);
    if (open > 0.01 && o.pal !== 'sil') {
      const rl = Lb * (0.82 + 0.3 * open), rw = Wb * (0.16 + 0.75 * open);
      const red = new Path2D(), n = 40;
      for (let i = 0; i <= n; i++) {
        const u = i / n, hw = rw / 2 * budHW(u) * (1 + 0.12 * Z.noise1(u * 9, 13));
        i ? red.lineTo(Lb * 0.06 + u * rl, -hw) : red.moveTo(Lb * 0.06, -hw);
      }
      for (let i = n; i >= 0; i--) { const u = i / n, hw = rw / 2 * budHW(u) * (1 + 0.12 * Z.noise1(u * 9 + 40, 14)); red.lineTo(Lb * 0.06 + u * rl, hw); }
      red.closePath();
      ctx.fillStyle = P.red; ctx.fill(red);
      ctx.save(); ctx.clip(red);                                       // crumpled silk: wrinkle strokes + a light ridge
      ctx.strokeStyle = P.redD; ctx.lineWidth = Math.max(1, lw * 0.8);
      for (let k = 0; k < 9; k++) {
        ctx.beginPath(); const u0 = 0.08 + k * 0.1;
        for (let j = 0; j <= 8; j++) { const v = (j / 8 - 0.5) * rw, u = u0 + 0.05 * Math.sin(j * 1.9 + k); j ? ctx.lineTo(Lb * 0.06 + u * rl, v) : ctx.moveTo(Lb * 0.06 + u * rl, v); }
        ctx.stroke();
      }
      ctx.globalAlpha *= 0.5; ctx.strokeStyle = P.redL; ctx.lineWidth = lw * 1.4;
      ctx.beginPath(); ctx.moveTo(Lb * 0.12, -rw * 0.08); ctx.bezierCurveTo(Lb * 0.4, -rw * 0.2, Lb * 0.7, rw * 0.05, Lb * 0.95, -rw * 0.02); ctx.stroke();
      ctx.restore();
      ctx.strokeStyle = P.line; ctx.lineWidth = lw * 0.9; ctx.stroke(red);
    }
    // two sepals (hinged at the receptacle, rotating apart when opening)
    for (const side of [-1, 1]) {
      ctx.save(); ctx.rotate(side * open * 0.55);
      const sp = sepalPath(Lb, Wb, side, gap * 0.5);
      ctx.fillStyle = P.sepal; ctx.fill(sp);
      if (o.pal !== 'sil') {
        ctx.save(); ctx.clip(sp);
        ctx.fillStyle = P.shade; ctx.globalAlpha *= 0.85;               // one shadow tone (the lower half, away from the light)
        ctx.beginPath(); ctx.ellipse(Lb * 0.55, side * Wb * 0.42, Lb * 0.62, Wb * 0.3, side * 0.12, 0, TAU); ctx.fill();
        ctx.globalAlpha = side > 0 ? 1 : 0.45; ctx.strokeStyle = P.hatch; ctx.lineWidth = Math.max(0.6, lw * 0.38);
        ctx.beginPath();                                                 // engraving hatch on the shadow side, following the curvature
        for (let k = 0; k < 13; k++) {
          const u = 0.12 + k * 0.062, hw = Wb / 2 * budHW(u), reach = side > 0 ? 0.42 : 0.68;
          ctx.moveTo(u * Lb, side * hw * 0.97); ctx.quadraticCurveTo((u + 0.02) * Lb, side * hw * (reach + 0.25), (u + 0.035) * Lb, side * hw * reach);
        }
        ctx.stroke(); ctx.globalAlpha = 1;
        if (wither > 0) { ctx.globalAlpha = wither * 0.6; ctx.strokeStyle = P.line; ctx.beginPath(); for (let k = 0; k < 6; k++) { const u = 0.15 + k * 0.13; ctx.moveTo(u * Lb, 0); ctx.lineTo((u + 0.08) * Lb, side * Wb * 0.4 * budHW(u)); } ctx.stroke(); }
        ctx.restore();
      }
      ctx.strokeStyle = P.line; ctx.lineWidth = lw; ctx.stroke(sp);
      if (hairs > 0 && o.pal !== 'sil') {                               // bristles along the outer edge
        ctx.beginPath(); ctx.lineWidth = Math.max(0.7, lw * 0.5);
        for (let k = 0; k < 26; k++) {
          const u = 0.06 + k * 0.034 + 0.01 * Z.rnds(k, side + 92); if (Z.rnd(k, side + 90) > hairs) continue;
          const hw = Wb / 2 * budHW(u), px = u * Lb, py = side * hw, du = 0.01, dy = side * Wb / 2 * (budHW(u + du) - budHW(u - du)) / (2 * du * Lb);
          const na = Math.atan2(side, -dy * side), hl = size * (0.06 + 0.06 * Z.rnd(k, side + 91));
          const hx = Math.cos(na) * 0.5 + 0.55, hy = Math.sin(na);
          ctx.moveTo(px, py); ctx.lineTo(px + hx * hl, py + hy * hl * 0.9);
        }
        ctx.stroke();
      }
      ctx.restore();
    }
    // light fissures (refrain 3): cracks across the sepals, glowing
    if ((o.crack || 0) > 0) {
      const net = crackNetLocal(o.crackSeed || 4, Lb, Wb);
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
      for (const [col, wd, al] of [[o.crackGlow || '#FFE9C8', lw * 4, 0.35], ['#FFFFFF', lw * 1.1, 1]]) {
        ctx.strokeStyle = Z.rgba(col, al); ctx.lineWidth = wd;
        for (const ln of net) {
          const loc = Z.clamp((o.crack - ln.d0) / (1 - ln.d0)); if (loc <= 0) continue;
          const sub = G.cut(ln.pts, loc); ctx.beginPath(); sub.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.stroke();
        }
      }
      ctx.restore();
    }
    ctx.restore();
    ctx.restore();
    return { tip: st.tip, th: st.th, pts: st.pts, center: [bx + Math.cos(th) * Lb * 0.5, by + Math.sin(th) * Lb * 0.5], Lb, Wb };
  };
  const crackCacheL = new Map();
  const crackNetLocal = (seed, Lb, Wb) => {
    const key = seed + '|' + Lb.toFixed(1); if (crackCacheL.has(key)) return crackCacheL.get(key);
    const R = Z.rng(seed), net = [];
    for (let i = 0; i < 7; i++) {                                       // fissures start at the seam and run outward
      const u0 = 0.2 + R() * 0.65, side = R() < 0.5 ? -1 : 1, pts = [[u0 * Lb, 0]];
      let x = u0 * Lb, y = 0, a = side * (Math.PI / 2) + R.range(-0.6, 0.6);
      for (let k = 0; k < 6; k++) { x += Math.cos(a) * Wb * 0.08; y += Math.sin(a) * Wb * 0.08; a += R.range(-0.5, 0.5); pts.push([x, y]); }
      net.push({ pts, d0: i * 0.09 });
    }
    net.push({ pts: Array.from({ length: 12 }, (_, k) => [Lb * (0.05 + k * 0.08), Wb * 0.02 * Math.sin(k * 2.1)]), d0: 0 });
    crackCacheL.set(key, net); return net;
  };

  // ================================================================== the open poppy (front view), from crumpled to open
  // o: { x, y, r, open 0..1, t, rot, pal 'plate'|'pressed'|'night', petals 4, seed, alpha, cup (0 flat .. 1 cupped), wind }
  G.poppy = (ctx, o) => {
    const r = o.r || 300, open = Z.clamp(o.open ?? 1), seed = o.seed || 2, t = o.t || 0, pressed = o.pal === 'pressed';
    const crumple = 1 - open, R0 = r * (0.28 + 0.72 * E.outCubic(open));
    const red = pressed ? '#B23A4A' : o.pal === 'night' ? '#FF3D6E' : '#D41E3C', redD = pressed ? '#7E2634' : '#8C0B22', redL = pressed ? '#CE6A72' : '#F04A62';
    ctx.save(); ctx.translate(o.x, o.y); ctx.rotate(o.rot || 0); ctx.globalAlpha *= o.alpha ?? 1;
    const order = [1, 3, 0, 2];                                          // outer pair behind, inner pair in front
    for (const k of order) {
      const base = (o.a0 || 0.3) + k * TAU / 4 + 0.12 * Z.rnds(k, seed), span = (k % 2 ? 1.05 : 1.2) * (0.75 + 0.25 * open);
      const pr = R0 * (k % 2 ? 0.92 : 1), path = new Path2D(), n = 60;
      path.moveTo(0, 0);
      for (let i = 0; i <= n; i++) {
        const u = i / n, a = base - span + 2 * span * u;
        const wav = 0.06 * Math.sin(u * TAU * 2.5 + k) + crumple * 0.22 * Z.noise1(u * 14 + k * 9 + t * 0.5, seed + k);
        const flutter = (o.wind || 0) * 0.03 * Math.sin(t * 6 + k * 2 + u * 8);
        const rr = pr * (Math.pow(Math.sin(Math.PI * u), 0.35) * (1 + wav + flutter));
        path.lineTo(Math.cos(a) * rr, Math.sin(a) * rr);
      }
      path.closePath();
      const g = ctx.createRadialGradient(0, 0, R0 * 0.05, 0, 0, pr);
      g.addColorStop(0, redD); g.addColorStop(0.45, red); g.addColorStop(1, redL);
      ctx.fillStyle = g; ctx.fill(path);
      ctx.save(); ctx.clip(path);
      // black basal blotch
      if (open > 0.4) {
        ctx.globalAlpha *= Z.clamp((open - 0.4) / 0.4) * (pressed ? 0.55 : 0.95);
        ctx.fillStyle = C.bloom.black;
        ctx.fill(G.blobPath(Math.cos(base) * pr * 0.2, Math.sin(base) * pr * 0.2, pr * 0.17, 0.3, seed + k * 5, 32, 2));
        ctx.globalAlpha = o.alpha ?? 1;
      }
      // veins and crumple folds
      ctx.strokeStyle = Z.rgba(redD, 0.55); ctx.lineWidth = Math.max(1, r * 0.004);
      ctx.beginPath();
      for (let v = 0; v < 13; v++) { const a = base - span * 0.85 + span * 1.7 * v / 12; ctx.moveTo(Math.cos(a) * pr * 0.22, Math.sin(a) * pr * 0.22); ctx.quadraticCurveTo(Math.cos(a + 0.05) * pr * 0.6, Math.sin(a + 0.05) * pr * 0.6, Math.cos(a) * pr * 0.97, Math.sin(a) * pr * 0.97); }
      ctx.stroke();
      if (crumple > 0.05) {
        ctx.fillStyle = Z.rgba(redD, 0.32 * crumple);                   // shadow patches where the silk folds under
        for (let f = 0; f < 6; f++) { const fa = base + (Z.rnd(f, seed + k) - 0.5) * span * 1.6, fr = pr * (0.3 + 0.55 * Z.rnd(f, seed + k + 3)); ctx.fill(G.blobPath(Math.cos(fa) * fr, Math.sin(fa) * fr, pr * 0.16, 0.45, seed + f * 7 + k)); }
        ctx.strokeStyle = Z.rgba(redD, 0.85 * crumple); ctx.lineWidth = Math.max(1, r * 0.005);
        for (let f = 0; f < 11; f++) {                                   // creases: bent strokes, mostly radial
          let fa = base + (Z.rnd(f, seed + 20 + k) - 0.5) * span * 1.7, fr = pr * (0.15 + 0.4 * Z.rnd(f, seed + 21 + k)), dir = fa + (Z.rnd(f, seed + 22 + k) - 0.5) * 1.6;
          ctx.beginPath(); let px = Math.cos(fa) * fr, py = Math.sin(fa) * fr; ctx.moveTo(px, py);
          for (let j = 0; j < 4; j++) { dir += (Z.rnd(f, j, seed + k) - 0.5) * 1.1; const st = pr * 0.09; px += Math.cos(dir) * st; py += Math.sin(dir) * st; ctx.lineTo(px, py); }
          ctx.stroke();
        }
      }
      ctx.restore();
      ctx.strokeStyle = Z.rgba(redD, 0.9); ctx.lineWidth = Math.max(1.2, r * 0.006); ctx.stroke(path);
    }
    // centre: stamens around the ovary with its flat, rayed stigma disc
    if (open > 0.2) {
      const ca = Z.clamp((open - 0.2) / 0.5), cr = r * 0.1;
      ctx.globalAlpha *= ca;
      ctx.strokeStyle = '#2A1218'; ctx.lineWidth = Math.max(1, r * 0.004);
      ctx.beginPath();
      for (let i = 0; i < 46; i++) { const a = i / 46 * TAU + Z.rnds(i, seed) * 0.05, l = cr * (1.5 + 0.6 * Z.rnd(i, seed + 1)); ctx.moveTo(Math.cos(a) * cr * 0.8, Math.sin(a) * cr * 0.8); ctx.lineTo(Math.cos(a) * l, Math.sin(a) * l); }
      ctx.stroke();
      ctx.fillStyle = '#1C0C12';
      for (let i = 0; i < 46; i++) { const a = i / 46 * TAU + Z.rnds(i, seed) * 0.05, l = cr * (1.5 + 0.6 * Z.rnd(i, seed + 1)); ctx.beginPath(); ctx.ellipse(Math.cos(a) * l, Math.sin(a) * l, r * 0.009, r * 0.006, a, 0, TAU); ctx.fill(); }
      ctx.fillStyle = pressed ? '#9DA58E' : '#8FA38A'; ctx.beginPath(); ctx.arc(0, 0, cr, 0, TAU); ctx.fill();
      ctx.strokeStyle = '#3B2A30'; ctx.lineWidth = Math.max(1.2, r * 0.006); ctx.stroke();
      ctx.beginPath();
      for (let i = 0; i < 10; i++) { const a = i / 10 * TAU; ctx.moveTo(0, 0); ctx.lineTo(Math.cos(a) * cr * 0.92, Math.sin(a) * cr * 0.92); }
      ctx.lineWidth = Math.max(1.5, r * 0.008); ctx.stroke();
    }
    ctx.restore();
  };

  // ================================================================== cochineal (胭脂虫): a waxy scale insect; crushing bleeds carmine
  // o: { rot, crush 0..1, t, seed, pal 'plate'|'night' }
  G.cochineal = (ctx, x, y, s, o = {}) => {
    const crush = Z.clamp(o.crush || 0), seed = o.seed || 7, R = Z.rng(seed), t = o.t || 0;
    ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot || 0);
    if (crush > 0) G.splat(ctx, 0, 0, s * 0.9, { prog: crush, seed: seed + 3, color: o.pal === 'night' ? '#FF2E5E' : C.carmine, n: 16, reach: 1.3 });
    ctx.scale(1, 1 - 0.75 * crush);
    ctx.strokeStyle = C.ink; ctx.lineWidth = Math.max(1, s * 0.022); ctx.lineCap = 'round';
    for (let i = 0; i < 3; i++) for (const sd of [-1, 1]) {           // short legs peeking out
      const lx = -s * 0.18 + i * s * 0.18, wig = Math.sin(t * 10 + i * 2 + sd) * (1 - crush);
      ctx.beginPath(); ctx.moveTo(lx, sd * s * 0.33); ctx.lineTo(lx + s * 0.05 + wig * s * 0.02, sd * s * 0.43); ctx.stroke();
    }
    const body = new Path2D(); body.ellipse(0, 0, s * 0.5, s * 0.38, 0, 0, TAU);
    ctx.fillStyle = G.mix('#6A3550', C.carmine, crush * 0.8); ctx.fill(body);
    ctx.save(); ctx.clip(body);
    ctx.strokeStyle = 'rgba(40,16,28,0.7)'; ctx.lineWidth = Math.max(1, s * 0.016);
    for (let i = 1; i < 9; i++) { const sx = -s * 0.5 + i * s * 0.111; ctx.beginPath(); ctx.moveTo(sx, -s * 0.4); ctx.quadraticCurveTo(sx + s * 0.05, 0, sx, s * 0.4); ctx.stroke(); }
    const wax = 1 - crush;                                             // white powdery wax: dense dabs, thicker on the back ridge
    for (let i = 0; i < 260; i++) {
      const a = R() * TAU, rr = Math.pow(R(), 0.7), wx = Math.cos(a) * rr * s * 0.5, wy = Math.sin(a) * rr * s * 0.38 * (0.6 + 0.4 * R());
      ctx.fillStyle = `rgba(248,246,242,${(0.35 + R() * 0.55) * wax})`;
      ctx.beginPath(); ctx.arc(wx, wy, s * (0.012 + R() * 0.035), 0, TAU); ctx.fill();
    }
    ctx.restore();
    ctx.strokeStyle = `rgba(248,246,242,${0.8 * (1 - crush)})`; ctx.lineWidth = Math.max(1, s * 0.012);   // fluffy rim
    ctx.beginPath(); for (let i = 0; i < 70; i++) { const a = i / 70 * TAU, ex = Math.cos(a) * s * 0.5, ey = Math.sin(a) * s * 0.38, l = s * (0.03 + 0.04 * Z.rnd(i, seed)); ctx.moveTo(ex, ey); ctx.lineTo(ex + Math.cos(a) * l, ey + Math.sin(a) * l); } ctx.stroke();
    ctx.strokeStyle = 'rgba(27,20,32,0.75)'; ctx.lineWidth = Math.max(1, s * 0.016); ctx.stroke(body);
    ctx.restore();
  };

  // ================================================================== silverfish (衣鱼): tapered carrot body, antennae, three cerci; wriggles
  G.silverfish = (ctx, x, y, ang, s, t, seed = 1, alpha = 1) => {
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang); ctx.globalAlpha *= alpha;
    const N = 20, wig = u => Math.sin(u * 5 - t * 24 + seed) * s * 0.045 * (0.25 + u);
    const sp = []; for (let i = 0; i <= N; i++) { const u = i / N; sp.push([s * 0.12 - u * s, wig(u)]); }
    const hw = u => s * (u < 0.12 ? 0.075 + 0.55 * u : 0.14 * Math.pow(1 - (u - 0.12) / 0.88, 0.8) + 0.008);
    ctx.strokeStyle = 'rgba(60,64,74,0.9)'; ctx.lineWidth = Math.max(0.8, s * 0.01); ctx.lineCap = 'round';
    const tl = sp[N];
    for (const a of [-0.32, 0, 0.32]) { ctx.beginPath(); ctx.moveTo(tl[0], tl[1]); ctx.quadraticCurveTo(tl[0] - s * 0.3, tl[1] + a * s * 0.25 + Math.sin(t * 9 + a * 5) * s * 0.03, tl[0] - s * 0.62, tl[1] + a * s * 0.7); ctx.stroke(); }
    for (const sd of [-1, 1]) { ctx.beginPath(); ctx.moveTo(sp[0][0], sp[0][1] + sd * s * 0.02); ctx.bezierCurveTo(s * 0.4, sd * s * 0.06, s * 0.7, sd * s * (0.3 + 0.05 * Math.sin(t * 7 + sd)), s * 1.05, sd * s * 0.5); ctx.stroke(); }
    for (const sd of [-1, 1]) for (let l = 0; l < 3; l++) { const q = sp[3 + l * 2]; ctx.beginPath(); ctx.moveTo(q[0], q[1] + sd * hw(0.15 + l * 0.1) * 0.8); ctx.lineTo(q[0] + s * 0.05 * Math.sin(t * 20 + l + sd), q[1] + sd * hw(0.15) * 1.6); ctx.stroke(); }
    const body = new Path2D(); body.moveTo(sp[0][0] + s * 0.02, sp[0][1]);
    for (let i = 0; i <= N; i++) body.lineTo(sp[i][0], sp[i][1] - hw(i / N));
    for (let i = N; i >= 0; i--) body.lineTo(sp[i][0], sp[i][1] + hw(i / N));
    body.closePath();
    const g = ctx.createLinearGradient(0, -s * 0.15, 0, s * 0.15); g.addColorStop(0, '#E8ECF1'); g.addColorStop(0.45, '#B3BBC6'); g.addColorStop(1, '#6C7480');
    ctx.fillStyle = g; ctx.fill(body);
    ctx.save(); ctx.clip(body); ctx.strokeStyle = 'rgba(60,64,74,0.45)'; ctx.lineWidth = Math.max(0.6, s * 0.006);
    for (let i = 2; i < N; i++) { const q = sp[i], h = hw(i / N); ctx.beginPath(); ctx.moveTo(q[0] + s * 0.01, q[1] - h); ctx.quadraticCurveTo(q[0] - s * 0.02, q[1], q[0] + s * 0.01, q[1] + h); ctx.stroke(); }
    ctx.strokeStyle = 'rgba(255,255,255,0.7)'; ctx.lineWidth = Math.max(1, s * 0.014);
    ctx.beginPath(); for (let i = 1; i < N - 3; i++) { const q = sp[i]; i > 1 ? ctx.lineTo(q[0], q[1] - hw(i / N) * 0.35) : ctx.moveTo(q[0], q[1] - hw(i / N) * 0.35); } ctx.stroke();
    ctx.restore();
    ctx.strokeStyle = 'rgba(50,54,64,0.8)'; ctx.lineWidth = Math.max(0.8, s * 0.008); ctx.stroke(body);
    ctx.restore();
  };

  // ================================================================== seals (印章): cached stamp art + stamping animation
  const sealCache = new Map();
  G.sealArt = (text, px, style = 'yin', color = C.carmine, seed = 3, fam = 'song') => {
    const key = [text, px, style, color, seed, fam].join('|'); let c = sealCache.get(key); if (c) return c;
    const chars = [...text], n = chars.length;
    // 1 and 4 glyphs: square; 2 and 3 glyphs: a tall name-seal rectangle (one column)
    const sw = n === 2 ? px * 0.56 : n === 3 ? px * 0.42 : px, sh = px;
    const pad = Math.ceil(px * 0.12); c = Z.canvas(Math.ceil(sw + pad * 2), Math.ceil(sh + pad * 2)); const x = c.getContext('2d'), R = Z.rng(seed);
    const sq = new Path2D(), m = 22;
    const edge = (x0, y0, x1, y1) => { for (let i = 0; i <= m; i++) { const k = i / m; sq.lineTo(Z.lerp(x0, x1, k) + R.range(-1, 1) * px * 0.008, Z.lerp(y0, y1, k) + R.range(-1, 1) * px * 0.008); } };
    sq.moveTo(pad, pad); edge(pad, pad, pad + sw, pad); edge(pad + sw, pad, pad + sw, pad + sh); edge(pad + sw, pad + sh, pad, pad + sh); edge(pad, pad + sh, pad, pad); sq.closePath();
    // glyph cells (u, v in the seal box, size in px): 4 = 2x2 read right column first
    const cells = n === 1 ? [[0.5, 0.5, 0.78]] : n === 2 ? [[0.5, 0.27, 0.44], [0.5, 0.73, 0.44]] : n === 3 ? [[0.5, 0.18, 0.31], [0.5, 0.5, 0.31], [0.5, 0.82, 0.31]] : [[0.73, 0.28, 0.42], [0.73, 0.72, 0.42], [0.27, 0.28, 0.42], [0.27, 0.72, 0.42]];
    const drawGlyphs = col => {
      x.fillStyle = col;
      chars.slice(0, 4).forEach((ch, i) => {
        const [u, v, s] = cells[i]; G.font(x, px * s, fam, 900);
        x.save(); x.translate(pad + u * sw, pad + v * sh); x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(ch, 0, px * 0.01); x.restore();
      });
    };
    if (style === 'yin') {                                             // red block, glyphs carved out (white)
      x.fillStyle = color; x.fill(sq);
      x.globalCompositeOperation = 'destination-out'; drawGlyphs('#000');
    } else {                                                           // red glyphs inside a red border
      x.strokeStyle = color; x.lineWidth = px * 0.06; x.stroke(sq); drawGlyphs(color);
    }
    x.globalCompositeOperation = 'destination-out';                    // ink erosion: specks and a worn corner
    for (let i = 0; i < 260; i++) { const r = px * (0.002 + Math.pow(R(), 4) * 0.02); x.globalAlpha = 0.4 + R() * 0.6; x.beginPath(); x.arc(pad + R() * sw, pad + R() * sh, r, 0, TAU); x.fill(); }
    x.globalAlpha = 0.5; const wc = R() * 4 | 0, cxw = pad + (wc % 2) * sw, cyw = pad + (wc >> 1) * sh;
    const gw = x.createRadialGradient(cxw, cyw, 0, cxw, cyw, px * 0.35); gw.addColorStop(0, 'rgba(0,0,0,0.6)'); gw.addColorStop(1, 'rgba(0,0,0,0)'); x.fillStyle = gw; x.fillRect(0, 0, c.width, c.height);
    G.reset(x);
    sealCache.set(key, c); return c;
  };
  // stamp at (cx, cy); k = time since the stamp lands (s) — negative = not yet. Lands with a squash and a tiny jolt.
  G.seal = (ctx, cx, cy, px, text, o = {}) => {
    const k = o.k ?? 1; if (k < -0.12) return;
    const art = G.sealArt(text, px, o.style || 'yin', o.color || C.carmine, o.seed || 3, o.fam || 'song');
    const pre = Z.clamp((k + 0.12) / 0.12), sc = k < 0 ? Z.lerp(1.6, 1.02, E.inQuad(pre)) : 1 + 0.02 * Math.exp(-k * 18), al = k < 0 ? pre * 0.35 : 1;
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(o.rot || 0); ctx.scale(sc, sc); ctx.globalAlpha *= al * (o.alpha ?? 1);
    if (o.multiply !== false) ctx.globalCompositeOperation = 'multiply';
    ctx.drawImage(art, -art.width / 2, -art.height / 2);
    ctx.restore();
  };

  // ================================================================== specimen label (标本签)
  // rows: [[key, value], …]; o: { k (0..1 typing progress), title, no, w, row (row height), ink, accent, paper, keyFam, valFam }
  G.label = (ctx, x, y, rows, o = {}) => {
    const w = o.w || 560, rh = o.row || 46, h = rh * (rows.length + 1.6) + 20, k = o.k ?? 1, ink = o.ink || C.ink;
    ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot || 0);
    ctx.fillStyle = o.paper || '#FBF7EE'; ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = ink; ctx.lineWidth = 2.2; ctx.strokeRect(0, 0, w, h); ctx.lineWidth = 0.8; ctx.strokeRect(7, 7, w - 14, h - 14);
    G.font(ctx, rh * 0.5, 'song', 900); ctx.fillStyle = ink; ctx.textBaseline = 'middle'; ctx.textAlign = 'center';
    ctx.fillText(o.title || '植物标本', w / 2, rh * 0.85);
    if (o.no) { G.font(ctx, rh * 0.36, 'dot', 400); ctx.textAlign = 'right'; ctx.fillStyle = o.accent || C.carmine; ctx.fillText(o.no, w - 20, rh * 0.85); }
    ctx.strokeStyle = Z.rgba(ink, 0.5); ctx.beginPath(); ctx.moveTo(18, rh * 1.45); ctx.lineTo(w - 18, rh * 1.45); ctx.stroke();
    const total = rows.reduce((a, r) => a + [...r[1]].length + 2, 0); let used = 0;
    rows.forEach((r, i) => {
      const yy = rh * (2.0 + i);
      ctx.textAlign = 'left'; G.font(ctx, rh * 0.4, o.keyFam || 'song', 500); ctx.fillStyle = Z.rgba(ink, 0.7);
      ctx.fillText(r[0], 22, yy);
      ctx.strokeStyle = Z.rgba(ink, 0.25); ctx.lineWidth = 0.8; ctx.beginPath(); ctx.moveTo(130, yy + rh * 0.32); ctx.lineTo(w - 22, yy + rh * 0.32); ctx.stroke();
      const vis = Math.max(0, Math.min([...r[1]].length, Math.floor(k * total - used - 2)));
      used += [...r[1]].length + 2;
      if (vis > 0) { G.font(ctx, rh * 0.6, o.valFam || 'hand', 400); ctx.fillStyle = (r[2] || ink); ctx.fillText([...r[1]].slice(0, vis).join(''), 140, yy - rh * 0.02); }
    });
    ctx.restore();
    return { w, h };
  };

  // ================================================================== particles (closed form)
  // petals: o { n, seed, area [x0,y0,x1,y1], color, color2, size, wind, fall (px/s), spin }
  G.petals = (ctx, t, o = {}) => {
    const n = o.n ?? 30, seed = o.seed ?? 61, [x0, y0, x1, y1] = o.area || [-100, -100, W + 100, H + 100];
    ctx.save();
    for (let i = 0; i < n; i++) {
      const life = (y1 - y0) / ((o.fall ?? 90) * (0.6 + 0.8 * Z.rnd(i, seed))), k = Z.fract((t + Z.rnd(i, seed + 1) * life) / life);
      const x = Z.lerp(x0, x1, Z.rnd(i, seed + 2)) + Math.sin(k * 6 + i) * 90 + (o.wind ?? 120) * k * life * 0.3, y = Z.lerp(y0, y1, k);
      const s = (o.size ?? 14) * (0.6 + 0.8 * Z.rnd(i, seed + 3)), flip = Math.cos(t * (1.5 + Z.rnd(i, seed + 4) * 2) + i), rot = t * (o.spin ?? 1) * (Z.rnd(i, seed + 5) - 0.5) * 3 + i;
      ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(Math.max(0.12, Math.abs(flip)), 1);
      ctx.fillStyle = flip > 0 ? (o.color || C.pink) : (o.color2 || o.color || C.rouge); ctx.globalAlpha *= o.alpha ?? 0.9;
      ctx.beginPath(); ctx.moveTo(0, -s); ctx.bezierCurveTo(s * 0.9, -s * 0.6, s * 0.7, s * 0.7, 0, s); ctx.bezierCurveTo(-s * 0.7, s * 0.7, -s * 0.9, -s * 0.6, 0, -s); ctx.fill();
      ctx.restore();
    }
    ctx.restore();
  };
  // snow: depth layers; o { n, seed, color, size, speed, wind, alpha, area }
  G.snow = (ctx, t, o = {}) => {
    const n = o.n ?? 160, seed = o.seed ?? 81, [x0, y0, x1, y1] = o.area || [-60, -60, W + 60, H + 60];
    ctx.save(); ctx.fillStyle = o.color || '#FFFFFF';
    for (let i = 0; i < n; i++) {
      const z = Z.rnd(i, seed), sp = (o.speed ?? 70) * (0.4 + 1.2 * z), life = (y1 - y0) / sp, k = Z.fract((t + Z.rnd(i, seed + 1) * life) / life);
      const x = Z.lerp(x0, x1, Z.rnd(i, seed + 2)) + Math.sin(t * (0.6 + z) + i) * 30 * (0.5 + z) + (o.wind ?? 20) * k * life;
      const y = Z.lerp(y0, y1, k), r = (o.size ?? 3) * (0.4 + 1.4 * z * z);
      ctx.globalAlpha = (o.alpha ?? 0.9) * (0.35 + 0.65 * z);
      ctx.beginPath(); ctx.arc(((x - x0) % (x1 - x0) + (x1 - x0)) % (x1 - x0) + x0, y, r, 0, TAU); ctx.fill();
    }
    ctx.restore();
  };
  // frost crystals growing from the frame edges: cached dendrites, revealed by prog 0..1
  const frostCache = new Map();
  G.frost = (ctx, prog, o = {}) => {
    const seed = o.seed || 9, key = seed + '|' + (o.n || 26); let net = frostCache.get(key);
    if (!net) {
      net = []; const R = Z.rng(seed);
      const grow = (x, y, a, len, depth, d0) => {
        const pts = [[x, y]]; let px = x, py = y, aa = a;
        const steps = Math.max(2, Math.round(len / 14));
        for (let i = 0; i < steps; i++) { aa += R.range(-0.08, 0.08); px += Math.cos(aa) * len / steps; py += Math.sin(aa) * len / steps; pts.push([px, py]); }
        net.push({ pts, d0, d1: Math.min(1, d0 + 0.22 + 0.08 * depth), w: Math.max(0.5, 1.8 - depth * 0.55), a: 1 - depth * 0.2 });
        if (depth < 3) for (let b = 2; b < steps - 1; b += 2) {
          const [bx, by] = pts[b], k = b / steps;
          for (const sd of [-1, 1]) if (R() < 0.62 - depth * 0.12) grow(bx, by, aa + sd * (1.02 + R() * 0.12), len * (0.28 + 0.18 * R()) * (1 - k * 0.6), depth + 1, d0 + 0.2 * k + 0.06);
        }
      };
      const n = o.n || 26;
      for (let i = 0; i < n; i++) {
        const side = i % 4, u = R();
        const [x, y, a] = side === 0 ? [u * W, -10, Math.PI / 2] : side === 1 ? [W + 10, u * H, Math.PI] : side === 2 ? [u * W, H + 10, -Math.PI / 2] : [-10, u * H, 0];
        grow(x, y, a + R.range(-0.6, 0.6), 140 + R() * 300, 0, R() * 0.25);
      }
      frostCache.set(key, net);
    }
    ctx.save(); ctx.lineCap = 'round'; ctx.strokeStyle = o.color || 'rgba(250,252,255,0.9)';
    for (const ln of net) {
      const loc = Z.clamp((prog - ln.d0) / (ln.d1 - ln.d0)); if (loc <= 0) continue;
      ctx.lineWidth = ln.w * (o.width ?? 1); ctx.globalAlpha = ln.a * (o.alpha ?? 1);
      const sub = G.cut(ln.pts, loc); ctx.beginPath(); sub.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.stroke();
    }
    ctx.restore();
  };

  // ================================================================== frame helpers
  G.vignette = (ctx, a = 0.3, color = '27,20,32') => {
    const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.05);
    g.addColorStop(0, `rgba(${color},0)`); g.addColorStop(1, `rgba(${color},${a})`);
    ctx.save(); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
  };
  // camera: apply zoom / pan / roll about (cx, cy) — call inside save()
  G.cam = (ctx, zoom = 1, dx = 0, dy = 0, rot = 0, cx = W / 2, cy = H / 2) => { ctx.translate(cx + dx, cy + dy); if (rot) ctx.rotate(rot); ctx.scale(zoom, zoom); ctx.translate(-cx, -cy); };
  // halftone shading band (print look)
  G.halftone = (ctx, rect, step, fn, color) => D.halftone(ctx, rect, step, fn, color);
  // corner registration marks + scale bar (specimen sheet furniture)
  G.sheetMarks = (ctx, o = {}) => {
    const ink = o.ink || C.ink, a = o.alpha ?? 0.55, m = o.margin || 70;
    ctx.save(); ctx.strokeStyle = Z.rgba(ink, a); ctx.lineWidth = 1.3;
    for (const [x, y, sx, sy] of [[m, m, 1, 1], [W - m, m, -1, 1], [m, H - m, 1, -1], [W - m, H - m, -1, -1]]) {
      ctx.beginPath(); ctx.moveTo(x, y + sy * 34); ctx.lineTo(x, y); ctx.lineTo(x + sx * 34, y); ctx.stroke();
    }
    if (o.scale !== false) {                                            // 0 1 2 3 4 5 cm scale bar
      const x0 = o.sx ?? m + 10, y0 = o.sy ?? H - m - 28, u = 38;
      for (let i = 0; i < 5; i++) { ctx.fillStyle = i % 2 ? Z.rgba(ink, a) : 'rgba(0,0,0,0)'; ctx.fillRect(x0 + i * u, y0, u, 8); ctx.strokeRect(x0 + i * u, y0, u, 8); }
      G.font(ctx, 15, 'dot', 400); ctx.fillStyle = Z.rgba(ink, a); ctx.textAlign = 'center'; ctx.textBaseline = 'top';
      for (let i = 0; i <= 5; i++) ctx.fillText(String(i), x0 + i * u, y0 + 13);
      ctx.textAlign = 'left'; ctx.fillText('cm', x0 + 5 * u + 12, y0 + 13);
    }
    ctx.restore();
  };
  // a strip of washi tape holding a stem down
  G.tape = (ctx, x, y, w, h, rot, color = 'rgba(232,214,190,0.78)', seed = 1) => {
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.fillStyle = color;
    ctx.beginPath(); ctx.moveTo(-w / 2, -h / 2);
    for (let i = 0; i <= 6; i++) ctx.lineTo(-w / 2 + w * i / 6, -h / 2 + Z.rnds(i, seed) * 3);
    for (let i = 0; i <= 6; i++) ctx.lineTo(w / 2 + Z.rnds(i, seed + 3) * 4, -h / 2 + h * i / 6);
    for (let i = 6; i >= 0; i--) ctx.lineTo(-w / 2 + w * i / 6, h / 2 + Z.rnds(i, seed + 5) * 3);
    for (let i = 6; i >= 0; i--) ctx.lineTo(-w / 2 + Z.rnds(i, seed + 7) * 4, -h / 2 + h * i / 6);
    ctx.closePath(); ctx.fill(); ctx.restore();
  };

  // ================================================================== transitions (paper material)
  // tear: A rips along a jagged diagonal; the halves pull apart, B underneath. o: { angle, seed, edge }
  Z.transition('tear', (ctx, A, B, k, o) => {
    ctx.drawImage(B, 0, 0);
    const e = G.EZ.io(k), seed = o.seed || 4, ang = o.angle ?? 1.35, R = Z.rng(seed), n = 36;
    const cx = W / 2, cy = H / 2, dx = Math.cos(ang), dy = Math.sin(ang), L = Math.hypot(W, H);
    const line = []; for (let i = 0; i <= n; i++) { const u = i / n - 0.5; line.push([cx + dx * u * L + (-dy) * R.range(-1, 1) * 26, cy + dy * u * L + dx * R.range(-1, 1) * 26]); }
    for (const sd of [-1, 1]) {
      const p = new Path2D(); p.moveTo(line[0][0], line[0][1]); line.forEach(q => p.lineTo(q[0], q[1]));
      p.lineTo(line[n][0] + (-dy) * sd * L, line[n][1] + dx * sd * L); p.lineTo(line[0][0] + (-dy) * sd * L, line[0][1] + dx * sd * L); p.closePath();
      const off = e * W * 0.75;
      ctx.save(); ctx.translate((-dy) * sd * off, dx * sd * off); ctx.rotate(sd * 0.05 * e); ctx.clip(p); ctx.drawImage(A, 0, 0);
      ctx.strokeStyle = o.edge || '#FBF7EE'; ctx.lineWidth = 7; ctx.stroke(p); ctx.restore();
    }
  });
  // budIris: B revealed through a growing bud / teardrop shape. o: { cx, cy, rot, color }
  Z.transition('budIris', (ctx, A, B, k, o) => {
    ctx.drawImage(A, 0, 0);
    const e = E.inOutExpo(k), cx = o.cx ?? W / 2, cy = o.cy ?? H / 2, s = Math.max(1, e * Math.hypot(W, H) * 1.25);
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(o.rot ?? 0.5);
    const p = new Path2D(); p.moveTo(0, -s); p.bezierCurveTo(s * 0.62, -s * 0.35, s * 0.62, s * 0.55, 0, s * 0.62); p.bezierCurveTo(-s * 0.62, s * 0.55, -s * 0.62, -s * 0.35, 0, -s); p.closePath();
    ctx.save(); ctx.clip(p); ctx.rotate(-(o.rot ?? 0.5)); ctx.translate(-cx, -cy); ctx.drawImage(B, 0, 0); ctx.restore();
    if (k > 0 && k < 1) { ctx.strokeStyle = Z.rgba(o.color || C.carmine, 1 - k); ctx.lineWidth = 12 * (1 - k) + 2; ctx.stroke(p); }
    ctx.restore();
  });
  // bleed: B soaks through A like ink in rice paper (several organic blobs with a coloured rim). o: { seed, color, cx, cy }
  Z.transition('bleed', (ctx, A, B, k, o) => {
    ctx.drawImage(A, 0, 0);
    const seed = o.seed || 12, R = Z.rng(seed), e = G.EZ.io(k), blobs = [];
    const cx = o.cx ?? W / 2, cy = o.cy ?? H / 2;
    for (let i = 0; i < 7; i++) blobs.push([i ? R() * W : cx, i ? R() * H : cy, i ? 0.1 + R() * 0.25 : 0]);
    const p = new Path2D();
    for (const [bx, by, d] of blobs) { const loc = Z.clamp((e - d) / (1 - d)); if (loc > 0) p.addPath(G.blobPath(bx, by, Math.hypot(W, H) * 0.85 * E.inCubic(loc) + 1, 0.3, seed + bx | 0, 64, 2.5)); }
    ctx.save(); ctx.clip(p); ctx.drawImage(B, 0, 0); ctx.restore();
    if (k > 0 && k < 1) { ctx.save(); ctx.strokeStyle = Z.rgba(o.color || C.carmine, 0.85 * (1 - k)); ctx.lineWidth = 9; ctx.stroke(p); ctx.restore(); }
  });
  // stamp: a seal-shaped square grows from the centre with a red border; B inside
  Z.transition('stamp', (ctx, A, B, k, o) => {
    ctx.drawImage(A, 0, 0);
    const e = E.inOutExpo(k), cx = o.cx ?? W / 2, cy = o.cy ?? H / 2, s = Math.max(1, e * Math.hypot(W, H));
    ctx.save(); ctx.translate(cx, cy); ctx.rotate((o.rot ?? -0.06) * (1 - e));
    ctx.beginPath(); ctx.rect(-s / 2, -s / 2, s, s); ctx.save(); ctx.clip(); ctx.rotate(-(o.rot ?? -0.06) * (1 - e)); ctx.translate(-cx, -cy); ctx.drawImage(B, 0, 0); ctx.restore();
    ctx.strokeStyle = Z.rgba(o.color || C.carmine, 1 - e * 0.8); ctx.lineWidth = 16 * (1 - e) + 3; ctx.strokeRect(-s / 2, -s / 2, s, s);
    ctx.restore();
  });
})();
