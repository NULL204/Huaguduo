/* engine/scenes/hgd_scenes.js — the 花骨朵 film's scenes (anime_mv). Uses engine/scenes/hgd_core.js (Z.HGD).
 * Every character is a key drawing (assets/char/*.png, NovelAI / Codex) animated by Z.HGD.puppet; props and
 * architecture (branch, buds, insects, paper panels, roots, petals) are drawn assets or simple graphic shapes.
 * Lyric text is never written here: scenes that typeset a line read it at runtime with Z.HGD.lyr(i).
 *
 *   hgdShot      general illustrated shot: plate + camera + rack focus + puppet characters + fx
 *   hgdBranch    the branch and the bud (modes intro | swell | pop | ignored | tail)
 *   hgdPalm      her cupped hands (modes intro | look | morph | crush | crack | snow)
 *   hgdTitle     title lockup on the intro stops
 *   hgdFork      the left / right question as architecture (modes ask | accuse | snow)
 *   hgdHouse     a paper house folds up around her
 *   hgdRouge     fingertip on the lip, carmine floods the frame
 *   hgdCard      the court-poem line as a vertical type card with cloud scrolls
 *   hgdFall      the backward fall (pendulum about the heels, slow motion, landing burst)
 *   hgdMud       spring mud, roots growing on the beats
 *   hgdPage      the frame becomes a page that silverfish eat through
 *   hgdDoll      she flickers between her drawing and a paper-doll cut-out
 *   hgdBed       one bed (modes warm | split)
 *   hgdCalendar  solar-term pages flipping on the beat
 *   hgdMemory    earlier shots as prints that burn away
 */
(() => {
  'use strict';
  const Z = window.Z, D = Z.draw, E = Z.ease, G = Z.HGD, P = G.P;
  const W = 1920, H = 1080;
  const ease = n => (typeof n === 'function' ? n : E[n] || E.inOutSine);
  const img = p => (p ? Z.imgSync(p) : null);
  const A = 'assets/char/', BG = 'assets/bg/', PR = 'assets/prop/';
  const beatT = (n) => Z.clock.at(n);                            // song time of beat n (0 = first downbeat)
  const beatsIn = (t0, t1) => Z.clock.beats.filter(b => b >= t0 - 1e-6 && b < t1 - 1e-6);

  // ------------------------------------------------------------------ character drawing for every scene
  // c: { img, x, y, h, x2, y2, h2, ease, anchor, flip, front, rig, rigName, tilt, tiltF, breathe, wind, gust, flutter, lag,
  //      bob: {amp, steps}, alpha, in: {at,dur,dx,dy,ds,ease}, out: {...}, sil, shadow: {dx,dy,a,color,skewX,sy}, rot, squash, phase, freeze }
  const charPos = (c, S, s) => {
    const p = Z.clamp((s - S.shot.t0) / S.dur), k = ease(c.ease || 'inOutSine')(p);
    let x = Z.lerp(c.x, c.x2 ?? c.x, k), y = Z.lerp(c.y, c.y2 ?? c.y, k);
    const lt = s - S.shot.t0;
    if (c.in) { const d = Z.clamp((lt - (c.in.at || 0)) / (c.in.dur || 0.6)), e = ease(c.in.ease || 'outExpo')(d); x += (c.in.dx || 0) * (1 - e); y += (c.in.dy || 0) * (1 - e); }
    if (c.out) { const d = Z.clamp((lt - c.out.at) / (c.out.dur || 0.5)), e = ease(c.out.ease || 'inExpo')(d); x += (c.out.dx || 0) * e; y += (c.out.dy || 0) * e; }
    return [x, y];
  };
  // the drawing to show now: run cycles (seq), pose switches (poses), mouth on sung syllables (lips), blinks (blink)
  const frameOf = (c, S) => {
    let path = c.img, smear = 0;
    if (c.seq) {                                                    // cycle on the beat grid (drawn on 2s/3s)
      const steps = c.seq.perBeat ?? 2, ph = Z.clock.beat(S.t) * steps + Math.floor(Z.clock.phase(S.t) * steps);
      path = c.seq.frames[((ph % c.seq.frames.length) + c.seq.frames.length) % c.seq.frames.length];
    }
    if (c.poses) for (const pz of c.poses) if (S.t >= pz.at) { path = pz.img; smear = Z.clamp(1 - (S.t - pz.at) / 0.1); }
    if (c.lips && G.CT.length) {
      const lines = c.lips.lines || [c.lips.line], open = c.lips.open ?? 0.16, pre = c.lips.pre ?? 0.02;
      let sing = false;
      for (const n of lines) { const L = G.lineInfo(n); if (L && L.on.some(o => S.t >= o - pre && S.t < o + open)) { sing = true; break; } }
      if (!sing && c.lips.closed) path = c.lips.closed;
    }
    if (c.blink) {
      const every = c.blink.every ?? 3.2, k = Math.floor(S.t / every), tb = k * every + Z.rnd(k, 77) * (every - 0.3);
      if (S.t >= tb && S.t < tb + 0.13) path = c.blink.img;
    }
    return { path, smear };
  };
  const drawPuppetChar = (ctx, S, c) => {
    const fr = frameOf(c, S);
    const im = img(fr.path); if (!im) return;
    if (c.front && S.fg) ctx = S.fg;
    const t = c.freeze === false ? S.t : G.ft(S.t);
    const lt = S.t - S.shot.t0, p = Z.clamp(lt / S.dur), k = ease(c.ease || 'inOutSine')(p);
    let [x, y] = charPos(c, S, S.t);
    let h = Z.lerp(c.h, c.h2 ?? c.h, k), alpha = c.alpha ?? 1, rot = c.rot || 0;
    if (c.in) { const d = Z.clamp((lt - (c.in.at || 0)) / (c.in.dur || 0.6)), e = ease(c.in.ease || 'outExpo')(d); h *= 1 + (c.in.ds || 0) * (1 - e); rot += (c.in.rot || 0) * (1 - e); if (c.in.alpha !== false) alpha *= d > 0 ? Math.min(1, e * 1.5) : 0; }
    if (c.out) { const d = Z.clamp((lt - c.out.at) / (c.out.dur || 0.5)), e = ease(c.out.ease || 'inExpo')(d); h *= 1 + (c.out.ds || 0) * e; if (c.out.alpha !== false) alpha *= 1 - e; }
    if (alpha <= 0.002) return;
    // secondary motion from the body's own movement (lag behind acceleration) + walking bob
    let lagX = 0, lagY = 0;
    if (c.lag !== false) {
      const t0 = S.shot.t0 - 0.5;
      lagX = Z.clamp(G.springLag(s => G.acc(q => charPos(c, S, q)[0], s), t0, S.t) * (c.lagK ?? 1), -160, 160);
      lagY = Z.clamp(G.springLag(s => G.acc(q => charPos(c, S, q)[1], s), t0, S.t) * (c.lagK ?? 1), -120, 120);
    }
    let tilt = 0;
    if (c.tilt) { const tf = c.tiltF ?? 0.35; tilt = c.tilt * Math.sin(Z.TAU * tf * Z.quant(t, 12) + (c.phase || 0)); }
    if (c.bob) {
      const ph = G.stepPhase(S.t, c.bob.steps || 1), amp = c.bob.amp ?? 10;
      y -= amp * Math.abs(Math.sin(Math.PI * ph));
      lagY += amp * 1.6 * Math.cos(Math.PI * ph);
      rot += (c.bob.sway ?? 0.012) * Math.sin(Math.PI * 2 * ph * 0.5);
    }
    let wind = c.wind ?? 14;
    if (c.gust) wind += c.gust * (0.5 + 0.5 * Z.fbm1(t * 0.6, 17)) + c.gust * 0.6 * S.clock.downPulse(S.t, 4);
    if (c.beatBump) h *= 1 + c.beatBump * S.clock.pulse(S.t, 9);
    if (c.punch) for (const pt of c.punch) { const d = S.t - pt; if (d >= 0 && d < 0.5) h *= 1 + 0.09 * Math.exp(-d * 9); }
    const opt = { anchor: c.anchor || [0.5, 1], rot, flip: c.flip, alpha, t, rigName: c.rigName || c.img, rig: c.rig, tilt, breathe: c.breathe ?? 1,
      wind, flutter: c.flutter ?? 0.6, lagX: lagX + (c.lagX || 0), lagY: lagY + (c.lagY || 0), squash: c.squash || 0, phase: c.phase || 0 };
    if (c.shadow) {
      const sh = c.shadow; ctx.save(); ctx.globalAlpha = (sh.a ?? 0.3) * alpha;
      ctx.translate(x + (sh.dx || 0), y + (sh.dy || 0)); ctx.transform(1, 0, sh.skewX || -0.6, sh.sy ?? 0.35, 0, 0);
      G.puppet(ctx, G.tint(im, sh.color || P.deep), 0, 0, h, Object.assign({}, opt, { alpha: 1 }));
      ctx.restore();
    }
    if (c.rim) {                                                    // backlight: a blurred, tinted copy just behind her
      ctx.save(); ctx.globalCompositeOperation = c.rim.comp || 'source-over'; ctx.globalAlpha = c.rim.a ?? 0.8; ctx.filter = `blur(${c.rim.blur ?? 8}px)`;
      G.puppet(ctx, G.tint(im, c.rim.color || '#FFFFFF'), x + (c.rim.dx || 0), y + (c.rim.dy || 0), h * (c.rim.scale ?? 1.012), opt);
      ctx.restore();
    }
    if (fr.smear > 0) { ctx.save(); ctx.globalAlpha = 0.35 * fr.smear; for (let j = 1; j <= 4; j++) G.puppet(ctx, im, x - j * 22 * (c.smearDir || 1), y, h, opt); ctx.restore(); }
    if (c.sil) G.puppet(ctx, G.tint(im, c.sil), x, y, h, opt);
    else G.puppet(ctx, im, x, y, h, opt);
    if (c.glint) G.sparkle(ctx, S.t, Object.assign({ n: 4, size: 26, area: [x - h * 0.3, y - h, x + h * 0.3, y - h * 0.3] }, c.glint));
  };
  G.drawChar = drawPuppetChar;

  // ------------------------------------------------------------------ fx dispatcher for hgd scenes
  const fx = (ctx, S, f) => {
    const t = f.realTime ? S.t : G.ft(S.t);
    switch (f.type) {
      case 'snow': G.snow(ctx, t, f); break;
      case 'petals': G.petals(ctx, t, f); break;
      case 'sparkle': G.sparkle(ctx, t, f); break;
      case 'stains': G.stains(ctx, typeof f.amount === 'function' ? f.amount(S) : f.amount, Object.assign({ t }, f)); break;
      case 'grain': G.grain(ctx, f.a ?? 0.12); break;
      case 'fill': D.fill(ctx, f.color, f.a ?? 0.5, f.comp || 'source-over'); break;
      case 'grad': D.vgrad(ctx, f.stops, f.a ?? 1, f.comp || 'source-over'); break;
      case 'glow': D.glow(ctx, f.x, f.y, f.r, f.color || '#FFFFFF', f.a ?? 0.6); break;
      case 'sun': {      // a pale sun disc that drifts on a path (y from y0 to y1 over the shot): cool halo so it reads on white
        const k = ease(f.ease || 'inOutSine')(S.p), x = Z.lerp(f.x, f.x2 ?? f.x, k), y = Z.lerp(f.y, f.y2 ?? f.y, k), r = f.r || 70;
        ctx.save();
        const g = ctx.createRadialGradient(x, y, r * 0.8, x, y, r * 3.2); g.addColorStop(0, 'rgba(190,205,228,0.0)'); g.addColorStop(0.35, 'rgba(176,192,220,0.22)'); g.addColorStop(1, 'rgba(176,192,220,0)');
        ctx.fillStyle = g; ctx.fillRect(x - r * 3.3, y - r * 3.3, r * 6.6, r * 6.6);
        ctx.beginPath(); ctx.arc(x, y, r, 0, Z.TAU); ctx.fillStyle = '#FFFFFF'; ctx.fill(); ctx.lineWidth = 1.5; ctx.strokeStyle = 'rgba(141,155,173,0.55)'; ctx.stroke();
        ctx.restore(); break;
      }
      case 'speed': {    // anime speed lines (12 fps), horizontal
        const tq = Z.quant(S.t, 12), n = f.n ?? 46;
        ctx.save(); ctx.globalAlpha = f.a ?? 0.55;
        for (let i = 0; i < n; i++) {
          const y = Z.rnd(i, 3, Math.floor(tq * 12)) * H, len = 200 + 900 * Z.rnd(i, 4, Math.floor(tq * 12)), x = Z.rnd(i, 5, Math.floor(tq * 12)) * (W + len) - len;
          ctx.fillStyle = i % 3 ? (f.color || 'rgba(141,155,173,0.7)') : 'rgba(255,255,255,0.9)'; ctx.fillRect(x, y, len, 1 + 2 * Z.rnd(i, 6));
        }
        ctx.restore(); break;
      }
      case 'flicker': {  // fluorescent flicker on beats (dims, never flashes white)
        const pl = S.clock.pulse(S.t, 14); D.fill(ctx, f.color || '#0E1626', (f.a ?? 0.35) * pl, 'multiply'); break;
      }
      case 'fgPetals': G.fgPetals(ctx, t, f); break;
      case 'fgSnow': G.fgSnow(ctx, t, f); break;
      case 'shafts': G.shafts(ctx, t, f); break;
      case 'leak': G.leak(ctx, t, f); break;
      case 'shock': for (const t0 of f.at || []) G.shock(ctx, S.t, t0, f); break;
      case 'lines': G.focusLines(ctx, S.t, f); break;
      case 'custom': f.fn(ctx, S); break;
    }
  };
  G.fx = fx;

  // ------------------------------------------------------------------ hgdShot
  // args: { bg, fill: [top, bottom], view: {from, to, ease}, focus: [from, to] | number, kick (beat zoom), shake,
  //         tint: [{color, a, comp}], fxBack: [...], chars: [...], fx: [...], grain }
  // every drawing a character may show: base, cycle frames, pose switches, mouth / blink variants
  const charAssets = c => [c.img, ...(c.seq ? c.seq.frames : []), ...(c.poses || []).map(p2 => p2.img), c.lips && c.lips.closed, c.blink && c.blink.img];
  G.charAssets = charAssets;
  const assetsOf = a => [a.bg, ...(a.chars || []).flatMap(charAssets), ...(a.extra || [])].filter(Boolean);
  Z.scene('hgdShot', {
    preload: a => assetsOf(a),
    draw(ctx, S) {
      const a = S.args, t = S.t;
      const v = a.view || {}, k = ease(v.ease || 'inOutSine')(S.p);
      const view = D.viewLerp(v.from || { zoom: 1.04 }, v.to || v.from || { zoom: 1.1 }, k);
      if (a.kick) view.zoom *= 1 + a.kick * S.clock.pulse(t, 7);
      if (a.punch) for (const pt of a.punch) { const d = t - pt; if (d >= 0 && d < 0.6) { view.zoom *= 1 + 0.12 * Math.exp(-d * 8); view.rot = (view.rot || 0) + 0.02 * Math.exp(-d * 8) * (Math.round(pt * 2) % 2 ? 1 : -1); } }
      if (a.dutch) view.rot = (view.rot || 0) + a.dutch * Math.sin(t * 0.6);
      if (a.shake) { const [sx, sy] = D.shake(t, a.shake, 12, 5); view.x += sx / 500; view.y += sy / 400; }
      if (a.handheld) { view.x += a.handheld * Z.fbm1(t * 0.35, 3); view.y += a.handheld * 0.8 * Z.fbm1(t * 0.31, 4); view.rot = (view.rot || 0) + a.handheld * 0.01 * Z.fbm1(t * 0.27, 5); }
      if (a.bg) {
        const f = Array.isArray(a.focus) ? Z.lerp(a.focus[0], a.focus[1], ease(a.focusEase || 'inOutCubic')(S.p)) : (a.focus || 0);
        G.plate(ctx, img(a.bg), view, f, a.blur || 16);
      } else G.paperFill(ctx, ...(a.fill || [P.frost, '#E7EDF4']));
      for (const tn of a.tint || []) D.fill(ctx, tn.color, tn.a ?? 0.4, tn.comp || 'multiply');
      for (const f of a.fxBack || []) fx(ctx, S, f);
      G.lyrics(ctx, S, 'back');
      for (const c of a.chars || []) drawPuppetChar(ctx, S, c);
      for (const f of a.fx || []) fx(a.fxFront && S.fg ? S.fg : ctx, S, f);
      G.lyrics(ctx, S, 'front');
      if (a.grain !== false) G.grain(ctx, a.grain ?? 0.1);
    },
  });

  // ------------------------------------------------------------------ hgdBranch: the branch and its bud
  // args: { mode, branch:{x,y,h,rot}, tip:[u,v] (bud point in the branch image), reveal:[t0,t1], zoom:{from,to,cx,cy},
  //         budAt (time the bud appears), pop (time it opens), figure (tiny figure walking away) }
  const budImg = (mode, S, a) => {
    if (mode === 'pop') return S.t < a.pop ? PR + 'bud_half.png' : PR + 'bloom.png';
    if (mode === 'ignored') return PR + 'bloom.png';
    if (mode === 'swell') return S.t < (a.crack ?? 1e9) ? PR + 'bud_closed.png' : PR + 'bud_half.png';
    return PR + 'bud_closed.png';
  };
  Z.scene('hgdBranch', {
    preload: a => [PR + 'branch.png', PR + 'bud_closed.png', PR + 'bud_half.png', PR + 'bloom.png', A + 'back_walk.png'],
    draw(ctx, S) {
      const a = S.args, mode = a.mode || 'intro', t = S.t, ft = G.ft(t);
      // page
      G.paperFill(ctx, '#F7F9FB', '#E8EDF3');
      const mist = ctx.createRadialGradient(W * 0.6, H * 0.4, 50, W * 0.6, H * 0.4, W * 0.7); mist.addColorStop(0, 'rgba(255,255,255,0.8)'); mist.addColorStop(1, 'rgba(215,227,238,0.0)');
      ctx.fillStyle = mist; ctx.fillRect(0, 0, W, H);
      // camera: zoom around the tip
      const br = a.branch || { x: 860, y: 640, h: 760, rot: 0 }, bim = img(PR + 'branch.png');
      const bw = bim.width * (br.h / bim.height);
      const tipX = br.x - bw / 2 + (a.tip ? a.tip[0] : 0.92) * bw, tipY = br.y - br.h / 2 + (a.tip ? a.tip[1] : 0.1) * br.h;
      const zf = a.zoom || {}, zk = ease(zf.ease || 'inOutCubic')(S.p), zoom = Z.lerp(zf.from ?? 1, zf.to ?? zf.from ?? 1, zk);
      const cx = zf.cx ?? tipX, cy = zf.cy ?? tipY;
      ctx.save();
      ctx.translate(W / 2 + (zf.dx || 0), H / 2 + (zf.dy || 0)); ctx.scale(zoom, zoom); ctx.translate(-cx, -cy);
      // the branch, inked in from its base (12 fps reveal with a ragged front)
      const rv = a.reveal ? Z.clamp((Z.quant(t, 12) - a.reveal[0]) / (a.reveal[1] - a.reveal[0])) : 1;
      const sway = 0.012 * Math.sin(ft * 0.9) + 0.006 * Z.fbm1(ft * 0.5, 4);
      ctx.save();
      ctx.translate(br.x - bw / 2, br.y + br.h / 2); ctx.rotate((br.rot || 0) + sway); ctx.translate(-(br.x - bw / 2), -(br.y + br.h / 2));
      if (rv < 1) {
        ctx.save(); ctx.beginPath();
        const front = br.x - bw / 2 + rv * (bw + 80);
        ctx.moveTo(br.x - bw / 2 - 40, br.y - br.h); for (let yy = 0; yy <= 12; yy++) ctx.lineTo(front + 30 * Z.rnds(yy, Math.floor(t * 12)), br.y - br.h / 2 + (yy / 12) * br.h * 1.4 - br.h * 0.2);
        ctx.lineTo(br.x - bw / 2 - 40, br.y + br.h); ctx.closePath(); ctx.clip();
        D.sprite(ctx, bim, br.x, br.y + br.h / 2, br.h, { anchor: [0.5, 1] });
        ctx.restore();
      } else D.sprite(ctx, bim, br.x, br.y + br.h / 2, br.h, { anchor: [0.5, 1] });
      // the bud at the tip (springs with the branch, pulses on beats when swelling)
      const budAt = a.budAt ?? (a.reveal ? a.reveal[1] - 0.2 : -1e9);
      const bk = Z.clamp((t - budAt) / 0.5);
      if (bk > 0) {
        const bi = img(budImg(mode, S, a));
        let bs = (a.budH || 120) * E.outBack(bk);
        if (mode === 'swell') bs *= 1 + 0.25 * S.p + 0.05 * S.clock.pulse(t, 6);
        if (mode === 'pop') { const pk = Z.clamp((t - a.pop) / 0.35); bs *= t < a.pop ? 1.25 + 0.04 * S.clock.pulse(t, 9) : Z.lerp(0.7, 1.6, E.outBack(pk)); }
        if (mode === 'ignored') bs *= 1.6;
        const bud = { x: tipX, y: tipY };
        ctx.save(); ctx.translate(bud.x, bud.y); ctx.rotate((a.budRot || 0.2) + 0.05 * Math.sin(ft * 1.3));
        D.sprite(ctx, bi, 0, bs * 0.15, bs, { anchor: [0.5, 1] });
        ctx.restore();
        if (mode === 'pop' && t >= a.pop) {     // petals thrown out by the opening
          const dt = t - a.pop;
          for (let i = 0; i < 14; i++) {
            const an = Z.rnd(i, 61) * Z.TAU, sp = 220 + 380 * Z.rnd(i, 62);
            const px = bud.x + Math.cos(an) * sp * dt, py = bud.y + Math.sin(an) * sp * dt + 260 * dt * dt;
            G.petalAt(ctx, px, py, 10 + 8 * Z.rnd(i, 63), an + dt * 4, Math.cos(dt * 6 + i), i % 2 ? P.carmine : P.rouge, Z.clamp(1 - dt / 1.4));
          }
        }
      }
      ctx.restore();
      if (a.thread) {
        const th = a.thread, k = E.inOutSine(Z.clamp((t - th.t0) / (th.t1 - th.t0))), pts = th.pts;
        ctx.save(); ctx.strokeStyle = Z.rgba(P.carmine, 0.9); ctx.lineWidth = th.w || 2.4; ctx.lineCap = 'round'; ctx.beginPath();
        const N = 80; for (let j = 0; j <= N * k; j++) { const u = j / N, f = u * (pts.length - 1), q = Math.min(pts.length - 2, Math.floor(f)), r = f - q; const x = Z.lerp(pts[q][0], pts[q + 1][0], r) + Math.sin(u * 9 + t) * 6, y = Z.lerp(pts[q][1], pts[q + 1][1], r) + Math.cos(u * 7 + t) * 4; if (j) ctx.lineTo(x, y); else ctx.moveTo(x, y); }
        ctx.stroke(); ctx.restore();
      }
      S.tip = [tipX, tipY];
      G.lyrics(ctx, S, 'world');
      // a tiny figure walking away into the white (the 'ignored' pull-back)
      if (a.figure) { const f = a.figure; G.drawChar(ctx, S, Object.assign({ img: A + 'back_walk.png', front: false, bob: { amp: 2, steps: 1 }, wind: 4, lag: false }, f)); }
      ctx.restore();
      // falling petals / frost
      if (mode === 'ignored' || mode === 'pop') G.petals(ctx, ft, { n: mode === 'ignored' ? 26 : 12, size: 9, speed: 60, wind: 0.2, alpha: 0.9 });
      G.sparkle(ctx, t, { n: mode === 'tail' ? 6 : 14, size: 18, alpha: 0.85, area: [0, 0, W, H * 0.8] });
      if (mode === 'intro' || mode === 'tail') G.snow(ctx, ft, { n: 40, size: 2.4, speed: 40, alpha: 0.6 });
      G.lyrics(ctx, S, 'front');
      G.grain(ctx, 0.12);
      // tail: credits typed under the branch
      if (mode === 'tail' && a.credits) {
        const ck = Z.clamp((t - S.shot.t0 - 0.4) / 0.8);
        ctx.save(); ctx.globalAlpha = ck; ctx.fillStyle = P.ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        D.font(ctx, 44, 'serif', 300); ctx.fillText(Z.TITLE, W / 2, H * 0.83);
        D.font(ctx, 18, 'mono', 500); ctx.fillStyle = P.deep;
        a.credits.forEach((line, i) => ctx.fillText(line, W / 2, H * 0.83 + 48 + i * 28));
        ctx.restore();
      }
    },
  });

  // ------------------------------------------------------------------ hgdPalm: the cupped hands
  // args: { mode, palm:[fx,fy] (point on the palm, fractions of the plate), view:{from,to}, morphAt, crushAt, landings:[t...] }
  Z.scene('hgdPalm', {
    preload: a => [A + 'palm_close.png', PR + 'cochineal.png', PR + 'bud_closed.png', PR + 'bud_half.png'],
    draw(ctx, S) {
      const a = S.args, mode = a.mode || 'look', t = S.t, ft = G.ft(t);
      const plate = img(A + 'palm_close.png');
      const v = a.view || {}, k = ease(v.ease || 'inOutSine')(S.p);
      const view = D.viewLerp(v.from || { zoom: 1.05 }, v.to || { zoom: 1.18 }, k);
      view.x += 0.05 * Z.fbm1(ft * 0.3, 7); view.y += 0.05 * Z.fbm1(ft * 0.27, 8);
      if (mode === 'crush') { const sh = Z.clamp((t - (a.crushAt ?? S.shot.t0)) / 2) * 6; const [sx, sy] = D.shake(t, sh, 24, 9); view.x += sx / 300; view.y += sy / 200; }
      const breath = 1 + 0.006 * Math.sin(ft * 2.0);
      view.zoom *= breath;
      D.cover(ctx, plate, view);
      // map a plate fraction to screen through the same cover transform
      const s = Math.max(W / plate.width, H / plate.height) * view.zoom, dw = plate.width * s, dh = plate.height * s;
      const mx = Math.max(0, (dw - W) / 2), my = Math.max(0, (dh - H) / 2);
      const toScr = (fx, fy) => [W / 2 + view.x * mx + (fx - 0.5) * dw, H / 2 + view.y * my + (fy - 0.5) * dh];
      const [px, py] = toScr(...(a.palm || [0.66, 0.6]));
      const unit = dh / 941;
      S.palm = { px, py, unit, toScr };
      G.lyrics(ctx, S, 'back');                                   // plate pixels -> screen
      const bugH = (a.bugH || 90) * unit;
      const bug = img(PR + 'cochineal.png');
      const drawBug = (x, y, ang, sc, al) => {
        ctx.save(); ctx.globalAlpha *= al;
        ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.translate(x + 6 * unit, y + 10 * unit); ctx.scale(1, 0.5);
        const g = ctx.createRadialGradient(0, 0, 2, 0, 0, bugH * 0.7); g.addColorStop(0, 'rgba(120,96,96,0.45)'); g.addColorStop(1, 'rgba(120,96,96,0)');
        ctx.fillStyle = g; ctx.fillRect(-bugH, -bugH, bugH * 2, bugH * 2); ctx.restore();
        ctx.translate(x, y); ctx.rotate(ang); const leg = 1 + 0.035 * Math.sin(Z.quant(t, 12) * 40);
        ctx.scale(sc * leg, sc / leg);
        D.sprite(ctx, bug, 0, 0, bugH, { anchor: [0.5, 0.5] });
        ctx.restore();
      };
      // insect path: wanders on the palm; heading follows the velocity
      const pathAt = (s) => [px + 70 * unit * Math.sin(s * 0.9 + 1) + 30 * unit * Math.sin(s * 2.3), py + 40 * unit * Math.sin(s * 0.7) + 18 * unit * Math.cos(s * 1.9)];
      S.bug = { pathAt, walkT: mode === 'intro' ? Math.max(0, ft - S.shot.t0 - 0.8) : ft };
      if (mode === 'intro' || mode === 'look' || mode === 'crush' || (mode === 'morph' && t < a.morphAt + 0.4)) {
        const walkT = mode === 'intro' ? Math.max(0, ft - S.shot.t0 - 0.8) : ft;
        let [bx, by] = pathAt(walkT);
        if (mode === 'intro') { const e = E.outCubic(Z.clamp((ft - S.shot.t0 - 0.6) / 2.4)); bx = Z.lerp(px + 520 * unit, bx, e); by = Z.lerp(py + 260 * unit, by, e); }
        const [nx, ny] = pathAt(walkT + 0.05), ang = Math.atan2(ny - by, nx - bx) + Math.PI / 2;
        let sc = 1, al = mode === 'intro' ? Z.clamp((ft - S.shot.t0 - 0.6) / 0.4) : 1;
        if (mode === 'morph') { const mk = Z.clamp((t - a.morphAt) / 0.4); sc = 1 - 0.5 * E.inCubic(mk); al *= 1 - mk; }
        if (mode === 'crush') al *= 1 - Z.clamp((t - (a.crushAt ?? S.shot.t0) - 0.8) / 1.0);
        if (al > 0) drawBug(bx, by, ang, sc, al);
        if (mode === 'intro') { const tk = Z.clamp((ft - S.shot.t0 - 2.6) / 0.8); if (tk > 0) G.inkBloom(ctx, bx, by + 30 * unit, 26 * unit, tk, { alpha: 0.35, seed: 4, t }); }
      }
      if (mode === 'morph' || mode === 'crack') {
        const at = mode === 'morph' ? a.morphAt : S.shot.t0 - 1;
        const mk = Z.clamp((t - at) / 0.45);
        if (mk > 0) {
          const bi = img(mode === 'crack' && t > (a.crackAt ?? S.shot.t0 + 1) ? PR + 'bud_half.png' : PR + 'bud_closed.png');
          const [bx, by] = mode === 'morph' ? pathAt(a.morphAt) : [px, py];
          const grow = mode === 'crack' ? 1 + 0.18 * S.p + 0.04 * S.clock.pulse(t, 8) : 1;
          ctx.save(); ctx.globalAlpha = E.outCubic(mk); ctx.translate(bx, by); ctx.rotate(-0.25 + 0.04 * Math.sin(ft * 1.4));
          D.sprite(ctx, bi, 0, 30 * unit, (a.budH || 210) * unit * Z.lerp(0.55, 1, E.outBack(mk)) * grow, { anchor: [0.5, 1] });
          ctx.restore();
          if (mode === 'morph') G.sparkle(ctx, t, { n: 5, size: 34, rate: 1.4, area: [bx - 120, by - 160, bx + 120, by + 40] });
        }
      }
      if (mode === 'crush') {
        const ck = Z.clamp((t - (a.crushAt ?? S.shot.t0)) / 2.6);
        G.inkBloom(ctx, px, py, 420 * unit, ck, { seed: 12, t, alpha: 0.9 });
        if (ck > 0.3) {            // dye seeping down through the gaps between the fingers
          ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.strokeStyle = Z.rgba(P.carmine, 0.55); ctx.lineCap = 'round';
          for (let i = 0; i < 5; i++) { const x0 = px - 160 * unit + i * 80 * unit, len = 260 * unit * E.outCubic(Z.clamp((ck - 0.3 - i * 0.05) / 0.6)); ctx.lineWidth = (5 + 3 * Z.rnd(i, 3)) * unit; ctx.beginPath(); ctx.moveTo(x0, py + 60 * unit); ctx.quadraticCurveTo(x0 + 10 * unit, py + 60 * unit + len * 0.5, x0 - 6 * unit, py + 60 * unit + len); ctx.stroke(); }
          ctx.restore();
        }
      }
      if (mode === 'snow') {
        G.snow(ctx, ft, { n: 110, size: 4, speed: 90, wind: 0.1 });
        for (const [i, lt] of (a.landings || []).entries()) {        // flakes that land in the palm melt into carmine drops
          const fall = Z.clamp((t - (lt - 1.6)) / 1.6), [lx, ly] = [px + (Z.rnds(i, 7) * 150) * unit, py + (Z.rnds(i, 8) * 70) * unit];
          if (fall > 0 && fall < 1) { ctx.save(); ctx.beginPath(); ctx.arc(lx + 40 * (1 - fall), ly - 700 * (1 - E.inQuad(fall)), 7, 0, Z.TAU); ctx.fillStyle = '#fff'; ctx.fill(); ctx.strokeStyle = 'rgba(120,138,168,0.6)'; ctx.stroke(); ctx.restore(); }
          if (t >= lt) G.inkBloom(ctx, lx, ly, 46 * unit, Z.clamp((t - lt) / 0.9), { seed: 30 + i, t, alpha: 0.85 });
        }
      }
      G.lyrics(ctx, S, 'front');
      G.sparkle(ctx, t, { n: 6, size: 18, alpha: 0.7, area: [px - 300, py - 300, px + 300, py + 200] });
      if (mode !== 'snow') G.snow(ctx, ft, { n: 26, size: 2.2, speed: 30, alpha: 0.55 });
      G.grain(ctx, 0.1);
    },
  });

  // ------------------------------------------------------------------ hgdTitle
  // args: { char, glyphTimes:[t,t,t], sub, credit, x (figure), glyphX }
  Z.scene('hgdTitle', {
    preload: a => [a.char || A + 'REF_master.png'],
    draw(ctx, S) {
      const a = S.args, t = S.t, ft = G.ft(t);
      G.paperFill(ctx, '#F8FAFC', '#E6ECF3');
      G.snow(ctx, ft, { n: 70, size: 2.6, speed: 46, alpha: 0.7 });
      G.drawChar(ctx, S, { img: a.char || A + 'REF_master.png', x: a.x ?? 640, y: 1010, h: 900, x2: (a.x ?? 640) + 30, wind: 26, gust: 18, tilt: 0.02, lag: false, flutter: 0.8 });
      const glyphs = [...Z.TITLE], gx = a.glyphX ?? 1340, size = 210;
      glyphs.forEach((ch, i) => {
        const gt = (a.glyphTimes || [])[i] ?? S.shot.t0 + 0.5 + i * 0.5, k = Z.clamp((Z.quant(t, 12) - gt) / 0.35);
        if (k <= 0) return;
        const y = 210 + i * size * 1.08;
        ctx.save(); ctx.globalAlpha = E.outCubic(k); ctx.translate(gx, y + (1 - E.outCubic(k)) * 30);
        D.font(ctx, size, 'serif', 200); ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillStyle = i === 2 ? P.carmine : P.ink; ctx.fillText(ch, 0, 0);
        ctx.restore();
      });
      const lk = Z.clamp((t - ((a.glyphTimes || [])[2] ?? S.shot.t0 + 1.5) - 0.4) / 0.8);
      if (lk > 0) {
        ctx.save(); ctx.globalAlpha = lk; ctx.fillStyle = P.deep; ctx.textAlign = 'center';
        D.font(ctx, 22, 'mono', 500); ctx.fillText(a.sub || Z.TITLE_SUB, gx, 210 + 3 * size * 1.08 - 10);
        ctx.strokeStyle = P.carmine; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(gx - 120 * lk, 210 + 3 * size * 1.08 + 18); ctx.lineTo(gx + 120 * lk, 210 + 3 * size * 1.08 + 18); ctx.stroke();
        D.font(ctx, 20, 'serif', 300); ctx.fillStyle = P.ink; ctx.fillText(a.credit || Z.CREDIT, gx, 210 + 3 * size * 1.08 + 52);
        ctx.restore();
      }
      G.sparkle(ctx, t, { n: 16, size: 22, alpha: 0.9 });
      G.grain(ctx, 0.12);
    },
  });

  // ------------------------------------------------------------------ hgdFork: the left / right question
  // args: { mode, line (lyric index), slams:[t_left, t_right], char, bg }
  const dirGlyphs = (line) => {
    const L = [...line];
    const li = L.indexOf('左'), ri = L.indexOf('右');          // the two directions, found in the runtime line
    return [li >= 0 ? L[li] : L[0] || '', ri >= 0 ? L[ri] : L[L.length - 1] || ''];
  };
  Z.scene('hgdFork', {
    preload: a => [a.bg || BG + 'field_fork.png', a.char || A + 'turn_back.png'],
    draw(ctx, S) {
      const a = S.args, mode = a.mode || 'ask', t = S.t, ft = G.ft(t);
      const line = G.lyr(a.line || 2), [gl, gr] = dirGlyphs(line);
      const [t1, t2] = a.slams || [S.shot.t0 + 0.3, S.shot.t0 + 1.3];
      // camera whips toward each direction as it is named
      const pan = (t < t1 ? 0 : t < t2 ? -1 : 1);
      const pk = t < t1 ? 0 : E.outExpo(Z.clamp((t - (t < t2 ? t1 : t2)) / 0.35));
      const prev = t < t2 ? 0 : -1, camX = Z.lerp(prev, pan, pk) * 0.55;
      const view = { zoom: 1.12 + 0.03 * S.p, x: camX, y: 0.2 };
      const whip = t >= t1 && Z.clamp(1 - (t - (t < t2 ? t1 : t2)) / 0.25);
      const fim = img(a.bg || BG + 'field_fork.png');
      G.plate(ctx, fim, view, whip ? 0.6 * whip : 0);
      const sc = Math.max(W / fim.width, H / fim.height) * view.zoom, dw = fim.width * sc, dh = fim.height * sc, mx = Math.max(0, (dw - W) / 2), my = Math.max(0, (dh - H) / 2);
      S.toScr = (fx, fy) => [W / 2 + view.x * mx + (fx - 0.5) * dw, H / 2 + view.y * my + (fy - 0.5) * dh];
      S.pathL = [[0.37, 0.98], [0.30, 0.80], [0.24, 0.66], [0.19, 0.55], [0.15, 0.48]];
      S.pathR = [[0.57, 0.98], [0.66, 0.78], [0.72, 0.66], [0.79, 0.58], [0.85, 0.5]];
      if (mode === 'snow') G.snow(ctx, ft, { n: 260, size: 5, speed: 200, wind: 0.9 });
      S.cam = { camX, pan: camX * mx * 1.4 };
      G.lyrics(ctx, S, 'back');
      // her, small at the fork, looking back
      G.drawChar(ctx, S, { img: a.char || A + 'turn_back.png', x: 960 + camX * mx * 1.4, y: 1000, h: 520, wind: mode === 'snow' ? 60 : 18, gust: mode === 'snow' ? 40 : 10, lag: false, tilt: 0.02 });
      // the two direction glyphs slam onto the two paths
      const glyph = (ch, x, ts, side) => {
        const k = Z.clamp((t - ts) / 0.22); if (k <= 0) return;
        const s = Z.lerp(1.5, 1, E.outBack(k)), size = mode === 'accuse' ? 560 : 500;
        let al = 1, dx = 0, dy = 0;
        if (mode === 'snow') { const bk = Z.clamp((t - ts - 0.9) / 1.2); al = 1 - bk; dx = side * 220 * E.inQuad(bk); dy = -60 * bk; }
        ctx.save(); ctx.translate(x - camX * 420 + dx, 540 + dy); ctx.scale(s, s); ctx.globalAlpha = al;
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        if (mode === 'accuse') { D.font(ctx, size, 'brush', 400); ctx.fillStyle = Z.rgba(P.carmine, 0.92); ctx.fillText(ch, 0, 0); }
        else { D.font(ctx, size, 'serif', 200); ctx.fillStyle = Z.rgba(P.ink, 0.85); ctx.fillText(ch, 0, 0); ctx.lineWidth = 2; ctx.strokeStyle = 'rgba(255,255,255,0.6)'; ctx.strokeText(ch, 0, 0); }
        ctx.restore();
      };
      void glyph; void gl; void gr;
      G.lyrics(ctx, S, 'front');
      if (mode === 'accuse') G.stains(ctx, 0.35 + 0.2 * S.p, { t: ft, n: 30 });
      G.sparkle(ctx, t, { n: mode === 'snow' ? 24 : 12, size: 22 });
      G.grain(ctx, 0.1);
      // accuse: the frame splits along the middle and the halves slide apart on the slams
      if (mode === 'accuse' && t >= t1) {
        const c = Z.scratch[0], x = c.getContext('2d'); x.clearRect(0, 0, W, H); x.drawImage(ctx.canvas, 0, 0);
        const off = 26 * (t >= t2 ? 2 : 1) * E.outExpo(Z.clamp((t - (t >= t2 ? t2 : t1)) / 0.3));
        ctx.save(); ctx.fillStyle = P.blood; ctx.fillRect(0, 0, W, H);
        ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W / 2 - 3, H); ctx.clip(); ctx.drawImage(c, -off * 0.3, -off); ctx.restore();
        ctx.save(); ctx.beginPath(); ctx.rect(W / 2 + 3, 0, W / 2, H); ctx.clip(); ctx.drawImage(c, off * 0.3, off); ctx.restore();
        ctx.restore();
      }
    },
  });

  // ------------------------------------------------------------------ hgdHouse: a paper house folds up around her on the beats
  // args: { char, beats:[t wall-back, t wall-left, t wall-right, t roof] }
  Z.scene('hgdHouse', {
    preload: a => [a.char || A + 'master_a.png'],
    draw(ctx, S) {
      const a = S.args, t = S.t, ft = G.ft(t);
      let zoom = 1 + 0.08 * E.inOutSine(S.p);
      for (const pt of a.punch || []) { const d = t - pt; if (d >= 0 && d < 0.5) zoom *= 1 + 0.06 * Math.exp(-d * 9); }
      ctx.save(); ctx.translate(W / 2, H * 0.62); ctx.scale(zoom, zoom); ctx.translate(-W / 2, -H * 0.62);
      G.paperFill(ctx, '#F9FAFB', '#E4EAF1');
      const floorY = 930, cx = 960;
      // floor plane lines
      ctx.save(); ctx.strokeStyle = 'rgba(141,155,173,0.35)'; ctx.lineWidth = 1;
      for (let i = -8; i <= 8; i++) { ctx.beginPath(); ctx.moveTo(cx + i * 60, floorY - 120); ctx.lineTo(cx + i * 260, H + 40); ctx.stroke(); }
      ctx.restore();
      const bt = a.beats || [S.shot.t0 + 0.05, S.shot.t0 + 0.55, S.shot.t0 + 1.05, S.shot.t0 + 1.55];
      const rise = i => E.outBack(Z.clamp((Z.quant(t, 12) - bt[i]) / 0.3), 1.2);
      const info = G.lineInfo(a.line || 10);
      const paper = (pts, k, alpha, lattice, gi = -1) => {
        if (k <= 0) return;
        ctx.save(); ctx.globalAlpha = alpha; ctx.beginPath(); pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.closePath();
        const yt = Math.min(...pts.map(p2 => p2[1])), yb = Math.max(...pts.map(p2 => p2[1]));
        const pg = ctx.createLinearGradient(0, yt, 0, yb); pg.addColorStop(0, '#FFFFFF'); pg.addColorStop(1, '#E3E9F1');
        ctx.fillStyle = pg; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = 'rgba(74,88,114,0.7)'; ctx.stroke();
        if (info && gi >= 0 && gi < info.chars.length) {        // the sung glyph, brushed onto this wall
          const gk = Z.clamp((t - info.on[gi] + 0.1) / 0.35);
          if (gk > 0) {
            const cxw = pts.reduce((m2, p2) => m2 + p2[0], 0) / pts.length, cyw = pts.reduce((m2, p2) => m2 + p2[1], 0) / pts.length;
            const hw = Math.abs(yb - yt);
            const slope = pts.length === 4 ? (pts[1][1] - pts[0][1]) / ((pts[1][0] - pts[0][0]) || 1) : 0;
            ctx.save(); ctx.translate(cxw, cyw); ctx.transform(1, Z.clamp(slope, -1.2, 1.2) * 0.85, 0, 1, 0, 0); ctx.globalAlpha = alpha * E.outCubic(gk);
            ctx.filter = `blur(${((1 - gk) * 6).toFixed(1)}px)`;
            D.font(ctx, hw * 0.3, 'brush', 400); ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.fillStyle = Z.rgba(P.carmine, 0.85); ctx.fillText(info.chars[gi], 0, 0); ctx.restore();
          }
        }
        if (lattice) { ctx.clip(); ctx.strokeStyle = 'rgba(141,155,173,0.55)'; ctx.lineWidth = 1.2; const [x0, y0] = pts[0], [x1, y1] = pts[2]; for (let i = 1; i < 6; i++) { const u = i / 6; ctx.beginPath(); ctx.moveTo(Z.lerp(pts[0][0], pts[1][0], u), Z.lerp(pts[0][1], pts[1][1], u)); ctx.lineTo(Z.lerp(pts[3][0], pts[2][0], u), Z.lerp(pts[3][1], pts[2][1], u)); ctx.stroke(); } for (let j = 1; j < 4; j++) { const u = j / 4; ctx.beginPath(); ctx.moveTo(Z.lerp(pts[0][0], pts[3][0], u), Z.lerp(pts[0][1], pts[3][1], u)); ctx.lineTo(Z.lerp(pts[1][0], pts[2][0], u), Z.lerp(pts[1][1], pts[2][1], u)); ctx.stroke(); } void x0; void y0; void x1; void y1; }
        ctx.restore();
      };
      // back wall rises from the floor line
      const kb = rise(0), wallH = 640, bw = 760, by = floorY - 110;
      paper([[cx - bw / 2, by - wallH * kb], [cx + bw / 2, by - wallH * kb], [cx + bw / 2, by], [cx - bw / 2, by]], kb, 0.96, true, -1);
      // her, inside
      G.drawChar(ctx, S, { img: a.char || A + 'master_a.png', x: cx, y: floorY - 40, h: 760, wind: 10, lag: false, tilt: 0.015 });
      // side walls hinge up (trapezoids in perspective)
      const kl = rise(1), kr = rise(2);
      paper([[cx - bw / 2, by - wallH * kl], [cx - bw / 2 - 260, floorY + 60 - (wallH + 140) * kl], [cx - bw / 2 - 260, floorY + 60], [cx - bw / 2, by]], kl, 0.86, true, 0);
      paper([[cx + bw / 2, by - wallH * kr], [cx + bw / 2 + 260, floorY + 60 - (wallH + 140) * kr], [cx + bw / 2 + 260, floorY + 60], [cx + bw / 2, by]], kr, 0.86, true, 1);
      // roof drops in last
      const kroof = rise(3);
      if (kroof > 0) {
        const ry = by - wallH - 40 - (1 - kroof) * 500;
        paper([[cx - bw / 2 - 300, ry + 150], [cx, ry - 120], [cx + bw / 2 + 300, ry + 150], [cx, ry + 60]], kroof, 0.95, false, 2);
      }
      ctx.restore();
      G.sparkle(ctx, t, { n: 10, size: 20 });
      G.snow(ctx, ft, { n: 30, size: 2.4, speed: 40, alpha: 0.5 });
      G.grain(ctx, 0.12);
    },
  });

  // ------------------------------------------------------------------ hgdRouge: the fingertip, the lip, the flood
  // args: { lip:[u,v] (on bride_bust), floodAt, recedeAt, view zoom }
  Z.scene('hgdRouge', {
    preload: () => [A + 'bride_bust.png'],
    draw(ctx, S) {
      const a = S.args, t = S.t, ft = G.ft(t);
      G.paperFill(ctx, '#F5F7FA', '#E2E8EF');
      const im = img(A + 'bride_bust.png'), [lu, lv] = a.lip || [0.5, 0.48];
      const zoom = Z.lerp(a.z0 ?? 2.2, a.z1 ?? 2.6, E.inOutSine(S.p));
      const h = H * zoom, w = im.width * h / im.height;
      const x0 = W / 2 - lu * w, y0 = H * 0.5 - lv * h;
      G.puppet(ctx, im, x0 + w / 2, y0 + h, h, { anchor: [0.5, 1], t: ft, rigName: A + 'bride_bust.png', wind: 6, breathe: 0.6 });
      const lx = W / 2, ly = H * 0.5;
      const fk = Z.clamp((t - (a.floodAt ?? S.shot.t0 + 0.3)) / 1.1), rk = Z.clamp((t - (a.recedeAt ?? S.shot.t1 - 0.6)) / 0.5);
      const kk = fk * (1 - E.inCubic(rk));
      G.inkBloom(ctx, lx, ly, 1500, kk, { seed: 41, t, alpha: 0.95 });
      if (kk > 0.6) D.fill(ctx, P.carmine, (kk - 0.6) * 1.2, 'multiply');
      G.lyrics(ctx, S, 'front');
      G.sparkle(ctx, t, { n: 4, size: 26, dark: kk > 0.5 });
      G.grain(ctx, 0.12);
    },
  });

  // ------------------------------------------------------------------ hgdCard: the court-poem line as a vertical type card
  // args: { line (lyric index), typeFrom, typeTo, ghost (char image drawn as a pale silhouette) }
  const cloud = (ctx, x, y, s, k, flip = 1) => {   // a 祥云 scroll: two spirals and a tail, drawn progressively
    ctx.save(); ctx.translate(x, y); ctx.scale(flip * s, s); ctx.lineWidth = 2.2 / s; ctx.strokeStyle = 'rgba(74,88,114,0.75)'; ctx.lineCap = 'round';
    const spiral = (cx, cy, r0, turns, kk) => { ctx.beginPath(); const N = 60; for (let i = 0; i <= N * kk; i++) { const u = i / N, a = u * turns * Z.TAU, r = r0 * (1 - u * 0.85); const px = cx + Math.cos(a) * r, py = cy + Math.sin(a) * r; if (i) ctx.lineTo(px, py); else ctx.moveTo(px, py); } ctx.stroke(); };
    spiral(0, 0, 40, 1.4, Z.clamp(k * 1.6)); spiral(70, -10, 28, 1.3, Z.clamp(k * 1.6 - 0.3));
    ctx.beginPath(); const tk = Z.clamp(k * 1.6 - 0.6); if (tk > 0) { ctx.moveTo(-40, 0); ctx.bezierCurveTo(-90, 20 * tk, -150, -10 * tk, -220 * tk, 10 * tk); ctx.stroke(); }
    ctx.restore();
  };
  Z.scene('hgdCard', {
    preload: a => [a.ghost || A + 'bride_bust.png'],
    draw(ctx, S) {
      const a = S.args, t = S.t;
      G.paperFill(ctx, '#FAFBFC', '#EEF1F5');
      const gim = img(a.ghost || A + 'bride_bust.png');
      ctx.save(); ctx.globalAlpha = 0.13 + 0.03 * Math.sin(t); G.puppet(ctx, gim, 520, H + 40, H * 1.05, { t, wind: 6, rigName: a.ghost || A + 'bride_bust.png' }); ctx.restore();
      D.fill(ctx, '#F6F8FB', 0.35);
      const info = G.lineInfo(a.line || 14), chars = info ? info.chars : [];
      const sung = info ? info.on.filter(o => o <= t + 0.08).length + Z.clamp((t + 0.08 - (info.on.find(o => o > t + 0.08) ?? 1e9) + 0.3) / 0.3) : 0;
      const k = chars.length ? Z.clamp(sung / chars.length) : 0;
      // vertical, right to left in two columns when long
      const per = Math.ceil(chars.length / 2), size = 118;
      const cols = [chars.slice(0, per), chars.slice(per)];
      cols.forEach((col, ci) => {
        D.vtext(ctx, col.join(''), 1420 - ci * 190, 150 + ci * 60, { size, fam: 'serif', weight: 300, color: P.ink, reveal: Z.clamp(k * 2 - ci) });
      });
      ctx.save(); ctx.strokeStyle = P.carmine; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(1560, 140); ctx.lineTo(1560, 140 + 760 * E.outCubic(Z.clamp(k * 1.5))); ctx.stroke(); ctx.restore();
      cloud(ctx, 860, 300, 1.4, Z.clamp((t - S.shot.t0) / 2.2), 1);
      cloud(ctx, 1140, 860, 1.1, Z.clamp((t - S.shot.t0 - 0.6) / 2.2), -1);
      G.sparkle(ctx, t, { n: 8, size: 18 });
      G.grain(ctx, 0.12);
    },
  });

  // ------------------------------------------------------------------ hgdFall: the backward fall
  // args: { bg, land (landing time, on a downbeat), slow (slow-motion factor), x, y, h }
  Z.scene('hgdFall', {
    preload: a => [a.bg || BG + 'flowers_eye.png', A + 'fall_back.png', ...(a.pose2 ? [a.pose2.img] : [])],
    draw(ctx, S) {
      const a = S.args, t = S.t, t0 = S.shot.t0, land = a.land ?? t0 + 2.5;
      const pre = Math.min(t, land) - t0, post = Math.max(0, t - land);
      // camera: low angle, drifting down with her, kick on landing
      const view = { zoom: 1.12 + 0.05 * Z.clamp(pre / (land - t0)), x: 0, y: -0.6 + 0.9 * E.inOutSine(Z.clamp(pre / (land - t0))) };
      if (post > 0) { const [sx, sy] = D.shake(t, 10 * Math.exp(-post * 4), 24, 3); view.x += sx / 400; view.y += sy / 300; }
      G.plate(ctx, img(a.bg || BG + 'flowers_eye.png'), view, 0);
      // body: rigid pendulum about the heels under gravity (slow motion), then the drop out of frame
      const slow = a.slow ?? 0.32, g = 9.81, L = 1.6;               // metres, body length
      const T = pre * slow; let th = 0.12, om = 0;                     // integrate the pendulum (fixed dt, from the shot start)
      for (let s = 0; s < T; s += 1 / 240) { om += (g / L) * Math.sin(th) / 240; th += om / 240; if (th > 1.2) { th = 1.2; break; } }
      const hx = a.x ?? 900, hy = (a.y ?? 1000) + (post > 0 ? 900 * E.inQuad(Z.clamp(post / 0.6)) : 0), h = a.h ?? 900;
      const rot = -0.55 + th;                                           // the drawing already leans back ~45°
      G.drawChar(ctx, S, { img: A + 'fall_back.png', poses: a.pose2 ? [a.pose2] : null, smearDir: -1, x: hx, y: hy, h, rot, anchor: [0.62, 0.95], wind: -10, lagY: -60 - 40 * om, lagX: -30 * om, lag: false, flutter: 1, tilt: 0.02 });
      // petals: drifting up past the camera during the fall, a burst on the landing
      G.petals(ctx, t, { n: 30, size: 12, speed: 70 * (post > 0 ? 3 : 1), up: post <= 0, wind: 0.15 });
      if (post > 0) {
        for (let i = 0; i < 40; i++) {
          const an = -Math.PI / 2 + Z.rnds(i, 71) * 1.3, sp = 500 + 700 * Z.rnd(i, 72);
          const px = hx + Z.rnds(i, 73) * 300 + Math.cos(an) * sp * post, py = H - 40 + Math.sin(an) * sp * post + 900 * post * post;
          G.petalAt(ctx, px, py, 12 + 10 * Z.rnd(i, 74), an + post * 5, Math.cos(post * 7 + i), i % 3 ? P.carmine : P.rouge, Z.clamp(1 - post / 1.6));
        }
      }
      S.fall = { hx, hy, th };
      G.lyrics(ctx, S, 'front');
      G.sparkle(ctx, t, { n: 6, size: 22 });
      G.grain(ctx, 0.1);
    },
  });

  // ------------------------------------------------------------------ hgdMud: roots grow wildly on the beats
  const rootTree = (() => { let cache = null; return () => {
    if (cache) return cache;
    const R = Z.rng(808), segs = [];
    const grow = (x, y, a, len, depth, born) => {
      if (depth > 6 || len < 14) return;
      const n = 4 + Math.floor(R() * 4); let px = x, py = y, ang = a;
      for (let i = 0; i < n; i++) { ang += R.range(-0.35, 0.35); const nx = px + Math.cos(ang) * len / n * 1.6, ny = py + Math.sin(ang) * len / n * 1.6; segs.push({ x0: px, y0: py, x1: nx, y1: ny, w: Math.max(0.6, 4.5 - depth * 0.7), born: born + i * 0.06 + depth * 0.05 }); px = nx; py = ny; if (R() < 0.45) grow(px, py, ang + R.sign() * R.range(0.4, 1.1), len * 0.62, depth + 1, born + i * 0.06 + 0.12); }
    };
    for (let k = 0; k < 7; k++) grow(200 + k * 260 + R.range(-60, 60), -20, Math.PI / 2 + R.range(-0.4, 0.4), 620, 0, k * 0.11);
    cache = segs; return segs; }; })();
  Z.scene('hgdMud', {
    preload: a => [a.bg || BG + 'mud.png'],
    draw(ctx, S) {
      const a = S.args, t = S.t;
      G.plate(ctx, img(a.bg || BG + 'mud.png'), { zoom: 1.1 + 0.08 * S.p, y: -0.3 + 0.4 * S.p }, 0);
      D.fill(ctx, '#2A2230', 0.18, 'multiply');
      // growth advances in steps on the beats (wild, not smooth)
      const bs = beatsIn(S.shot.t0 - 1, t + 1e-6).filter(b => b <= t);
      const steps = bs.filter(b => b >= S.shot.t0).length, last = bs.length ? bs[bs.length - 1] : S.shot.t0;
      const prog = Z.clamp((steps + E.outExpo(Z.clamp((t - last) / 0.25))) / 8);
      ctx.save(); ctx.lineCap = 'round';
      for (const s of rootTree()) {
        const k = Z.clamp((prog - s.born * 0.55) / 0.12); if (k <= 0) continue;
        ctx.strokeStyle = 'rgba(244,236,222,0.85)'; ctx.lineWidth = s.w;
        ctx.beginPath(); ctx.moveTo(s.x0, s.y0); ctx.lineTo(Z.lerp(s.x0, s.x1, k), Z.lerp(s.y0, s.y1, k)); ctx.stroke();
      }
      ctx.restore();
      // a petal sinks into the mud
      const pk = Z.clamp((t - S.shot.t0) / S.dur);
      G.petalAt(ctx, 1240, 300 + 420 * E.inOutSine(pk), 34 * (1 - 0.5 * pk), 0.4 + pk, Math.cos(t * 1.4), P.carmine, 1 - 0.6 * pk);
      G.lyrics(ctx, S, 'front');
      G.grain(ctx, 0.14);
    },
  });

  // ------------------------------------------------------------------ hgdPage: silverfish eat through the page
  // args: { page (image printed on the page), under (what shows through the holes), bugs: n }
  const pageC = (() => { let c = null; return () => c || (c = Z.canvas(W, H)); })();
  Z.scene('hgdPage', {
    preload: a => [a.page || A + 'lying_flowers.png', a.under || BG + 'mud.png', PR + 'silverfish.png'],
    draw(ctx, S) {
      const a = S.args, t = S.t, lt = t - S.shot.t0;
      // under the page
      G.plate(ctx, img(a.under || BG + 'mud.png'), { zoom: 1.15 }, 0.5); D.fill(ctx, '#140F14', 0.45, 'multiply');
      // the page: the printed image on paper with a margin
      const pc = pageC(), x = pc.getContext('2d');
      x.setTransform(1, 0, 0, 1, 0, 0); x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1; x.clearRect(0, 0, W, H);
      x.fillStyle = '#F6F5F1'; x.fillRect(70, 50, W - 140, H - 100);
      D.cover(x, img(a.page || A + 'lying_flowers.png'), { zoom: 1.0 }, 1);
      x.globalCompositeOperation = 'destination-in'; x.fillStyle = '#000'; x.fillRect(70, 50, W - 140, H - 100); x.globalCompositeOperation = 'source-over';
      x.save(); x.globalCompositeOperation = 'multiply'; x.globalAlpha = 0.12; x.fillStyle = '#C8C2B4'; x.fillRect(0, 0, W, H); x.restore();
      x.save(); G.lyrics(x, S, 'page'); x.restore();
      // holes: the trails of the silverfish so far + bites on the beats
      const n = a.bugs ?? 4, sf = img(PR + 'silverfish.png');
      const route = (i, s) => { const y0 = 180 + i * 220 + 60 * Math.sin(i * 2.1), sp = 170 + 40 * Z.rnd(i, 5), dir = i % 2 ? -1 : 1; const xx = dir > 0 ? -120 + sp * s : W + 120 - sp * s; return [xx, y0 + 60 * Math.sin(s * 1.3 + i) + 20 * Math.sin(s * 3.1 + i)]; };
      x.save(); x.globalCompositeOperation = 'destination-out';
      for (let i = 0; i < n; i++) {
        for (let s = 0.3; s < lt; s += 0.05) { const [hx, hy] = route(i, s); G.blob(x, hx, hy, 22 + 18 * Math.min(1, (lt - s) * 0.8), i * 31 + Math.floor(s * 20), 0.35); x.fill(); }
      }
      for (const b of beatsIn(S.shot.t0, t)) { const j = Math.round(b * 2); const bx = 200 + Z.rnd(j, 91) * (W - 400), by = 150 + Z.rnd(j, 92) * (H - 300); G.blob(x, bx, by, 40 + 80 * Z.rnd(j, 93) * E.outCubic(Z.clamp((t - b) / 0.4)), j, 0.4); x.fill(); }
      x.restore();
      ctx.save(); ctx.shadowColor = 'rgba(20,10,10,0.5)'; ctx.shadowBlur = 18; ctx.drawImage(pc, 0, 0); ctx.restore();
      // the silverfish themselves (wiggle on 12 fps)
      for (let i = 0; i < n; i++) {
        const s = lt; const [hx, hy] = route(i, s), [nx, ny] = route(i, s + 0.05);
        const ang = Math.atan2(ny - hy, nx - hx) + Math.PI / 2;
        ctx.save(); ctx.translate(hx, hy); ctx.rotate(ang + 0.12 * Math.sin(Z.quant(t, 12) * 18 + i));
        D.sprite(ctx, sf, 0, 0, 120, { anchor: [0.5, 0.5] }); ctx.restore();
      }
      G.grain(ctx, 0.1);
    },
  });

  // ------------------------------------------------------------------ hgdDoll: drawing / paper doll on the beats
  Z.scene('hgdDoll', {
    preload: a => [a.char || A + 'bust_calm.png'],
    draw(ctx, S) {
      const a = S.args, t = S.t, im = img(a.char || A + 'bust_calm.png');
      D.vgrad(ctx, [[0, '#1B2742'], [1, '#0D1322']]);
      G.snow(ctx, t, { n: 40, size: 2, speed: 20, alpha: 0.35, rim: false });
      const beat = S.clock.beat(t), doll = ((beat % 2) + 2) % 2 === 1;
      const flip = Math.cos(Math.min(1, S.clock.since(t) / 0.12) * Math.PI);  // a quick card turn at each beat
      const h = 1000, x = 960, y = 1080;
      ctx.save(); ctx.translate(x, 0); ctx.scale(Math.max(0.05, Math.abs(flip)), 1); ctx.translate(-x, 0);
      if (doll) {
        // a flat paper cut-out of her: paper-white fill, a pencil outline, paper grain inside
        ctx.save(); ctx.globalAlpha = 0.9; G.puppet(ctx, G.tint(im, '#4A5872'), x + 6, y + 4, h, { t, wind: 4, rigName: a.char || A + 'bust_calm.png' }); ctx.restore();
        G.puppet(ctx, G.tint(im, '#F2F0EA'), x, y, h, { t, wind: 4, rigName: a.char || A + 'bust_calm.png' });
        G.lyrics(ctx, S, 'xray');
      } else {
        G.puppet(ctx, im, x, y, h, { t, wind: 8, tilt: 0.02 * Math.sin(t), rigName: a.char || A + 'bust_calm.png' });
        D.fill(ctx, '#2B3A66', 0.25, 'multiply');
      }
      ctx.restore();
      G.lyrics(ctx, S, 'front');
      G.sparkle(ctx, t, { n: 6, size: 18, dark: true });
      G.grain(ctx, 0.08, 'overlay');
    },
  });

  // ------------------------------------------------------------------ hgdBed: one bed (warm | split)
  // args: { mode, lie:{x,y,h,rot}, splitAt }
  Z.scene('hgdBed', {
    preload: () => [BG + 'bedroom.png', A + 'lying_side.png'],
    draw(ctx, S) {
      const a = S.args, t = S.t, mode = a.mode || 'warm';
      const render = (c) => {
        G.plate(c, img(BG + 'bedroom.png'), { zoom: 1.08 + 0.04 * S.p, x: 0.2, y: 0.1 }, 0);
        D.fill(c, '#22345E', 0.42, 'multiply');
        D.glow(c, 640, 470, 360, P.lamp, 0.35 + 0.05 * Math.sin(t * 2));
        const L = a.lie || { x: 980, y: 700, h: 260, rot: -0.04 };
        G.drawChar(c, S, { img: A + 'lying_side.png', x: L.x, y: L.y, h: L.h, rot: L.rot, wind: 2, lag: false, breathe: 1.4, anchor: [0.5, 0.5] });
        G.lyrics(c, S, 'bed');
        G.grain(c, 0.08);
      };
      if (mode === 'warm') { render(ctx); G.sparkle(ctx, t, { n: 6, size: 16, dark: true }); return; }
      const c = Z.scratch[1], x = c.getContext('2d'); x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, W, H); x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1; x.filter = 'none';
      render(x);
      const k = E.inOutCubic(Z.clamp((t - (a.splitAt ?? S.shot.t0 + 0.4)) / (S.dur * 0.8)));
      D.vgrad(ctx, [[0, '#0B1120'], [1, '#141E36']]);
      G.petals(ctx, t, { n: 16, size: 8, speed: 30, alpha: 0.7 });
      const mid = a.mid ?? 1000;
      ctx.save(); ctx.beginPath(); ctx.rect(0, 0, mid, H); ctx.clip(); ctx.translate(-230 * k, 50 * k); ctx.rotate(-0.05 * k); ctx.drawImage(c, 0, 0); D.fill(ctx, '#F2C48C', 0.12 * k, 'soft-light'); ctx.restore();
      ctx.save(); ctx.beginPath(); ctx.rect(mid, 0, W - mid, H); ctx.clip(); ctx.translate(230 * k, -50 * k); ctx.rotate(0.05 * k); ctx.drawImage(c, 0, 0); D.fill(ctx, '#3A6BC8', 0.18 * k, 'multiply'); ctx.restore();
      G.sparkle(ctx, t, { n: 8, size: 18, dark: true });
    },
  });

  // ------------------------------------------------------------------ hgdCalendar: solar-term pages flip one per beat
  const TERMS = ['惊蛰', '春分', '清明', '谷雨', '立夏', '小满', '芒种', '夏至', '小暑', '大暑', '立秋', '处暑', '白露', '秋分', '寒露', '霜降'];
  Z.scene('hgdCalendar', {
    preload: a => [a.bg || A + 'desk.png'],
    draw(ctx, S) {
      const a = S.args, t = S.t;
      G.plate(ctx, img(a.bg || A + 'desk.png'), { zoom: 1.12, x: -0.3 }, 0.85, 22);
      D.fill(ctx, '#0E1626', 0.28, 'multiply');
      const t0 = a.from ?? S.shot.t0, bs = Z.clock.beats.filter(b => b >= t0 - 1e-6);
      let i = 0; while (i < bs.length && bs[i] <= t) i++;
      const idx = Math.min(TERMS.length - 1, Math.max(0, i - 1 + (a.startIndex || 0))), last = bs[Math.max(0, i - 1)] ?? t0;
      const fk = Z.clamp((t - last) / 0.18);
      const cx = 960, cy = 560, pw = 620, ph = 760;
      const sp_note = (a.lyrics || []).some(l => l.z === 'note');
      const page = (j, sy) => {
        ctx.save(); ctx.translate(cx, cy - ph / 2); ctx.scale(1, sy); ctx.translate(-cx, -(cy - ph / 2));
        ctx.fillStyle = '#F7F7F3'; ctx.shadowColor = 'rgba(0,0,0,0.35)'; ctx.shadowBlur = 24; ctx.fillRect(cx - pw / 2, cy - ph / 2, pw, ph); ctx.shadowBlur = 0;
        ctx.fillStyle = P.carmine; ctx.fillRect(cx - pw / 2, cy - ph / 2, pw, 74);
        ctx.fillStyle = P.ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        D.font(ctx, 230, 'serif', 300); ctx.fillText(TERMS[j][0], cx, cy - 90); ctx.fillText(TERMS[j][1], cx, cy + 160);
        D.font(ctx, 22, 'mono', 500); ctx.fillStyle = P.deep; ctx.fillText(`${String(j + 3).padStart(2, '0')} / 24`, cx, cy + ph / 2 - 40);
        if (sp_note) { ctx.save(); ctx.translate(cx - pw / 2 + 70, cy + ph / 2 - 160); G.lyrics(ctx, S, 'note'); ctx.restore(); }
        // the date stamp, carmine ink
        ctx.save(); ctx.translate(cx + 190, cy + 250); ctx.rotate(-0.25); ctx.strokeStyle = Z.rgba(P.carmine, 0.85); ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(0, 0, 62, 0, Z.TAU); ctx.stroke(); ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(0, 0, 50, 0, Z.TAU); ctx.stroke(); D.font(ctx, 26, 'mono', 600); ctx.fillStyle = Z.rgba(P.carmine, 0.85); ctx.fillText('DONE', 0, 2); ctx.restore();
        ctx.restore();
      };
      page(Math.min(TERMS.length - 1, idx + 1), 1);
      if (fk < 1) page(idx, Math.cos(fk * Math.PI * 0.5)); else page(Math.min(TERMS.length - 1, idx + 1), 1);
      // rings
      ctx.save(); ctx.strokeStyle = '#9AA6B6'; ctx.lineWidth = 6; for (let r = -2; r <= 2; r++) { ctx.beginPath(); ctx.arc(cx + r * 110, cy - ph / 2, 16, Math.PI, 0); ctx.stroke(); } ctx.restore();
      G.grain(ctx, 0.1);
    },
  });

  // ------------------------------------------------------------------ hgdMemory: earlier shots as prints that burn away
  // args: { shots:[[id, t], ...], burns:[t...] }
  const memC = []; const memCanvas = i => memC[i] || (memC[i] = Z.canvas(W, H));
  Z.scene('hgdMemory', {
    async draw(ctx, S) {
      const a = S.args, t = S.t;
      G.paperFill(ctx, '#F7F8FA', '#E3E8EF');
      const list = a.shots || [];
      for (let i = 0; i < list.length; i++) { const [id, st] = list[i]; await Z.renderShot(id, st, memCanvas(i).getContext('2d')); }
      list.forEach(([id], i) => {
        void id;
        const bt = (a.burns || [])[i] ?? S.shot.t1, bk = Z.clamp((t - bt) / 0.6);
        const px = 360 + i * 600, py = 520 + (i % 2 ? 40 : -30), rot = (i - 1) * 0.06, pw = 520, ph = 330;
        ctx.save(); ctx.translate(px, py); ctx.rotate(rot);
        ctx.fillStyle = '#FBFBF8'; ctx.shadowColor = 'rgba(30,40,60,0.25)'; ctx.shadowBlur = 16; ctx.fillRect(-pw / 2 - 18, -ph / 2 - 18, pw + 36, ph + 70); ctx.shadowBlur = 0;
        ctx.save(); ctx.filter = 'grayscale(0.55) contrast(0.92) brightness(1.06)'; ctx.drawImage(memCanvas(i), -pw / 2, -ph / 2, pw, ph); ctx.restore();
        ctx.save(); ctx.translate(0, ph / 2 + 26); S.print = i; G.lyrics(ctx, S, 'print' + i); ctx.restore();
        if (bk > 0) {          // the print burns away from one corner: white hole with a carmine-brown rim
          ctx.save(); ctx.beginPath(); G.blob(ctx, pw / 2, ph / 2, 900 * E.inQuad(bk), 7 + i, 0.3); ctx.fillStyle = '#F7F8FA'; ctx.fill(); ctx.lineWidth = 7; ctx.strokeStyle = Z.rgba(P.blood, 0.55 * (1 - bk)); ctx.stroke(); ctx.restore();
        }
        ctx.restore();
      });
      G.lyrics(ctx, S, 'front');
      G.grain(ctx, 0.12);
    },
  });

  // ------------------------------------------------------------------ hgdBurst: one composed close-up per beat (chorus montage)
  // args: { times: [t...] (cut starts, usually beats), cuts: [{ img, plate, view, viewTo, bg: [top, bottom] | color, x, y, h, flip,
  //         tint: {color, a, comp}, lines, shock, flash: color, glyph: { line, i, x, y, size, color, fam } }], lyrics }
  Z.scene('hgdBurst', {
    preload: a => (a.cuts || []).flatMap(c => (c.plate ? [c.img] : charAssets(c))).filter(Boolean),
    draw(ctx, S) {
      const a = S.args, t = S.t, times = a.times || [S.shot.t0];
      let k = 0; while (k + 1 < times.length && times[k + 1] <= t + 1e-6) k++;
      const c = a.cuts[k % a.cuts.length], t0 = times[k], t1 = times[k + 1] ?? S.shot.t1, dt = t - t0, lp = Z.clamp(dt / Math.max(0.05, t1 - t0));
      const punch = 1 + (c.punch ?? 0.14) * Math.exp(-dt * 10);
      const im = img(c.img);
      if (c.plate) {
        const v = D.viewLerp(c.view || { zoom: 1.2 }, c.viewTo || c.view || { zoom: 1.3 }, E.outCubic(lp));
        v.zoom *= punch; D.cover(ctx, im, v);
      } else {
        if (Array.isArray(c.bg)) D.vgrad(ctx, [[0, c.bg[0]], [1, c.bg[1]]]); else D.fill(ctx, c.bg || P.frost, 1);
        if (c.lines) G.focusLines(ctx, t, { x: c.lx ?? W / 2, y: c.ly ?? H / 2, n: 80, inner: 300, color: c.lineColor || 'rgba(255,255,255,0.85)', alpha: 0.9 });
        const h = (c.h || 1300) * punch * Z.lerp(1, c.grow ?? 1.06, lp);
        G.drawChar(ctx, S, Object.assign({ x: c.x ?? W / 2, y: c.y ?? 1200, h: c.h || 1300, wind: c.wind ?? 50, gust: c.gust ?? 30, lag: false, flutter: 1.2 }, c, { h, y: (c.y ?? 1200) + (c.dy || 0) * lp }));
      }
      for (const tn of c.tint ? [c.tint] : []) D.fill(ctx, tn.color, tn.a ?? 0.4, tn.comp || 'multiply');
      if (c.plate && c.lines) G.focusLines(ctx, t, { n: 80, inner: 320, color: c.lineColor || 'rgba(255,255,255,0.8)', alpha: Z.clamp(1 - dt * 2) });
      if (c.shock) G.shock(ctx, t, t0, { x: c.sx ?? W / 2, y: c.sy ?? H / 2, r: 1100, w: 22 });
      if (c.glyph) {
        const L = G.lineInfo(c.glyph.line); const ch = L && L.chars[c.glyph.i];
        if (ch) { const gk = Z.clamp(dt / 0.12); if (gk > 0) { ctx.save(); ctx.translate(c.glyph.x ?? W * 0.75, c.glyph.y ?? H * 0.5); const sc = Z.lerp(1.6, 1, E.outExpo(gk)); ctx.scale(sc, sc); G.TYPE_FX.stamp(ctx, ch, c.glyph.size || 420, { color: c.glyph.color || P.carmine, fam: c.glyph.fam || 'brush', alpha: 0.95, comp: c.glyph.comp || 'source-over' }, { a: 1, e: 0, i: c.glyph.i, seed: 3 }); ctx.restore(); } }
      }
      G.lyrics(ctx, S, 'front');
      const fl = c.flash ?? (k === 0 ? '#FFFFFF' : null);
      if (fl && dt < 0.1) D.fill(ctx, fl, 0.75 * (1 - dt / 0.1));
      G.grain(ctx, 0.1);
    },
  });
})();
