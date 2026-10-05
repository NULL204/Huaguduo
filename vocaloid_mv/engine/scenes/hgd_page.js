/* engine/scenes/hgd_page.js — 花骨朵: the herbarium sheet (the film's master frame: it opens and closes the film) and the
 * plain type cards.
 *
 *   hPage  mode 'intro'    s01  black → rice paper; a carmine drop blooms; the bud writes itself as a botanical plate;
 *                               the specimen label types in.  args: drop, pin, tape, stem [t0,t1], bud [t0,t1],
 *                               hatch [t0,t1], wash [t0,t1], label [t0,t1]
 *          mode 'stamp'    s02  the stop (frame holds), seal 「待开」 at args.stamp, glide to the bud, heartbeat at args.pulse
 *          mode 'photo'    s28  an old sepia photograph of the sheet; the line handwritten on its border   args: line
 *          mode 'glassine' s29  the plate under a milky glassine sheet that peels back                   args: peel [t0,t1]
 *          mode 'end'      s47  the same sheet with the pressed bloom; seal + credits; a silverfish     args: seal
 *   hType  mode 'title' s03 · 'want' s12 · 'want2' s18 · 'dont' s27 · 'dont2' s32                         args: line
 *
 * One shared composition (sheet()) so the page is the same object every time it appears.
 */
(() => {
  'use strict';
  const Z = window.Z, D = Z.draw, E = Z.ease, G = Z.HGD, C = G.C;
  const W = 1920, H = 1080, TAU = Math.PI * 2;

  // ------------------------------------------------------------------ the specimen and its furniture
  const BUD = { x: 560, y: 1110, len: 930, size: 220, nod: 0.84, lean: 0.07 };
  const LABEL = { x: 1150, y: 628, w: 600, row: 46 };
  const ROWS_BUD = () => [['科', '罂粟科 Papaveraceae'], ['种', '虞美人 Papaver rhoeas'], ['状态', '花骨朵（未开）', C.carmine], ['采集', '晚春']];
  const ROWS_END = () => [['科', '罂粟科 Papaveraceae'], ['种', '虞美人 Papaver rhoeas'], ['状态', '已开', C.carmine], ['采集', G.part(41, 2, 6) || '—']];
  const lerp = Z.lerp, clamp = Z.clamp, inv = Z.inv;
  const win = (t, w) => clamp((t - w[0]) / (w[1] - w[0]));

  // stem only (write-on), same geometry as G.bud: ink outline stroke + paper fill + bristles inside the grown part
  function drawStem(ctx, o, prog, P) {
    const st = G.stemPoints(o), size = o.size, lw = Math.max(1.4, size * 0.016), sw = size * 0.085;
    if (prog <= 0) return st;
    G.vstroke(ctx, st.pts, u => sw * (1.25 - 0.45 * u) + lw * 2, P.line, prog);
    G.vstroke(ctx, st.pts, u => sw * (1.25 - 0.45 * u), P.stem, prog);
    ctx.save(); ctx.strokeStyle = P.line; ctx.lineWidth = Math.max(0.8, lw * 0.55); ctx.lineCap = 'round'; ctx.beginPath();
    const n = Math.floor(st.pts.length * prog);
    for (let i = 3; i < n; i += 2) {
      if (Z.rnd(i, 71) > (o.hairs ?? 1)) continue;
      const [px, py] = st.pts[i], a = st.ang[i], side = (i >> 1) % 2 ? 1 : -1, hl = size * (0.06 + 0.05 * Z.rnd(i, 72));
      const ha = a + side * (1.05 + 0.25 * Z.rnds(i, 73)) - side * 0.35;
      const bx = px + Math.cos(a + side * Math.PI / 2) * sw * 0.55, by = py + Math.sin(a + side * Math.PI / 2) * sw * 0.55;
      ctx.moveTo(bx, by); ctx.quadraticCurveTo(bx + Math.cos(ha) * hl * 0.6, by + Math.sin(ha) * hl * 0.6, bx + Math.cos(ha - side * 0.25) * hl, by + Math.sin(ha - side * 0.25) * hl);
    }
    ctx.stroke(); ctx.restore();
    return st;
  }
  // bud head drawn into an offscreen (cached per palette / open / sway-free pose), revealed with a clock wipe
  const headCache = new Map();
  function budHead(pal, open, hairs) {
    const key = pal + '|' + open.toFixed(3) + '|' + hairs; let c = headCache.get(key); if (c) return c;
    c = Z.canvas(W, H); const x = c.getContext('2d');
    G.bud(x, Object.assign({}, BUD, { pal, open, hairs, stem: false, t: 0, sway: 0 }));
    headCache.set(key, c); return c;
  }
  const budCenter = (() => { let c = null; return () => c || (c = (() => { const st = G.stemPoints(BUD); return [st.tip[0] + Math.cos(st.th) * BUD.size * 0.5, st.tip[1] + Math.sin(st.th) * BUD.size * 0.5]; })()); })();

  function pin(ctx, x, y, k) {                                   // a red-headed insect pin, dropping in
    if (k <= 0) return;
    const e = E.outBack(clamp(k * 2.2), 2.2), yy = y - (1 - e) * 60;
    ctx.save(); ctx.globalAlpha *= clamp(k * 4);
    ctx.fillStyle = 'rgba(27,20,32,0.18)'; ctx.beginPath(); ctx.ellipse(x + 10, y + 8, 14, 6, 0.3, 0, TAU); ctx.fill();
    ctx.strokeStyle = '#6E6A70'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x, yy); ctx.lineTo(x + 4, yy + 26); ctx.stroke();
    const g = ctx.createRadialGradient(x - 4, yy - 4, 1, x, yy, 11); g.addColorStop(0, '#FF8FA0'); g.addColorStop(0.4, C.carmine); g.addColorStop(1, C.deep);
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, yy, 10, 0, TAU); ctx.fill();
    ctx.restore();
  }

  // the whole sheet. o: { t, paper, specimen 'bud'|'bloom', p:{ drop, marks, number, stem, head, hatch, wash, tape, pin, label, seal, sealText, rows } }
  function sheet(ctx, o) {
    const t = o.t, p = o.p, tq = Z.quant(t, 12);
    G.drawPaper(ctx, o.paper || 'xuan');
    // the carmine drop: a falling bead, then a soft stain that stays as a watermark behind the specimen
    const [cx, cy] = budCenter();
    if (p.drop != null) {
      const fallT = 0.32, dt = t - (p.drop - fallT), sx = cx - 150, sy = cy + 170;
      if (dt > 0 && dt < fallT) { const k = dt / fallT, yy = lerp(-40, sy, E.inQuad(k)); ctx.fillStyle = C.carmine; ctx.beginPath(); ctx.ellipse(sx, yy, 9, 14, 0, 0, TAU); ctx.fill(); }
      if (t >= p.drop) {
        const u = t - p.drop;
        ctx.save(); ctx.globalCompositeOperation = 'multiply';
        G.bleed(ctx, sx, sy, 120, { prog: clamp(u / 3.0), seed: 17, color: '#EDC7C9', a: 0.4, edge: 0.3 });   // the halo soaks out slowly
        ctx.restore();
        ctx.save(); ctx.globalAlpha = 0.92; G.splat(ctx, sx, sy, 24, { prog: clamp(u / 0.18), seed: 41, color: C.carmine, n: 9, reach: 1.6 }); ctx.restore();
      }
    }
    // sheet furniture
    if ((p.marks ?? 1) > 0) { ctx.save(); ctx.globalAlpha *= p.marks ?? 1; G.sheetMarks(ctx, { alpha: 0.5 }); ctx.restore(); }
    if ((p.number ?? 1) > 0) {
      const s = 'No.0507', n = Math.round((p.number ?? 1) * s.length);
      ctx.save(); G.font(ctx, 38, 'dot', 400); ctx.fillStyle = Z.rgba(C.ink, 0.78); ctx.textBaseline = 'top'; ctx.fillText(s.slice(0, n), 118, 100);
      G.font(ctx, 28, 'song', 500); ctx.fillStyle = Z.rgba(C.ink, 0.6 * clamp(((p.number ?? 1) - 0.5) * 2)); ctx.fillText('Papaver rhoeas L.', 118, 150);
      G.font(ctx, 36, 'hand', 400); ctx.fillStyle = Z.rgba(C.carmine, 0.8 * clamp(((p.number ?? 1) - 0.7) * 3.3)); ctx.fillText('虞美人 · 花骨朵', 118, 190);
      ctx.restore();
    }
    // specimen
    if (o.specimen === 'bloom') {
      const st = G.stemPoints(Object.assign({}, BUD, { nod: 0.18, len: 520 }));
      ctx.save(); ctx.globalAlpha *= 0.95; drawStem(ctx, Object.assign({}, BUD, { nod: 0.18, len: 520 }), 1, G.BUDPAL.print); ctx.restore();
      ctx.save(); ctx.globalCompositeOperation = 'multiply';
      ctx.translate(st.tip[0], st.tip[1] - 60); ctx.scale(1, 0.9);
      G.poppy(ctx, { x: 0, y: 0, r: 250, open: 1, pal: 'pressed', seed: 6, a0: 0.5, t: 0, alpha: 0.92 });
      ctx.restore();
    } else {
      const P = G.BUDPAL.print;
      drawStem(ctx, BUD, p.stem ?? 1, P);
      const head = p.head ?? 1, sketch = p.sketch ?? (head > 0 ? 1 : 0);
      const lineArt = budHead('print', 0.0, 0), done = budHead('print', 0.11, 1), blush = budHead('blush', 0.11, 1);
      if (sketch > 0 && head < 1) { ctx.save(); ctx.globalAlpha = 0.2 * sketch; ctx.drawImage(lineArt, 0, 0); ctx.restore(); }   // pencil under-drawing
      if (head > 0) {
        ctx.save();
        if (head < 1) {                                        // clock wipe around the bud centre: the pen inks it round
          ctx.beginPath(); ctx.moveTo(cx, cy); ctx.arc(cx, cy, 500, -Math.PI / 2, -Math.PI / 2 + TAU * head); ctx.closePath(); ctx.clip();
        }
        const hk = clamp(p.hatch ?? 1), wk = clamp(p.wash ?? 1);
        if (hk < 1) ctx.drawImage(lineArt, 0, 0);
        if (hk > 0 && wk < 1) { ctx.globalAlpha = hk; ctx.drawImage(done, 0, 0); }
        if (wk > 0) { ctx.globalAlpha = wk; ctx.drawImage(blush, 0, 0); }   // the wash: the hidden red seeps into the sepals
        ctx.restore();
      }
    }
    // washi tape over the stem + a pin by the label
    if ((p.tape ?? 1) > 0) {
      const bloomStem = o.specimen === 'bloom', st = G.stemPoints(bloomStem ? Object.assign({}, BUD, { nod: 0.18, len: 520 }) : BUD), k = E.outBack(clamp((p.tape ?? 1) * 1.6), 1.4);
      for (const [i, rot, seed] of (bloomStem ? [[12, -0.5, 3], [30, 0.42, 5]] : [[18, -0.5, 3], [40, 0.42, 5]])) {
        const [tx, ty] = st.pts[i];
        ctx.save(); ctx.globalAlpha *= clamp((p.tape ?? 1) * 3); G.tape(ctx, tx, ty - (1 - k) * 30, 150, 38, rot, 'rgba(226,206,180,0.82)', seed); ctx.restore();
      }
    }
    pin(ctx, 1772, 128, p.pin ?? 1);
    if ((p.label ?? 1) > 0) {
      ctx.save(); ctx.globalAlpha *= clamp((p.label ?? 1) * 6);
      ctx.fillStyle = 'rgba(27,20,32,0.10)'; ctx.fillRect(LABEL.x + 8, LABEL.y + 10, LABEL.w, LABEL.row * 5.6 + 20);
      G.label(ctx, LABEL.x, LABEL.y, p.rows || ROWS_BUD(), { k: p.label ?? 1, no: 'No.0507', w: LABEL.w, row: LABEL.row, title: '植物标本 · 花骨朵' });
      ctx.restore();
    }
    if (p.sealK != null && p.sealK > -0.12) G.seal(ctx, LABEL.x + LABEL.w - 92, LABEL.y + LABEL.row * 4.15, p.sealPx || 120, p.sealText || '待开', { k: p.sealK, rot: -0.08, seed: 9 });
    return { cx, cy };
  }

  // per-shot camera about a point
  const camAt = (ctx, z, px, py, rot = 0) => { ctx.translate(W / 2, H / 2); ctx.rotate(rot); ctx.scale(z, z); ctx.translate(-px, -py); };

  // ------------------------------------------------------------------ hPage
  function intro(ctx, S) {
    const a = S.args, t = S.t, tq = S.tq;
    const A = { drop: a.drop ?? 0.55, pin: a.pin ?? 3.37, tape: a.tape ?? 7.37, stem: a.stem || [4.10, 6.6], bud: a.bud || [6.6, 7.4],
      hatch: a.hatch || [7.4, 8.5], wash: a.wash || [8.5, 9.5], label: a.label || [8.1, 10.8] };
    const tt = Math.min(t, a.freezeAt ?? 1e9);                 // the stop holds the frame
    const qt = Math.min(tq, a.freezeAt ?? 1e9);
    const p = {
      drop: A.drop, marks: clamp((tt - 1.0) / 0.8), number: clamp((qt - 1.6) / 1.4), stem: E.inOutSine(win(qt, A.stem)),
      head: win(qt, A.bud), hatch: win(qt, A.hatch), wash: win(tt, A.wash), tape: clamp((tt - A.tape) / 0.35), pin: clamp((tt - A.pin) / 0.4),
      label: win(qt, A.label),
    };
    ctx.save();
    const z = 1 + 0.06 * E.inOutSine(clamp(tt / 11));
    camAt(ctx, z, 960, 540);
    sheet(ctx, { t: tt, p });
    ctx.restore();
    // fade up from black
    const f = 1 - clamp(t / 0.5); if (f > 0) D.fill(ctx, '#000', f);
    // the pin's tiny jolt is felt by the paper: a 2-frame nudge
    return p;
  }
  function stamp(ctx, S) {
    const a = S.args, t = S.t, T = a.stamp ?? 11.36, pulseT = a.pulse ?? 13.56, hold0 = S.shot.t0;
    const frozen = t < T;                                      // 11.00–11.36: the frame holds (only grain moves)
    const tt = frozen ? hold0 : t;
    const p = { drop: 0.55, marks: 1, number: 1, stem: 1, head: 1, hatch: 1, wash: 1, tape: 1, pin: 1, label: 1, sealK: t - T, sealText: '待开', sealPx: 128 };
    // glide label -> bud close-up after the stamp
    const [cx, cy] = budCenter();
    const g = G.EZ.io(clamp((t - (T + 0.35)) / 1.9));
    const z = lerp(1.06, 1.9, g), px = lerp(960, cx + 40, g), py = lerp(540, cy + 30, g);
    let jx = 0, jy = 0;
    if (t >= T) { const u = t - T; jx = G.damp(u, 7, 22, 9); jy = G.damp(u, 9, 20, 7); }
    ctx.save(); ctx.translate(jx, jy); camAt(ctx, z, px, py);
    sheet(ctx, { t: tt, p });
    // heartbeat: the slit swells and glows once
    const hb = Math.exp(-Math.pow((t - pulseT - 0.12) / 0.18, 2));
    if (hb > 0.01) {
      ctx.save(); ctx.globalAlpha = 0.9 * hb; ctx.drawImage(budHead('blush', 0.11 + 0.08 * hb, 1), 0, 0); ctx.restore();
      D.glow(ctx, cx, cy, 120 + 60 * hb, C.rouge, 0.18 * hb);
    }
    ctx.restore();
  }
  // the photo: the sheet rendered small once, sepia-toned, as an old print with a white border
  let photoC = null;
  function photoArt() {
    if (photoC) return photoC;
    const big = Z.canvas(W, H), bx = big.getContext('2d');
    sheet(bx, { t: 20, p: { drop: 0.55, marks: 1, number: 1, stem: 1, head: 1, hatch: 1, wash: 1, tape: 1, pin: 1, label: 1, sealK: 5, sealText: '待开', sealPx: 128 } });
    const w = 1120, h = 630; photoC = Z.canvas(w, h); const x = photoC.getContext('2d');
    x.filter = 'sepia(0.85) contrast(0.92) brightness(1.04) saturate(0.8)'; x.drawImage(big, 0, 0, w, h); x.filter = 'none';
    const g = x.createRadialGradient(w / 2, h / 2, h * 0.3, w / 2, h / 2, h * 0.85); g.addColorStop(0, 'rgba(60,40,20,0)'); g.addColorStop(1, 'rgba(60,40,20,0.45)');
    x.fillStyle = g; x.fillRect(0, 0, w, h);
    const R = Z.rng(77); x.strokeStyle = 'rgba(255,248,235,0.35)'; x.lineWidth = 1;            // scratches + dust
    for (let i = 0; i < 26; i++) { const sx = R() * w, sy = R() * h; x.beginPath(); x.moveTo(sx, sy); x.lineTo(sx + R.range(-30, 30), sy + R.range(20, 120)); x.stroke(); }
    x.fillStyle = 'rgba(40,28,16,0.35)'; for (let i = 0; i < 90; i++) { x.beginPath(); x.arc(R() * w, R() * h, R() * 1.8, 0, TAU); x.fill(); }
    return photoC;
  }
  function photo(ctx, S) {
    const a = S.args, t = S.t, lt = S.lt, line = a.line ?? 24;
    G.drawPaper(ctx, 'aged', 0);
    D.vgrad(ctx, [[0, 'rgba(40,28,20,0.25)'], [1, 'rgba(40,28,20,0.5)']], 1, 'multiply');
    const art = photoArt(), pw = art.width, ph = art.height, bw = 34, bb = 150;
    ctx.save();
    const drift = lt * 0.6;
    ctx.translate(W / 2 + 10 - drift * 6, H / 2 - 8); ctx.rotate(-0.045 + drift * 0.004); ctx.scale(1 + lt * 0.008, 1 + lt * 0.008);
    const x0 = -pw / 2 - bw, y0 = -ph / 2 - bw - 30, fw = pw + bw * 2, fh = ph + bw + bb;
    ctx.fillStyle = 'rgba(30,18,10,0.35)'; ctx.fillRect(x0 + 16, y0 + 20, fw, fh);                          // shadow
    ctx.fillStyle = '#F3EBDD'; ctx.fillRect(x0, y0, fw, fh);
    ctx.drawImage(art, x0 + bw, y0 + bw);
    // the print yellows while we look at it
    const age = clamp(lt / 2.6);
    ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = `rgba(214,170,110,${0.18 + 0.35 * age})`; ctx.fillRect(x0, y0, fw, fh); ctx.restore();
    ctx.save(); ctx.globalAlpha = 0.25 * age; ctx.fillStyle = '#F3EBDD'; ctx.fillRect(x0 + bw, y0 + bw, pw, ph); ctx.restore();   // fading
    // handwritten caption on the border
    const ct = G.CT(line), glyphs = G.glyphs(line);
    G.text(ctx, glyphs.join(''), x0 + fw / 2, y0 + fh - bb / 2 + 6, { size: 74, fam: 'hand', weight: 400, color: '#3A2A22', spacing: 0.08,
      reveal: G.sung(line, t, 0.1, 0.35), anim: 'ink' });
    G.font(ctx, 20, 'dot', 400); ctx.fillStyle = 'rgba(58,42,34,0.55)'; ctx.textAlign = 'right'; ctx.textBaseline = 'alphabetic';
    ctx.fillText('No.0507', x0 + fw - 26, y0 + fh - 18);
    ctx.restore();
    G.vignette(ctx, 0.35, '30,18,10');
  }
  function glassine(ctx, S) {
    const a = S.args, t = S.t, lt = S.lt, pk = G.EZ.io(win(t, a.peel || [99.1, 101.5]));
    const [cx, cy] = budCenter();
    ctx.save(); camAt(ctx, 1.55 + 0.04 * clamp(lt / 4), cx + 220, cy + 80);
    sheet(ctx, { t: 20, p: { drop: 0.55, marks: 1, number: 1, stem: 1, head: 1, hatch: 1, wash: 1, tape: 1, pin: 1, label: 1, sealK: 5, sealText: '待开', sealPx: 128 } });
    ctx.restore();
    // fold line moves from the bottom-right corner toward the top-left; d = distance of the fold from the corner along the diagonal
    const dirx = -0.83, diry = -0.56, L = Math.hypot(W, H) * 1.05, d = pk * L;
    const ox = W, oy = H, fx = ox + dirx * d, fy = oy + diry * d;          // point on the fold line; normal = (dirx, diry)
    const side = (x, y) => (x - fx) * dirx + (y - fy) * diry;            // > 0: still covered by glassine
    const poly = (s) => {                                                 // frame polygon clipped to one side of the fold
      const pts = [[0, 0], [W, 0], [W, H], [0, H]], out = [];
      for (let i = 0; i < 4; i++) {
        const A = pts[i], B = pts[(i + 1) % 4], sa = side(...A) * s, sb = side(...B) * s;
        if (sa >= 0) out.push(A);
        if (sa * sb < 0) { const k = sa / (sa - sb); out.push([lerp(A[0], B[0], k), lerp(A[1], B[1], k)]); }
      }
      return out;
    };
    const covered = poly(1);
    if (covered.length > 2) {
      ctx.save(); ctx.beginPath(); covered.forEach((q, i) => (i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]))); ctx.closePath(); ctx.clip();
      ctx.fillStyle = 'rgba(250,248,244,0.62)'; ctx.fillRect(0, 0, W, H);
      ctx.strokeStyle = 'rgba(255,255,255,0.55)'; ctx.lineWidth = 1.2;                                    // crinkles
      const R = Z.rng(311); ctx.beginPath();
      for (let i = 0; i < 70; i++) { let x = R() * W, y = R() * H; ctx.moveTo(x, y); for (let k = 0; k < 3; k++) { x += R.range(-120, 120); y += R.range(-60, 60); ctx.lineTo(x, y); } }
      ctx.stroke();
      ctx.restore();
    }
    // the flap: the peeled region mirrored across the fold line, a translucent sheet with a soft fold shadow
    if (pk > 0.001 && pk < 0.999) {
      const peeled = poly(-1);
      if (peeled.length > 2) {
        const refl = ([x, y]) => { const s = side(x, y); return [x - 2 * s * dirx, y - 2 * s * diry]; };
        ctx.save(); ctx.beginPath(); peeled.map(refl).forEach((q, i) => (i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]))); ctx.closePath();
        ctx.shadowColor = 'rgba(27,20,32,0.25)'; ctx.shadowBlur = 30; ctx.fillStyle = 'rgba(246,244,240,0.86)'; ctx.fill();
        ctx.shadowBlur = 0;
        const g = ctx.createLinearGradient(fx, fy, fx + dirx * 160, fy + diry * 160);
        g.addColorStop(0, 'rgba(255,255,255,0.0)'); g.addColorStop(0.15, 'rgba(255,255,255,0.7)'); g.addColorStop(1, 'rgba(200,196,190,0.3)');
        ctx.fillStyle = g; ctx.fill(); ctx.restore();
      }
    }
  }
  function endCard(ctx, S) {
    const a = S.args, t = S.t, lt = S.lt, T = a.seal ?? 161.2;
    const credit = Z.CREDIT || '', cr = clamp((t - 162.0) / 2.0);
    const rows = ROWS_END();
    const p = { marks: 1, number: 1, tape: 1, pin: 1, label: 1, rows, sealK: t - T, sealText: G.part(41, 2, 6) || '无人问津', sealPx: 150 };
    ctx.save(); camAt(ctx, 1.0 + 0.012 * clamp(lt / 7), 960, 540);
    sheet(ctx, { t, p, specimen: 'bloom' });
    // credits typed under the label
    if (cr > 0) {
      const n = Math.round([...credit].length * cr);
      ctx.save(); ctx.textAlign = 'left'; ctx.textBaseline = 'top';
      G.font(ctx, 30, 'hand', 400); ctx.fillStyle = Z.rgba(C.ink, 0.85); ctx.fillText([...credit].slice(0, n).join(''), LABEL.x + 6, LABEL.y + LABEL.row * 5.6 + 44);
      G.font(ctx, 17, 'hei', 500); ctx.fillStyle = Z.rgba(C.ink, 0.5 * clamp((cr - 0.6) * 2.5));
      ctx.fillText('vocaloid-style-mv-pipeline · JIZURA 字面', LABEL.x + 6, LABEL.y + LABEL.row * 5.6 + 92);
      ctx.restore();
    }
    // a silverfish crosses the sheet (forgetting goes on)
    const sk = (t - 164.5) / 2.6;
    if (sk > 0 && sk < 1.2) {
      const e = sk, x = lerp(W + 80, 860, e), y = lerp(880, 760, e) + Math.sin(e * 9) * 14;
      G.silverfish(ctx, x, y, Math.PI + 0.12 + Math.cos(e * 9) * 0.08, 70, t, 3, 1);
    }
    ctx.restore();
    const f = clamp((t - (S.shot.t1 - 0.4)) / 0.4); if (f > 0) D.fill(ctx, '#000', f);
  }

  Z.scene('hPage', {
    init: async () => { await G.ready(); },
    draw(ctx, S) {
      const m = S.args.mode || 'intro';
      if (m === 'intro') return void intro(ctx, S);
      if (m === 'stamp') return void stamp(ctx, S);
      if (m === 'photo') return void photo(ctx, S);
      if (m === 'glassine') return void glassine(ctx, S);
      if (m === 'end') return void endCard(ctx, S);
    },
  });

  // ------------------------------------------------------------------ hType: plain type cards
  function title(ctx, S) {
    const t = S.t, back = S.args.musicBack ?? 15.54;
    G.drawPaper(ctx, 'xuan', 11);
    const push = 1 + 0.035 * G.EZ.soft(clamp((t - back) / 0.6));
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(push, push); ctx.translate(-W / 2, -H / 2);
    const glyphs = [...(Z.TITLE || '花骨朵')];
    const xs = [520, 1000, 1470], ys = [560, 520, 590], ss = [560, 470, 520], rs = [-0.035, 0.02, 0.045];
    glyphs.forEach((g, i) => {
      G.text(ctx, g, xs[i] + 7, ys[i] + 5, { size: ss[i], fam: 'brush', weight: 400, color: Z.rgba(C.carmine, 0.85), rotate: rs[i] });
      G.text(ctx, g, xs[i], ys[i], { size: ss[i], fam: 'brush', weight: 400, color: C.ink, rotate: rs[i] });
    });
    G.seal(ctx, 1760, 860, 96, glyphs[0] || '花', { k: 1, style: 'yin', rot: 0.04, seed: 21 });
    ctx.restore();
    ctx.save(); ctx.fillStyle = Z.rgba(C.ink, 0.72); ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
    G.font(ctx, 24, 'dot', 400); ctx.fillText(Z.TITLE_SUB || 'HUAGUDUO', 118, 960);
    G.font(ctx, 22, 'hei', 500); ctx.fillText('Vocal：' + (Z.ARTIST || '洛天依'), 118, 996);
    ctx.fillStyle = Z.rgba(C.carmine, 0.85); ctx.fillRect(100, 930, 3, 76);
    ctx.restore();
  }
  function typeCard(ctx, S, o) {
    const t = S.t, line = S.args.line;
    if (o.black && t < o.black) { D.fill(ctx, '#000', 1); return; }
    G.drawPaper(ctx, o.paper, o.seed || 0);
    if (o.tint) D.fill(ctx, o.tint[0], o.tint[1], 'multiply');
    const glyphs = G.glyphs(line).join(''), ct = G.CT(line);
    let jx = 0, jy = 0;
    if (o.slam) for (const c of ct) { const u = t - (c - 0.12); if (u >= 0 && u < 0.6) { jx += G.damp(u, 10, 16, 8); jy += G.damp(u, 8, 15, 6); } }
    ctx.save(); ctx.translate(jx, jy);
    const z = 1 + (o.push || 0) * clamp(S.lt / S.dur);
    ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2);
    if (o.under) G.text(ctx, glyphs, W / 2 + o.under[0], H / 2 + o.under[1], { size: o.size, fam: o.fam, weight: o.weight, color: o.underColor, spacing: o.spacing ?? 0.1, reveal: G.sung(line, t, 0.12, o.dur || 0.2), anim: o.anim });
    G.text(ctx, glyphs, W / 2, H / 2, { size: o.size, fam: o.fam, weight: o.weight, color: o.color, spacing: o.spacing ?? 0.1, reveal: G.sung(line, t, 0.12, o.dur || 0.2), anim: o.anim });
    if (o.rule) {                                              // a thin carmine rule grows under the words
      const k = G.EZ.out(clamp((t - (ct[ct.length - 1] + 0.1)) / 0.5));
      ctx.fillStyle = Z.rgba(C.carmine, 0.9); ctx.fillRect(W / 2 - 150 * k, H / 2 + o.size * 0.75, 300 * k, 3);
    }
    ctx.restore();
    if (o.dust) {
      ctx.save(); ctx.fillStyle = 'rgba(244,238,228,0.5)';
      for (let i = 0; i < 60; i++) { const x = (Z.rnd(i, 5) * W + t * 9 * (0.5 + Z.rnd(i, 6))) % W, y = (Z.rnd(i, 7) * H - t * 5 * Z.rnd(i, 8) + H) % H; ctx.globalAlpha = 0.25 + 0.5 * Math.abs(Math.sin(t * 0.8 + i)); ctx.beginPath(); ctx.arc(x, y, 0.8 + 1.6 * Z.rnd(i, 9), 0, TAU); ctx.fill(); }
      ctx.restore();
    }
  }
  Z.scene('hType', {
    init: async () => { await G.ready(); },
    draw(ctx, S) {
      const m = S.args.mode || 'title';
      if (m === 'title') return void title(ctx, S);
      if (m === 'want') return void typeCard(ctx, S, { black: 46.54, paper: 'ink', size: 66, fam: 'song', weight: 500, color: '#F4EEE4', rule: true, anim: 'ink', dur: 0.3 });
      if (m === 'want2') return void typeCard(ctx, S, { paper: 'xuan', seed: 4, size: 176, fam: 'song', weight: 900, color: C.carmine, under: [-6, 5], underColor: Z.rgba(C.ink, 0.9), anim: 'slam', dur: 0.16, push: 0.04, slam: true });
      if (m === 'dont') return void typeCard(ctx, S, { paper: 'ink', size: 58, fam: 'song', weight: 300, color: '#EDE6DA', anim: 'ink', dur: 0.4, dust: true, spacing: 0.3 });
      if (m === 'dont2') return void typeCard(ctx, S, { paper: 'office', size: 230, fam: 'hei', weight: 900, color: '#E0243C', under: [7, 5], underColor: Z.rgba(C.ink, 0.85), anim: 'slam', dur: 0.12, slam: true, spacing: 0.06 });
    },
  });
})();
