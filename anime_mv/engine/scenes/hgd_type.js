/* engine/scenes/hgd_type.js — 花骨朵: bespoke lyric typography that lives inside each image (no template layer).
 *
 * Every line is drawn glyph by glyph, each glyph appearing on its own sung onset (analysis/char_timing.json), with a
 * layout and an effect chosen for that shot's imagery and the words' meaning: snow that gathers into glyphs and blows
 * away, glyphs pressed into the snow paths, written along the palm, cast as shadows on the alley wall, made of the
 * veil's silver beads, stamped in rouge, falling with her, sprouting roots, eaten through, floating with petals...
 * The words themselves are read at runtime from the user's LRC (Z.HGD.LYR); nothing here contains lyric text.
 *
 *   G.lyric(ctx, S, spec)          draw one spec; scenes call G.lyrics(ctx, S, z) for all specs of a z level
 *   spec = { line, from, to, z: 'back'|'front'|'text', lay: {...}, fx, fam, weight, size, color, stroke,
 *            lead, inDur, hold, outDur, until, out, seed, ... }
 *   lay  = { type: 'col', x, y, pitch, per, gap }  | { type: 'row', x, y, spacing, align, per, gap }
 *        | { type: 'path', pts: [[x,y]...], a0, a1, orient }  | { type: 'quad', quad: [TL,TR,BR,BL], grid: 'row'|'col' }
 *        | { type: 'fn', fn: (i, n, S, st) => [x, y, rot, scale] }
 */
(() => {
  'use strict';
  const Z = window.Z, D = Z.draw, E = Z.ease, G = Z.HGD, P = G.P;
  const W = 1920, H = 1080;

  G.CT = [];                                         // per-glyph onsets (numbers only), set by the timeline
  // glyphs (non-space) of line n, with their onsets
  G.lineInfo = (n) => {
    const L = G.LYR[n - 1]; if (!L) return null;
    const chars = [...L.text].filter(c => c.trim());
    const e = G.CT.find(x => x.line === n - 1);
    const t0 = e ? e.t : L.t, end = e ? e.end : (G.LYR[n] ? G.LYR[n].t - 0.2 : L.t + 3);
    const on = chars.map((c, i) => (e && e.chars[i] != null ? e.chars[i] : t0 + (end - t0) * i / Math.max(1, chars.length)));
    return { chars, on, t0, end };
  };

  // ------------------------------------------------------------------ glyph masks (sampled once per glyph + face)
  const maskCache = new Map();
  G.glyphMask = (ch, fam = 'serif', weight = 400) => {
    const key = ch + '|' + fam + '|' + weight; let m = maskCache.get(key); if (m) return m;
    const s = 160, c = Z.canvas(s, s), x = c.getContext('2d', { willReadFrequently: true });
    D.font(x, s * 0.82, fam, weight); x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillStyle = '#000'; x.fillText(ch, s / 2, s / 2);
    const d = x.getImageData(0, 0, s, s).data, inside = [], edge = [], R = Z.rng(Z.hash(ch.codePointAt(0), weight));
    const A = (px, py) => (px < 0 || py < 0 || px >= s || py >= s ? 0 : d[(py * s + px) * 4 + 3]);
    for (let py = 0; py < s; py += 2) for (let px = 0; px < s; px += 2) {
      if (A(px, py) > 128) {
        inside.push([px / s - 0.5, py / s - 0.5]);
        if (A(px + 3, py) < 60 || A(px - 3, py) < 60 || A(px, py + 3) < 60 || A(px, py - 3) < 60) edge.push([px / s - 0.5, py / s - 0.5]);
      }
    }
    // shuffle (deterministic) so subsets look even
    for (let i = inside.length - 1; i > 0; i--) { const j = Math.floor(R() * (i + 1)); [inside[i], inside[j]] = [inside[j], inside[i]]; }
    for (let i = edge.length - 1; i > 0; i--) { const j = Math.floor(R() * (i + 1)); [edge[i], edge[j]] = [edge[j], edge[i]]; }
    m = { inside, edge }; maskCache.set(key, m); return m;
  };
  // a stamped glyph (rough rubber-stamp edges), cached as a small canvas
  const stampCache = new Map();
  const stampGlyph = (ch, color, fam = 'brush') => {
    const key = ch + color + fam; let c = stampCache.get(key); if (c) return c;
    const s = 220; c = Z.canvas(s, s); const x = c.getContext('2d');
    D.font(x, s * 0.78, fam, 400); x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillStyle = color; x.fillText(ch, s / 2, s / 2 + 4);
    x.globalCompositeOperation = 'destination-out'; const R = Z.rng(Z.hash(ch.codePointAt(0), 77));
    for (let i = 0; i < 260; i++) { x.globalAlpha = 0.25 + 0.6 * R(); x.beginPath(); x.arc(R() * s, R() * s, 0.6 + 2.6 * R() * R(), 0, Z.TAU); x.fill(); }
    x.globalAlpha = 0.55; for (let i = 0; i < 14; i++) { x.beginPath(); const yy = R() * s; x.moveTo(0, yy); x.lineTo(s, yy + (R() - 0.5) * 30); x.lineWidth = 0.5 + R() * 1.5; x.strokeStyle = '#000'; x.stroke(); }
    stampCache.set(key, c); return c;
  };

  // ------------------------------------------------------------------ layouts
  const homography = (q) => {      // unit square -> quad (TL, TR, BR, BL), bilinear approximation per point
    return (u, v) => {
      const [a, b, c, d] = q;
      const top = [Z.lerp(a[0], b[0], u), Z.lerp(a[1], b[1], u)], bot = [Z.lerp(d[0], c[0], u), Z.lerp(d[1], c[1], u)];
      return [Z.lerp(top[0], bot[0], v), Z.lerp(top[1], bot[1], v)];
    };
  };
  const layout = (lay, i, n, S, st) => {
    const L = lay || {};
    switch (L.type || 'col') {
      case 'col': {
        const per = L.per || 99, col = Math.floor(i / per), k = i % per;
        return [L.x - col * (L.gap || 1.25) * st.size, L.y + k * (L.pitch || 1.08) * st.size, L.rot || 0, 1];
      }
      case 'row': {
        const per = L.per || 99, row = Math.floor(i / per), k = i % per, cnt = Math.min(per, n - row * per);
        const sp = (L.spacing || 1.04) * st.size, w = (cnt - 1) * sp;
        const x0 = L.align === 'left' ? L.x : L.align === 'right' ? L.x - w : L.x - w / 2;
        return [x0 + k * sp, L.y + row * (L.gap || 1.3) * st.size, L.rot || 0, 1];
      }
      case 'path': {
        const pts = L.pts, a0 = L.a0 ?? 0, a1 = L.a1 ?? 1;
        const u = n <= 1 ? (a0 + a1) / 2 : Z.lerp(a0, a1, i / (n - 1));
        // arc-length on the polyline
        let tot = 0; const seg = []; for (let j = 1; j < pts.length; j++) { const l = Math.hypot(pts[j][0] - pts[j - 1][0], pts[j][1] - pts[j - 1][1]); seg.push(l); tot += l; }
        let s = u * tot, j = 0; while (j < seg.length - 1 && s > seg[j]) { s -= seg[j]; j++; }
        const f = seg[j] ? s / seg[j] : 0, [x0, y0] = pts[j], [x1, y1] = pts[j + 1] || pts[j];
        const rot = L.orient ? Math.atan2(y1 - y0, x1 - x0) + (L.orientOff || 0) : (L.rot || 0);
        const sc = L.scale ? Z.lerp(L.scale[0], L.scale[1], u) : 1;
        return [Z.lerp(x0, x1, f), Z.lerp(y0, y1, f), rot, sc];
      }
      case 'quad': {
        const hm = homography(L.quad), uv = L.grid === 'col' ? [0.5, (i + 0.5) / n] : [(i + 0.5) / n, 0.5];
        const [x, y] = hm(uv[0], uv[1]);
        const [xa] = hm(uv[0] - 0.02, uv[1]), [xb] = hm(uv[0] + 0.02, uv[1]);
        const [, ya] = hm(uv[0], uv[1] - 0.02), [, yb] = hm(uv[0], uv[1] + 0.02);
        return [x, y, L.rot || 0, 1, (xb - xa) / (0.04 * (L.unitW || 1000)), (yb - ya) / (0.04 * (L.unitH || 1000))];
      }
      case 'fn': return L.fn(i, n, S, st);
    }
    return [W / 2, H / 2, 0, 1];
  };

  // ------------------------------------------------------------------ glyph renderer
  const setFont = (ctx, size, sp) => { D.font(ctx, size, sp.fam || 'serif', sp.weight || 400); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; };
  const plain = (ctx, ch, size, sp, alpha = 1, color) => {
    setFont(ctx, size, sp); ctx.globalAlpha *= alpha;
    if (sp.glow) { ctx.shadowColor = sp.glow; ctx.shadowBlur = sp.glowR || 18; }
    if (sp.stroke) { ctx.lineWidth = sp.strokeW || size * 0.06; ctx.strokeStyle = sp.stroke; ctx.lineJoin = 'round'; ctx.strokeText(ch, 0, 0); }
    ctx.fillStyle = color || sp.color || P.ink; ctx.fillText(ch, 0, 0);
    ctx.shadowBlur = 0;
  };

  G.lyric = (ctx, S, sp) => {
    const info = G.lineInfo(sp.line); if (!info) return;
    const t = S.t, from = sp.from ?? 0, to = Math.min(info.chars.length, sp.to ?? info.chars.length), n = to - from;
    if (n <= 0) return;
    const size0 = sp.size || 72, lead = sp.lead ?? 0.1, inDur = sp.inDur ?? 0.35;
    const exitAt = sp.until ?? Math.min(info.end + (sp.hold ?? 0.6), S.shot.t1 - (sp.outDur ?? 0.35) + 0.05);
    const outDur = sp.outDur ?? 0.35, ek = Z.clamp((t - exitAt) / outDur);
    const fxName = sp.fx || 'ink', seed = sp.seed ?? sp.line * 13;
    const st = { size: size0 };
    for (let k = 0; k < n; k++) {
      const i = from + k, ch = info.chars[i], on = info.on[i] + (sp.shift || 0);
      if (sp.skip && sp.skip.includes(i)) continue;
      const a = Z.clamp((t - (on - lead)) / inDur);
      if (a <= 0) continue;
      st.i = i; st.on = on;
      const pos = layout(sp.lay, k, n, S, st);
      let [x, y, rot, sc] = pos; const sx = pos[4] || 1, sy = pos[5] || 1;
      let size = size0 * (sc || 1) * (sp.sizes ? sp.sizes[k] ?? 1 : 1);
      const life = sp.life ? Z.clamp(1 - (t - on - sp.life) / 0.5) : 1;
      if (life <= 0) continue;
      const gs = { a, e: Math.max(ek, 1 - life), on, age: t - on, k, n, i, seed: seed + i * 7 };
      const sp2 = sp.colors ? Object.assign({}, sp, { color: sp.colors[k % sp.colors.length] }) : sp;
      ctx.save();
      ctx.translate(x, y); if (rot) ctx.rotate(rot); if (sx !== 1 || sy !== 1) ctx.scale(Math.max(0.05, sx), Math.max(0.05, sy));
      FX[fxName](ctx, ch, size, sp2, gs, S);
      ctx.restore();
    }
  };
  G.lyrics = (ctx, S, z) => { for (const sp of S.args.lyrics || []) if ((sp.z || 'front') === z) G.lyric(ctx, S, sp); };

  // ------------------------------------------------------------------ effects (each draws one glyph at the origin)
  const FX = {
    // ink settling into paper: blur -> sharp, slight spread
    ink(ctx, ch, size, sp, g) {
      const a = E.outCubic(g.a), e = g.e; if (e >= 1) return;
      const blur = (1 - a) * size * 0.08 + e * size * 0.06;
      if (blur > 0.4) ctx.filter = `blur(${blur.toFixed(1)}px)`;
      ctx.scale(1 + 0.06 * (1 - a), 1 + 0.06 * (1 - a));
      plain(ctx, ch, size, sp, a * (1 - e));
      ctx.filter = 'none';
    },
    // snow gathers into the glyph, then blows away on the wind
    snow(ctx, ch, size, sp, g, S) {
      const m = G.glyphMask(ch, sp.fam || 'serif', sp.weight || 500), pts = m.inside, N = Math.min(pts.length, sp.points || 220);
      const a = E.inOutCubic(Z.clamp(g.a)), e = g.e, wind = sp.wind ?? 1, t = S.t;
      ctx.save();
      for (let j = 0; j < N; j++) {
        const [u, v] = pts[j], tx = u * size * 1.2, ty = v * size * 1.2;
        const sx = tx + Z.rnds(j, g.seed) * size * 2.2 - wind * size * 1.2, sy = ty - size * (1.4 + 1.6 * Z.rnd(j, g.seed + 1));
        let px = Z.lerp(sx, tx, a), py = Z.lerp(sy, ty, a);
        if (e > 0) { const ee = E.inQuad(e); px += wind * ee * size * (2 + 3 * Z.rnd(j, g.seed + 2)); py += ee * size * (Z.rnds(j, g.seed + 3) * 1.2 - 0.4); }
        px += Math.sin(t * 2 + j) * 1.2;
        const r = (sp.flake || 1.6) * (0.6 + Z.rnd(j, g.seed + 4)) * size / 90;
        ctx.globalAlpha = (0.55 + 0.45 * a) * (1 - e * 0.9);
        ctx.beginPath(); ctx.arc(px, py, r, 0, Z.TAU); ctx.fillStyle = '#FFFFFF'; ctx.fill();
        ctx.lineWidth = 0.6; ctx.strokeStyle = 'rgba(110,128,160,0.55)'; ctx.stroke();
      }
      ctx.restore();
      const solid = Z.clamp((g.a - 0.75) / 0.25) * (1 - e);
      if (solid > 0) { ctx.save(); plain(ctx, ch, size, sp, solid * (sp.solid ?? 0.85)); ctx.restore(); }
    },
    // frost: pale glyph with a slate rim and crystals growing out of its edges
    frost(ctx, ch, size, sp, g, S) {
      const a = E.outCubic(g.a), e = g.e; if (e >= 1) return;
      ctx.save(); plain(ctx, ch, size, Object.assign({}, sp, { stroke: 'rgba(96,114,146,0.75)', strokeW: size * 0.035 }), a * (1 - e), sp.color || '#F7FAFD'); ctx.restore();
      const m = G.glyphMask(ch, sp.fam || 'serif', sp.weight || 400), N = Math.min(m.edge.length, 70);
      ctx.save(); ctx.strokeStyle = `rgba(120,140,170,${0.6 * (1 - e)})`; ctx.lineWidth = 1; ctx.lineCap = 'round';
      for (let j = 0; j < N; j++) {
        const [u, v] = m.edge[j], gk = Z.clamp(a * 1.4 - Z.rnd(j, g.seed) * 0.6); if (gk <= 0) continue;
        const x = u * size * 1.2, y = v * size * 1.2, an = Math.atan2(v, u) + Z.rnds(j, g.seed + 1) * 0.8, L = size * 0.08 * gk * (0.5 + Z.rnd(j, g.seed + 2));
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + Math.cos(an) * L, y + Math.sin(an) * L);
        ctx.moveTo(x + Math.cos(an) * L * 0.5, y + Math.sin(an) * L * 0.5); ctx.lineTo(x + Math.cos(an + 0.7) * L * 0.85, y + Math.sin(an + 0.7) * L * 0.85);
        ctx.stroke();
      }
      ctx.restore();
      void S;
    },
    // silver beads (the veil's embroidery): the glyph as a field of tiny beads that catch the light
    beads(ctx, ch, size, sp, g, S) {
      const m = G.glyphMask(ch, sp.fam || 'serif', sp.weight || 600), pts = m.inside, N = Math.min(pts.length, sp.points || 260);
      const e = g.e; if (e >= 1) return;
      for (let j = 0; j < N; j++) {
        const show = Z.clamp(g.a * 1.6 - Z.rnd(j, g.seed) * 0.6); if (show <= 0) continue;
        const [u, v] = pts[j], x = u * size * 1.2, y = v * size * 1.2, r = size / 70 * (0.8 + 0.5 * Z.rnd(j, g.seed + 1));
        const tw = 0.5 + 0.5 * Math.sin(S.t * 5 + j * 2.3);
        const gr = ctx.createRadialGradient(x - r * 0.3, y - r * 0.3, 0, x, y, r);
        gr.addColorStop(0, '#FFFFFF'); gr.addColorStop(0.6, `rgba(196,204,216,${0.95})`); gr.addColorStop(1, 'rgba(120,132,150,0.9)');
        ctx.globalAlpha = show * (1 - e); ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(x, y, r, 0, Z.TAU); ctx.fill();
        if (tw > 0.97) { ctx.save(); ctx.translate(x, y); G.sparkle(ctx, S.t, { n: 1, size: r * 6, area: [-1, -1, 1, 1], alpha: 0.9, seed: j }); ctx.restore(); }
      }
    },
    // rubber stamp in rouge: slams in, rough edges, a little rotation
    stamp(ctx, ch, size, sp, g) {
      const k = Z.clamp(g.a), e = g.e; if (e >= 1) return;
      const s = Z.lerp(1.5, 1, E.outExpo(k)), c = stampGlyph(ch, sp.color || P.carmine, sp.fam || 'brush');
      ctx.rotate((Z.rnds(g.i, g.seed) * 0.12)); ctx.scale(s, s); ctx.globalAlpha *= Math.min(1, k * 3) * (sp.alpha ?? 0.9) * (1 - e);
      ctx.globalCompositeOperation = sp.comp || 'multiply';
      ctx.drawImage(c, -size * 0.62, -size * 0.62, size * 1.24, size * 1.24);
    },
    // smeared rouge: the glyph dragged sideways like a fingertip of lipstick
    smear(ctx, ch, size, sp, g) {
      const a = E.outCubic(g.a), e = g.e; if (e >= 1) return;
      const len = (sp.smear || 0.6) * size * (0.3 + 0.7 * a);
      for (let j = 6; j >= 0; j--) { ctx.save(); ctx.translate(-len * j / 6, 0); plain(ctx, ch, size, sp, (j ? 0.12 : 1) * a * (1 - e)); ctx.restore(); }
    },
    // cast shadow on a wall: skewed, translucent, multiplied
    shadow(ctx, ch, size, sp, g) {
      const a = E.outCubic(g.a), e = g.e; if (e >= 1) return;
      ctx.transform(1, 0, sp.skew ?? -0.55, sp.sy ?? 1, 0, 0);
      ctx.globalCompositeOperation = 'multiply'; ctx.filter = `blur(${(sp.soft ?? 2).toFixed(1)}px)`;
      plain(ctx, ch, size, sp, a * (sp.alpha ?? 0.45) * (1 - e), sp.color || '#5A6880');
      ctx.filter = 'none';
    },
    // pressed into snow: a soft hollow (shadow below-right, highlight above-left), low contrast
    emboss(ctx, ch, size, sp, g) {
      const a = E.outCubic(g.a), e = g.e; if (e >= 1) return;
      const al = a * (1 - e), s = sp.alpha ?? 1, d = Math.max(2, size * 0.035);
      ctx.save(); ctx.translate(d, d * 1.2); ctx.filter = 'blur(2px)'; plain(ctx, ch, size, sp, Math.min(1, 0.55 * s) * al, '#5F7092'); ctx.restore();
      ctx.save(); ctx.translate(-d * 0.6, -d * 0.6); plain(ctx, ch, size, sp, Math.min(1, 0.9 * s) * al, '#FFFFFF'); ctx.restore();
      ctx.save(); plain(ctx, ch, size, sp, Math.min(1, 0.6 * s) * al, sp.color || '#C3D0E3'); ctx.restore();
      ctx.filter = 'none';
    },
    // falls after appearing (gravity + spin), fading as it drops out of view
    fall(ctx, ch, size, sp, g) {
      const a = E.outCubic(g.a), d = Math.max(0, g.age - (sp.delay ?? 0.35)), gr = sp.gravity ?? 900;
      ctx.translate(Z.rnds(g.i, g.seed) * 60 * d, 0.5 * gr * d * d * (sp.slow ?? 1));
      ctx.rotate(Z.rnds(g.i, g.seed + 1) * 2.5 * d);
      plain(ctx, ch, size, sp, a * (1 - g.e) * Z.clamp(1 - d / (sp.life ?? 2.2)));
    },
    // rises with a little sway (petals / ash)
    float(ctx, ch, size, sp, g, S) {
      const a = E.outCubic(g.a), d = Math.max(0, g.age);
      ctx.translate(Math.sin(S.t * 1.3 + g.i) * size * 0.15 + (sp.drift || 0) * d, -(sp.rise ?? 60) * d);
      ctx.rotate(Math.sin(S.t * 0.9 + g.i * 1.7) * 0.12);
      plain(ctx, ch, size, sp, a * (1 - g.e) * Z.clamp(1 - d / (sp.life ?? 4)));
    },
    // sprouts roots from its base while it sinks a little into the mud
    roots(ctx, ch, size, sp, g) {
      const a = E.outCubic(g.a), e = g.e; if (e >= 1) return;
      const R = Z.rng(g.seed), grow = Z.clamp(g.age / (sp.grow ?? 1.4));
      ctx.save(); ctx.translate(0, size * 0.1 * grow); plain(ctx, ch, size, sp, a * (1 - e)); ctx.restore();
      ctx.save(); ctx.strokeStyle = sp.rootColor || 'rgba(244,236,222,0.9)'; ctx.lineCap = 'round'; ctx.globalAlpha *= 1 - e;
      for (let r = 0; r < 4; r++) {
        let x = R.range(-0.3, 0.3) * size, y = size * 0.42, an = Math.PI / 2 + R.range(-0.6, 0.6), w = 2.4;
        const steps = Math.floor(10 * grow);
        ctx.beginPath(); ctx.moveTo(x, y);
        for (let k = 0; k < steps; k++) { an += R.range(-0.4, 0.4); x += Math.cos(an) * size * 0.06; y += Math.sin(an) * size * 0.06; ctx.lineTo(x, y); }
        ctx.lineWidth = w; ctx.stroke();
      }
      ctx.restore();
    },
    // pops open (like the bloom): overshoot, wobble
    pop(ctx, ch, size, sp, g, S) {
      const k = Z.clamp(g.a * 1.2), e = g.e; if (e >= 1) return;
      const s = E.outBack(k, 2.6);
      ctx.rotate(Math.sin(S.t * 9 + g.i) * 0.06 * (1 - k * 0.5)); ctx.scale(s, s);
      plain(ctx, ch, size, sp, Math.min(1, k * 2) * (1 - e));
    },
    // seeps out of a point (the crushed dye) and drips down
    bleed(ctx, ch, size, sp, g) {
      const a = E.outCubic(g.a), e = g.e; if (e >= 1) return;
      ctx.translate(0, (sp.drip ?? 40) * Math.max(0, g.age));
      ctx.scale(0.5 + 0.5 * a, 0.5 + 0.7 * a);
      ctx.filter = `blur(${((1 - a) * 6).toFixed(1)}px)`;
      plain(ctx, ch, size, sp, a * (1 - e), sp.color || P.carmine); ctx.filter = 'none';
    },
    // streams off behind a moving figure: motion-smeared, thinning out
    trail(ctx, ch, size, sp, g) {
      const a = E.outCubic(g.a), e = g.e; if (e >= 1) return;
      const sm = Math.min(5, Math.floor(g.age * 6));
      for (let j = sm; j >= 0; j--) { ctx.save(); ctx.translate(j * size * 0.12 * (sp.dir || 1), 0); plain(ctx, ch, size, sp, (j ? 0.1 : 1) * a * (1 - e)); ctx.restore(); }
    },
    // old paint on a wall: multiplied, slightly broken
    wall(ctx, ch, size, sp, g) {
      const a = E.outCubic(g.a), e = g.e; if (e >= 1) return;
      ctx.globalCompositeOperation = 'multiply'; ctx.filter = 'blur(0.8px)';
      plain(ctx, ch, size, sp, a * (sp.alpha ?? 0.6) * (1 - e), sp.color || '#6B7690');
      ctx.filter = 'none';
    },
    // drifts down like a snowflake from above and comes to rest at its place
    settle(ctx, ch, size, sp, g, S) {
      const fallT = sp.fallT ?? 1.6, k = Z.clamp(g.age + (sp.lead ?? 0.1)) / fallT, kk = E.outQuad(Z.clamp(k));
      const dy = -(sp.drop ?? 520) * (1 - kk), dx = Math.sin(S.t * 1.4 + g.i) * 30 * (1 - kk);
      ctx.translate(dx, dy); ctx.rotate(Math.sin(S.t + g.i) * 0.3 * (1 - kk));
      plain(ctx, ch, size, sp, Math.min(1, g.a * 2) * (1 - g.e));
    },
    // seen through a sheer curtain: soft, low contrast, swaying
    veil(ctx, ch, size, sp, g, S) {
      const a = E.outCubic(g.a), e = g.e; if (e >= 1) return;
      ctx.translate(Math.sin(S.t * 0.9 + g.i * 0.6) * size * 0.08, 0);
      ctx.filter = `blur(${(sp.soft ?? 3).toFixed(1)}px)`;
      plain(ctx, ch, size, sp, a * (sp.alpha ?? 0.55) * (1 - e));
      ctx.filter = 'none';
    },
    // carried off by the wind after it is sung
    blow(ctx, ch, size, sp, g, S) {
      const a = E.outCubic(g.a), d = Math.max(0, g.age - (sp.delay ?? 0.25));
      ctx.translate((sp.wind ?? 420) * d * d * 0.9 + Math.sin(S.t * 3 + g.i) * 6, -(sp.lift ?? 90) * d + Math.sin(d * 4 + g.i) * 20);
      ctx.rotate((sp.spin ?? 0.9) * d * (g.i % 2 ? 1 : -1));
      plain(ctx, ch, size, sp, a * (1 - g.e) * Z.clamp(1 - d / (sp.life2 ?? 2.4)));
    },
    // the same glyph repeated row after row toward a vanishing point (desks, stamps)
    recede(ctx, ch, size, sp, g) {
      const a = E.outCubic(g.a), e = g.e; if (e >= 1) return;
      const n = sp.copies || 7, [vx, vy] = (typeof sp.toward === 'function' ? sp.toward(g.k) : sp.toward) || [0, -300], f = sp.shrink ?? 0.72;
      for (let j = n - 1; j >= 0; j--) {
        const s2 = Math.pow(f, j), kk = j / n;
        ctx.save(); ctx.translate(vx * (1 - s2), vy * (1 - s2)); ctx.scale(s2, s2);
        plain(ctx, ch, size, sp, a * (1 - e) * (j ? 0.55 * (1 - kk) : 1));
        ctx.restore();
      }
    },
    // a snowflake that falls into place and melts into carmine
    flake(ctx, ch, size, sp, g, S) {
      const fallT = sp.fallT ?? 1.0, k = Z.clamp((g.age + (sp.lead ?? 0.1)) / fallT), kk = E.inQuad(k);
      const dy = -(sp.drop ?? 600) * (1 - kk), dx = Math.sin(S.t * 2 + g.i) * 20 * (1 - kk);
      ctx.translate(dx, dy);
      const melt = Z.clamp((k - 0.95) / 0.05) * Z.clamp((g.age + (sp.lead ?? 0.1) - fallT) / 0.5);
      if (melt < 1) { ctx.save(); plain(ctx, ch, size, Object.assign({}, sp, { stroke: 'rgba(110,128,160,0.8)', strokeW: size * 0.05 }), (1 - melt) * (1 - g.e), '#FFFFFF'); ctx.restore(); }
      if (melt > 0) { ctx.save(); ctx.filter = `blur(${((1 - melt) * 4).toFixed(1)}px)`; plain(ctx, ch, size, sp, melt * (1 - g.e), sp.color || P.carmine); ctx.restore(); ctx.filter = 'none'; }
    },
    // very small, very light — barely noticed
    whisper(ctx, ch, size, sp, g) { plain(ctx, ch, size, sp, E.outCubic(g.a) * (1 - g.e) * (sp.alpha ?? 0.7)); },
  };
  G.TYPE_FX = FX;
})();
