/* engine/scenes/hgd_core.js — 花骨朵 film toolkit (anime_mv). Loaded after the template scenes, before hgd_scenes.js.
 *
 *   Z.HGD.P                 palette (frost / ice / slate / ink + carmine, the film's only saturated colour)
 *   Z.HGD.LYR, lyr(i)       lyric lines read at runtime from analysis/lyrics_mv.lrc by the timeline (never hard-coded)
 *   Z.HGD.ft(t)             "visual time": stands still inside the song's stops (FREEZE windows) — particles and
 *                           characters freeze in mid-air while the beat clock keeps the real time
 *   Z.HGD.puppet(...)       WebGL mesh deformer for the key drawings (NovelAI / Codex art): head tilt about the neck,
 *                           breathing, hair / braid / shawl on wind + a damped spring driven by the body's motion,
 *                           skirt flutter; face rigid, feet planted. Drawn motion on 12 fps (2コマ打ち).
 *   Z.HGD.springLag(...)    secondary-motion spring integrated from the shot start (fixed dt, deterministic)
 *   fx: snow, petals, sparkle (chromatic-aberration star glints that read on white), stains (carmine creeping in from
 *       the frame edges), inkBloom (dye spreading in water), grain (paper), blurred (cached rack-focus copies)
 *   transitions: 'smear' (directional motion smear, pose-to-pose), 'whiteout'
 * Everything is a pure function of song time t (seeded noise only).
 */
(() => {
  'use strict';
  const Z = window.Z, D = Z.draw, E = Z.ease;
  const W = 1920, H = 1080;
  const G = (Z.HGD = {});

  // ------------------------------------------------------------------ palette
  const P = (G.P = {
    ink: '#1A1D26', carmine: '#C8183C', rouge: '#E85A74', blood: '#8E1B2E', frost: '#F4F7FA', ice: '#D7E3EE',
    slate: '#8D9BAD', deep: '#4A5872', silver: '#C9CED6', paper: '#F6F6F2', skin: '#FFF1EA', night: '#121A2C',
    lamp: '#F2C48C', mud: '#3A2E2A', leaf: '#8FA58A',
  });

  // ------------------------------------------------------------------ Chinese faces for every toolkit font key
  Object.assign(Z.FONT, {
    mincho: '"Noto Serif SC"', minchoHeavy: '"Noto Serif SC"', serif: '"Noto Serif SC"', tokumin: '"Noto Serif SC"',
    gothic: '"Noto Sans SC"', sans: '"Noto Sans SC"', hand: '"Long Cang"', brush: '"Ma Shan Zheng"',
    cursive: '"Zhi Mang Xing"', song: '"ZCOOL XiaoWei"', dot: '"IBM Plex Mono"', mono: '"IBM Plex Mono"',
  });
  G.FONTS_TO_LOAD = ['200 64px "Noto Serif SC"', '300 64px "Noto Serif SC"', '500 64px "Noto Serif SC"', '700 64px "Noto Serif SC"',
    '900 64px "Noto Serif SC"', '300 64px "Noto Sans SC"', '500 64px "Noto Sans SC"', '400 64px "Ma Shan Zheng"',
    '400 64px "Zhi Mang Xing"', '400 64px "Long Cang"', '400 64px "ZCOOL XiaoWei"', '500 64px "IBM Plex Mono"'];

  // ------------------------------------------------------------------ lyrics (runtime only)
  G.LYR = [];
  G.lyr = i => (G.LYR[i - 1] || {}).text || '';
  G.parseLrc = (lrc) => {
    const out = [];
    for (const line of lrc.split(/\r?\n/)) {
      const m = line.match(/^\[(\d+):(\d+(?:\.\d+)?)\](.*)$/);
      if (!m) continue;
      const text = m[3].replace(/[\/*]/g, '').replace(/!+\s*$/, '').trim();
      if (!text || /^\[.*\]$/.test(text)) continue;
      out.push({ t: +m[1] * 60 + +m[2], text });
    }
    return out;
  };

  // ------------------------------------------------------------------ freeze windows (the intro stops)
  G.FREEZE = [];
  G.ft = (t) => {
    let shift = 0;
    for (const [a, b] of G.FREEZE) {
      if (t >= b) shift += b - a;
      else if (t >= a) return a - shift;
    }
    return t - shift;
  };

  // ------------------------------------------------------------------ physics helpers
  // damped spring: offset of a hanging mass (hair, shawl) in the frame of a body whose acceleration is acc(s) px/s^2
  G.springLag = (acc, t0, t, k = 55, c = 8.5, dt = 1 / 120) => {
    let y = 0, v = 0;
    const n = Math.min(1200, Math.max(0, Math.floor((t - t0) / dt)));
    for (let i = 0; i < n; i++) { const s = t0 + i * dt; const f = -k * y - c * v - acc(s); v += f * dt; y += v * dt; }
    return y;
  };
  G.acc = (posFn, s, h = 1 / 60) => (posFn(s + h) - 2 * posFn(s) + posFn(s - h)) / (h * h);
  // a step cycle locked to the beat: 0..1 per step, `steps` steps per beat
  G.stepPhase = (t, steps = 1) => { const b = Z.clock.beat(t) + Z.clock.phase(t); return Z.fract(b * steps); };

  // ------------------------------------------------------------------ puppet: WebGL mesh deformer
  const PUP = (() => {
    const SIZE = 2048;
    const cv = document.createElement('canvas'); cv.width = SIZE; cv.height = SIZE;
    const gl = cv.getContext('webgl2', { premultipliedAlpha: true, alpha: true, preserveDrawingBuffer: true, antialias: true });
    if (!gl) { console.warn('puppet: no WebGL2'); return null; }
    const vs = `#version 300 es
      in vec2 pos; in vec2 uv; uniform vec2 res; out vec2 vuv;
      void main(){ vuv = uv; vec2 c = pos / res * 2.0 - 1.0; gl_Position = vec4(c.x, -c.y, 0.0, 1.0); }`;
    const fs = `#version 300 es
      precision highp float; in vec2 vuv; uniform sampler2D img; uniform float alpha; out vec4 o;
      void main(){ o = texture(img, vuv) * alpha; }`;
    const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
    const pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, fs)); gl.linkProgram(pr);
    const loc = { pos: gl.getAttribLocation(pr, 'pos'), uv: gl.getAttribLocation(pr, 'uv'), res: gl.getUniformLocation(pr, 'res'), img: gl.getUniformLocation(pr, 'img'), alpha: gl.getUniformLocation(pr, 'alpha') };
    const GX = 22, GY = 40;
    const nv = (GX + 1) * (GY + 1);
    const vbuf = gl.createBuffer(), ibuf = gl.createBuffer();
    const idx = [];
    for (let j = 0; j < GY; j++) for (let i = 0; i < GX; i++) { const a = j * (GX + 1) + i, b = a + 1, c = a + GX + 1, d = c + 1; idx.push(a, b, c, b, d, c); }
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ibuf); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(idx), gl.STATIC_DRAW);
    const vao = gl.createVertexArray(); gl.bindVertexArray(vao);
    gl.bindBuffer(gl.ARRAY_BUFFER, vbuf); gl.bufferData(gl.ARRAY_BUFFER, nv * 4 * 4, gl.DYNAMIC_DRAW);
    gl.enableVertexAttribArray(loc.pos); gl.vertexAttribPointer(loc.pos, 2, gl.FLOAT, false, 16, 0);
    gl.enableVertexAttribArray(loc.uv); gl.vertexAttribPointer(loc.uv, 2, gl.FLOAT, false, 16, 8);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ibuf);
    const texCache = new Map();
    const tex = (img) => {
      let t = texCache.get(img); if (t) return t;
      t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
      gl.generateMipmap(gl.TEXTURE_2D);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      texCache.set(img, t); return t;
    };
    const data = new Float32Array(nv * 4);
    return {
      SIZE, cv, GX, GY,
      // fill vertices with fn(u, v) -> [px, py] in target pixels; render img into the top-left ow x oh of the canvas
      render(img, ow, oh, fn) {
        let k = 0;
        for (let j = 0; j <= GY; j++) for (let i = 0; i <= GX; i++) { const u = i / GX, v = j / GY; const [px, py] = fn(u, v); data[k++] = px; data[k++] = py; data[k++] = u; data[k++] = v; }
        gl.bindVertexArray(vao);
        gl.bindBuffer(gl.ARRAY_BUFFER, vbuf); gl.bufferSubData(gl.ARRAY_BUFFER, 0, data);
        gl.viewport(0, SIZE - oh, ow, oh);
        gl.enable(gl.SCISSOR_TEST); gl.scissor(0, SIZE - oh, ow, oh);
        gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
        gl.useProgram(pr); gl.uniform2f(loc.res, ow, oh); gl.uniform1f(loc.alpha, 1);
        gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex(img)); gl.uniform1i(loc.img, 0);
        gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
        gl.drawElements(gl.TRIANGLES, GX * GY * 6, gl.UNSIGNED_SHORT, 0);
        gl.disable(gl.SCISSOR_TEST);
      },
    };
  })();

  const sstep = (a, b, x) => { const k = Z.clamp((x - a) / (b - a)); return k * k * (3 - 2 * k); };
  // default rig for a standing full-body drawing (normalised image coords); per-image overrides in the timeline (G.RIG)
  G.RIG_DEFAULT = { neck: [0.5, 0.2], waist: 0.45, core: [0.5, 0.13], face: [0.36, 0.05, 0.64, 0.21], feet: 0.93, skirt: null };
  G.RIG = {};
  // o: { anchor, rot, flip, alpha, t, rig, tilt, breathe, wind, flutter, lagX, lagY, squash, phase, q }
  G.puppet = (ctx, img, x, y, h, o = {}) => {
    if (!img) return null;
    const s = h / img.height, w = img.width * s;
    const [ax, ay] = o.anchor || [0.5, 1];
    const rig = Object.assign({}, G.RIG_DEFAULT, G.RIG[o.rigName] || {}, o.rig || {});
    const q = o.q ?? 12, t = o.t ?? 0, tq = q ? Z.quant(t, q) : t, ph = o.phase || 0;
    const wind = o.wind ?? 0, lagX = o.lagX || 0, lagY = o.lagY || 0, flutter = o.flutter ?? 0.6;
    const tilt = o.tilt || 0, br = o.breathe ?? 1;
    const breath = br * Math.sin(t * 2.0 + ph);
    const m = Math.ceil(Math.min(420, Math.abs(wind) * 1.2 + Math.abs(lagX) * 1.2 + Math.abs(lagY) + 0.06 * h + 24));
    let ow = Math.ceil(w + 2 * m), oh = Math.ceil(h + 2 * m), f = 1;
    if (!PUP || ow > PUP.SIZE || oh > PUP.SIZE) { f = Math.min(PUP ? PUP.SIZE / ow : 1, PUP ? PUP.SIZE / oh : 1); }
    if (!PUP) { D.sprite(ctx, img, x, y, h, { anchor: o.anchor, rot: o.rot, flip: o.flip, alpha: o.alpha, t }); return null; }
    const rw = Math.floor(ow * f), rh = Math.floor(oh * f);
    const [nu, nv] = rig.neck, [cu, ch] = rig.core, [fu0, fv0, fu1, fv1] = rig.face;
    const nx = m + nu * w, ny = m + nv * h, ct = Math.cos(tilt), st = Math.sin(tilt);
    PUP.render(img, rw, rh, (u, v) => {
      let px = m + u * w, py = m + v * h;
      // head tilt about the neck (full above the neck, fading out just below it)
      const kh = sstep(nv + 0.05, nv - 0.06, v);
      if (kh > 0 && tilt) { const dx = px - nx, dy = py - ny, a = tilt * kh; const c = Math.cos(a), s2 = Math.sin(a); px = nx + dx * c - dy * s2; py = ny + dx * s2 + dy * c; }
      // breathing: chest widens a hair, shoulders rise
      if (v > nv && v < rig.waist) { const k = Math.sin(Math.PI * (v - nv) / (rig.waist - nv)); px += (u - cu) * w * 0.010 * breath * k; py -= 0.005 * breath * h * (1 - (v - nv) / (rig.waist - nv)); }
      // secondary motion: everything outside the body column and below the crown (hair, braid, shawl)
      const dc = Math.abs(u - cu) - ch;
      let wgt = sstep(0, 0.2, dc) * Math.pow(sstep(nv - 0.12, 1.0, v), 0.75);
      if (u > fu0 - 0.04 && u < fu1 + 0.04 && v > fv0 - 0.03 && v < fv1 + 0.03) wgt *= 0.15;   // keep the face drawn
      wgt *= 1 - sstep(rig.feet - 0.06, rig.feet, v) * (Math.abs(u - cu) < ch * 1.8 ? 1 : 0);  // planted feet
      if (wgt > 0) {
        const wave = Math.sin(Z.TAU * (0.85 * tq) - 6.5 * v + ph + u * 2.0);
        px += wgt * (wind * (0.62 + 0.38 * wave) + lagX + flutter * 6 * Math.sin(Z.TAU * 1.7 * tq - 9 * v + ph));
        py += wgt * (lagY * 0.7 + 0.1 * Math.abs(wind) * Math.sin(Z.TAU * 1.2 * tq - 5 * v + 1.7 + ph));
      }
      // skirt hem flutter
      if (rig.skirt) { const [s0, s1] = rig.skirt; const ks = sstep(s0, s1, v) * (1 - sstep(s1, s1 + 0.05, v)); if (ks > 0) px += ks * (flutter * 5 + Math.abs(wind) * 0.12) * Math.sin(Z.TAU * 1.4 * tq + u * 9 + ph); }
      return [px * f, py * f];
    });
    ctx.save();
    ctx.globalAlpha *= o.alpha ?? 1;
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
    ctx.translate(x, y);
    if (o.rot) ctx.rotate(o.rot);
    const sq = o.squash || 0;
    ctx.scale((o.flip ? -1 : 1) * (1 + sq * 0.5), 1 - sq);
    ctx.drawImage(PUP.cv, 0, 0, rw, rh, -m - ax * w, -m - ay * h, ow, oh);
    ctx.restore();
    return { w, h };
  };

  // ------------------------------------------------------------------ cached helpers
  let idN = 0; const idOf = img => img.__id || (img.__id = 'i' + (++idN));   // cache keys only (no randomness)
  const tintCache = new Map();
  G.tint = (img, color) => Z.tinted(img, color, 'hgd' + (img.width + 'x' + img.height) + idOf(img));
  const blurCache = new Map();
  // a blurred copy (rack focus): drawn small with a canvas blur, upscaled when used
  G.blurred = (img, r) => {
    const key = idOf(img) + '|' + r;
    let c = blurCache.get(key); if (c) return c;
    const sc = 0.25; c = Z.canvas(Math.max(8, Math.round(img.width * sc)), Math.max(8, Math.round(img.height * sc)));
    const x = c.getContext('2d'); x.filter = `blur(${Math.max(0.5, r * sc)}px)`; x.drawImage(img, 0, 0, c.width, c.height);
    blurCache.set(key, c); return c;
  };
  void tintCache;

  // ------------------------------------------------------------------ paper grain (multiply)
  let grainC = null;
  G.grain = (ctx, a = 0.1, comp = 'multiply') => {
    if (!grainC) {
      grainC = Z.canvas(512, 512); const x = grainC.getContext('2d'); const id = x.createImageData(512, 512); const R = Z.rng(77);
      for (let i = 0; i < id.data.length; i += 4) { const v = 238 + Math.floor(R() * 17) - (R() < 0.015 ? 26 : 0); id.data[i] = v; id.data[i + 1] = v + 1; id.data[i + 2] = v + 3; id.data[i + 3] = 255; }
      x.putImageData(id, 0, 0);
      x.globalAlpha = 0.18; x.strokeStyle = '#8d97a6';
      for (let i = 0; i < 260; i++) { x.beginPath(); const sx = R() * 512, sy = R() * 512, an = R() * Math.PI; x.moveTo(sx, sy); x.lineTo(sx + Math.cos(an) * (6 + R() * 28), sy + Math.sin(an) * (6 + R() * 28)); x.lineWidth = 0.4 + R() * 0.8; x.stroke(); }
    }
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalCompositeOperation = comp; ctx.globalAlpha = a;
    ctx.fillStyle = ctx.createPattern(grainC, 'repeat'); ctx.fillRect(0, 0, W, H); ctx.restore();
  };

  // ------------------------------------------------------------------ snow (closed form; visible on white: faint slate rims)
  G.snow = (ctx, t, o = {}) => {
    const n = o.n ?? 160, seed = o.seed ?? 3, wind = o.wind ?? 0.25, sp = o.speed ?? 120, a0 = o.alpha ?? 1;
    const [x0, y0, x1, y1] = o.area || [-200, -60, W + 200, H + 60];
    ctx.save();
    for (let i = 0; i < n; i++) {
      const d = Z.rnd(i, seed), size = (o.size ?? 4) * (0.35 + 1.9 * d * d), v = sp * (0.35 + 0.95 * d);
      const span = y1 - y0, wx = x1 - x0;
      const y = y0 + Z.fract(Z.rnd(i, seed + 2) + t * v / span) * span;
      const xr = Z.rnd(i, seed + 1) * wx + wind * v * t + Math.sin(t * (0.6 + d) + i) * 26 * (0.4 + d);
      const x = x0 + ((xr % wx) + wx) % wx;
      const al = a0 * (0.45 + 0.55 * d);
      ctx.globalAlpha = al;
      ctx.beginPath(); ctx.arc(x, y, size, 0, Z.TAU);
      ctx.fillStyle = o.color || '#FFFFFF'; ctx.fill();
      if (o.rim !== false) { ctx.lineWidth = Math.max(0.6, size * 0.18); ctx.strokeStyle = o.rimColor || 'rgba(120,138,168,0.55)'; ctx.stroke(); }
    }
    ctx.restore();
  };

  // ------------------------------------------------------------------ petals (carmine, tumbling: the scale-x flip fakes 3D)
  const petalPath = (ctx, s) => { ctx.beginPath(); ctx.moveTo(0, -s); ctx.bezierCurveTo(s * 0.9, -s * 0.7, s * 0.8, s * 0.6, 0, s); ctx.bezierCurveTo(-s * 0.7, s * 0.5, -s * 0.8, -s * 0.6, 0, -s); };
  G.petals = (ctx, t, o = {}) => {
    const n = o.n ?? 40, seed = o.seed ?? 9, sp = o.speed ?? 90, wind = o.wind ?? 0.35, a0 = o.alpha ?? 1;
    const [x0, y0, x1, y1] = o.area || [-200, -80, W + 200, H + 80];
    const cols = o.colors || [P.carmine, P.rouge, '#B3122F'];
    ctx.save();
    for (let i = 0; i < n; i++) {
      const d = Z.rnd(i, seed), s = (o.size ?? 13) * (0.5 + 1.1 * d), v = sp * (0.5 + 0.8 * d) * (o.up ? -1 : 1);
      const span = y1 - y0, wx = x1 - x0;
      const y = y0 + Z.fract(Z.rnd(i, seed + 2) + t * v / span) * span;
      const xr = Z.rnd(i, seed + 1) * wx + wind * Math.abs(v) * t + Math.sin(t * (0.9 + d) + i * 1.3) * 60;
      const x = x0 + ((xr % wx) + wx) % wx;
      ctx.save(); ctx.translate(x, y); ctx.rotate(t * (0.6 + 1.6 * Z.rnd(i, seed + 3)) + i);
      ctx.scale(Math.cos(t * (1.5 + 2 * Z.rnd(i, seed + 4)) + i), 1);
      ctx.globalAlpha = a0 * (0.55 + 0.45 * d);
      petalPath(ctx, s); ctx.fillStyle = cols[i % cols.length]; ctx.fill();
      ctx.lineWidth = 0.8; ctx.strokeStyle = 'rgba(90,10,25,0.35)'; ctx.stroke();
      ctx.restore();
    }
    ctx.restore();
  };
  G.petalAt = (ctx, x, y, s, rot, flip, color, a = 1) => { ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(flip, 1); ctx.globalAlpha *= a; petalPath(ctx, s); ctx.fillStyle = color; ctx.fill(); ctx.lineWidth = 0.8; ctx.strokeStyle = 'rgba(90,10,25,0.35)'; ctx.stroke(); ctx.restore(); };

  // ------------------------------------------------------------------ sparkle with chromatic aberration (reads on white and on dark)
  const star = (ctx, x, y, L, w) => {
    ctx.beginPath();
    for (let k = 0; k < 8; k++) { const a = k * Math.PI / 4 - Math.PI / 2, r = k % 2 === 0 ? (k % 4 === 0 ? L : L * 0.62) : w; ctx.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r); }
    ctx.closePath();
  };
  G.sparkle = (ctx, t, o = {}) => {
    const n = o.n ?? 26, seed = o.seed ?? 5, rate = o.rate ?? 0.6, size = o.size ?? 22, dark = !!o.dark;
    const [x0, y0, x1, y1] = o.area || [0, 0, W, H];
    const tq = Z.quant(t, 12);
    ctx.save();
    for (let i = 0; i < n; i++) {
      const life = 1 / (rate * (0.5 + Z.rnd(i, seed + 3)));
      const k = Z.fract(tq / life + Z.rnd(i, seed + 4)), cyc = Math.floor(tq / life + Z.rnd(i, seed + 4));
      const a = Math.pow(Math.sin(Math.PI * k), 3) * (o.alpha ?? 1);
      if (a < 0.03) continue;
      const x = Z.lerp(x0, x1, Z.rnd(i, seed, cyc)), y = Z.lerp(y0, y1, Z.rnd(i, seed + 1, cyc));
      const L = size * (0.5 + Z.rnd(i, seed + 2)) * (0.6 + 0.4 * Math.sin(Math.PI * k)), wd = L * 0.07, off = Math.max(1.5, L * 0.08);
      if (dark) {
        ctx.globalCompositeOperation = 'lighter';
        for (const [dx, col] of [[-off, '255,70,110'], [0, '255,255,255'], [off, '70,200,255']]) { ctx.globalAlpha = a * (dx ? 0.55 : 0.9); star(ctx, x + dx, y, L, wd); ctx.fillStyle = `rgb(${col})`; ctx.fill(); }
      } else {
        ctx.globalCompositeOperation = 'source-over';
        ctx.globalAlpha = a * 0.65; star(ctx, x - off, y, L, wd); ctx.fillStyle = 'rgb(255,92,128)'; ctx.fill();
        ctx.globalAlpha = a * 0.65; star(ctx, x + off, y, L, wd); ctx.fillStyle = 'rgb(70,170,255)'; ctx.fill();
        ctx.globalAlpha = a; star(ctx, x, y, L * 0.92, wd * 0.8); ctx.fillStyle = '#FFFFFF'; ctx.fill();
        ctx.lineWidth = 0.7; ctx.strokeStyle = `rgba(110,128,160,${0.5 * a})`; ctx.stroke();
      }
    }
    ctx.restore();
  };

  // ------------------------------------------------------------------ noisy blob (watercolour) + dye bloom + edge stains
  G.blob = (ctx, cx, cy, r, seed, wob = 0.22, t = 0) => {
    ctx.beginPath();
    const N = 36;
    for (let i = 0; i <= N; i++) {
      const a = (i / N) * Z.TAU;
      const rr = r * (1 + wob * Z.fbm1(Math.cos(a) * 1.7 + Math.sin(a) * 1.3 + 7 + t * 0.15, seed, 3) + 0.5 * wob * Z.noise1(a * 3 + seed, seed + 3));
      const x = cx + Math.cos(a) * rr, y = cy + Math.sin(a) * rr;
      if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y);
    }
    ctx.closePath();
  };
  // dye spreading in water: k 0..1 growth; layers of noisy discs, darker rims (multiply on light frames)
  G.inkBloom = (ctx, cx, cy, R, k, o = {}) => {
    if (k <= 0) return;
    const seed = o.seed ?? 3, col = o.color || P.carmine, a = o.alpha ?? 0.85, t = o.t ?? 0;
    ctx.save(); ctx.globalCompositeOperation = o.comp || 'multiply';
    for (let l = 0; l < 5; l++) {
      const kk = Z.clamp(k * (1.15 - l * 0.12)), r = R * E.outCubic(kk) * (0.45 + l * 0.14);
      if (r < 1) continue;
      G.blob(ctx, cx + Z.rnds(l, seed) * R * 0.08, cy + Z.rnds(l, seed + 1) * R * 0.08, r, seed + l * 13, 0.28, t);
      const g = ctx.createRadialGradient(cx, cy, r * 0.1, cx, cy, r);
      g.addColorStop(0, Z.rgba(col, a * 0.55)); g.addColorStop(0.75, Z.rgba(col, a * 0.32)); g.addColorStop(1, Z.rgba(col, a * 0.5));
      ctx.fillStyle = g; ctx.fill();
      ctx.lineWidth = 2 + l; ctx.strokeStyle = Z.rgba(P.blood, a * 0.18); ctx.stroke();
    }
    ctx.restore();
  };
  // carmine stains creeping in from the frame edges: amount 0..1 (grows through the film)
  G.stains = (ctx, amount, o = {}) => {
    if (amount <= 0) return;
    const n = o.n ?? 40, seed = o.seed ?? 21, t = o.t ?? 0, sc = o.scale ?? 1;
    ctx.save(); ctx.globalCompositeOperation = 'multiply';
    for (let i = 0; i < n; i++) {
      const birth = Z.rnd(i, seed + 2) * 0.85, g = Z.clamp((amount - birth) / 0.35);
      if (g <= 0) continue;
      const side = i % 4, along = Z.rnd(i, seed), out = 10 + 50 * Z.rnd(i, seed + 1);
      const cx = side === 0 ? along * W : side === 1 ? W + out : side === 2 ? along * W : -out;
      const cy = side === 0 ? -out : side === 1 ? along * H : side === 2 ? H + out : along * H;
      const r = (50 + 170 * Z.rnd(i, seed + 3) * Z.rnd(i, seed + 4)) * E.outCubic(g) * sc;
      // pale wash
      G.blob(ctx, cx, cy, r, seed + i * 7, 0.42, t * 0.3);
      ctx.fillStyle = Z.rgba(P.rouge, 0.16 + 0.1 * g); ctx.fill();
      // the tide line where the dye dried (darker, broken)
      ctx.setLineDash([r * 0.35, r * 0.06, r * 0.12, r * 0.05]); ctx.lineWidth = 1.2 + 1.6 * Z.rnd(i, seed + 5);
      ctx.strokeStyle = Z.rgba(P.carmine, 0.38 * g); ctx.stroke(); ctx.setLineDash([]);
      // a denser core near the edge it came from
      G.blob(ctx, cx, cy, r * 0.45, seed + i * 7 + 3, 0.5, t * 0.3); ctx.fillStyle = Z.rgba(P.carmine, 0.14 * g); ctx.fill();
      // speckles thrown off
      for (let j = 0; j < 5; j++) { const an = Z.rnd(i, j, seed + 6) * Z.TAU, d = r * (1.05 + 0.4 * Z.rnd(i, j, seed + 7)); ctx.beginPath(); ctx.arc(cx + Math.cos(an) * d, cy + Math.sin(an) * d, 1 + 3 * Z.rnd(i, j, seed + 8), 0, Z.TAU); ctx.fillStyle = Z.rgba(P.carmine, 0.3 * g); ctx.fill(); }
    }
    ctx.restore();
  };

  // ------------------------------------------------------------------ background plate with camera and rack focus
  // view: {zoom,x,y,rot}; focus 0 = sharp, 1 = fully blurred (cross-fades a cached blurred copy)
  G.plate = (ctx, img, view, focus = 0, blurR = 18) => {
    if (focus < 0.99) D.cover(ctx, img, view);
    if (focus > 0.01) D.cover(ctx, G.blurred(img, blurR), view, Z.clamp(focus));
  };

  // ------------------------------------------------------------------ high-key sky / paper fills
  G.paperFill = (ctx, top = P.frost, bottom = '#E9EEF4') => D.vgrad(ctx, [[0, top], [1, bottom]]);

  // ------------------------------------------------------------------ impact: 集中線 (focus lines) converging on a point, on 12 fps
  G.focusLines = (ctx, t, o = {}) => {
    const cx = o.x ?? W / 2, cy = o.y ?? H / 2, n = o.n ?? 90, q = Math.floor(t * 12), inner = o.inner ?? 260, a0 = o.alpha ?? 1;
    ctx.save(); ctx.fillStyle = o.color || '#0A0D14'; ctx.globalAlpha = a0;
    for (let i = 0; i < n; i++) {
      const an = (i / n) * Z.TAU + Z.rnds(i, q, 3) * 0.03, w = 0.004 + 0.016 * Z.rnd(i, q, 4), r0 = inner * (0.8 + 0.6 * Z.rnd(i, q, 5)), r1 = 1600;
      ctx.beginPath(); ctx.moveTo(cx + Math.cos(an) * r0, cy + Math.sin(an) * r0);
      ctx.lineTo(cx + Math.cos(an - w) * r1, cy + Math.sin(an - w) * r1); ctx.lineTo(cx + Math.cos(an + w) * r1, cy + Math.sin(an + w) * r1); ctx.closePath(); ctx.fill();
    }
    ctx.restore();
  };
  // impact windows set by the timeline: [{ t, dur, style: 'neg' | 'red' | 'lines', x, y }]
  G.IMPACTS = [];
  G.impactAt = (t) => G.IMPACTS.find(i => t >= i.t && t < i.t + (i.dur ?? 0.12)) || null;
  G.impactOverlay = (ctx, S) => {
    const im = G.impactAt(S.t); if (!im) return;
    G.focusLines(ctx, S.t, { x: im.x, y: im.y, n: im.n ?? 110, inner: im.inner ?? 220, color: im.style === 'red' ? '#8E1B2E' : '#0A0D14', alpha: im.alpha ?? 0.85 });
  };

  // ------------------------------------------------------------------ depth: huge out-of-focus things passing the lens
  G.fgPetals = (ctx, t, o = {}) => {
    const n = o.n ?? 5, seed = o.seed ?? 41, sp = o.speed ?? 520, dir = o.dir ?? 1;
    ctx.save();
    for (let i = 0; i < n; i++) {
      const s = (o.size ?? 120) * (0.6 + 0.9 * Z.rnd(i, seed)), life = (W + 600) / (sp * (0.6 + 0.8 * Z.rnd(i, seed + 1)));
      const k = Z.fract(t / life + Z.rnd(i, seed + 2)), x = dir > 0 ? -300 + k * (W + 600) : W + 300 - k * (W + 600);
      const y = H * (0.1 + 0.8 * Z.rnd(i, seed + 3)) + Math.sin(t * 1.3 + i) * 60;
      ctx.save(); ctx.translate(x, y); ctx.rotate(t * (0.5 + Z.rnd(i, seed + 4)) + i); ctx.scale(Math.cos(t * 1.7 + i), 1);
      for (const [sc, al] of [[1.35, 0.12], [1.15, 0.18], [1, 0.35]]) {   // soft edge without a blur filter
        ctx.globalAlpha = al * (o.alpha ?? 1); ctx.beginPath(); ctx.moveTo(0, -s * sc); ctx.bezierCurveTo(s * 0.9 * sc, -s * 0.7 * sc, s * 0.8 * sc, s * 0.6 * sc, 0, s * sc); ctx.bezierCurveTo(-s * 0.7 * sc, s * 0.5 * sc, -s * 0.8 * sc, -s * 0.6 * sc, 0, -s * sc);
        ctx.fillStyle = o.color || P.carmine; ctx.fill();
      }
      ctx.restore();
    }
    ctx.restore();
  };
  G.fgSnow = (ctx, t, o = {}) => {
    const n = o.n ?? 14, seed = o.seed ?? 51, sp = o.speed ?? 380, wind = o.wind ?? 0.6;
    ctx.save();
    for (let i = 0; i < n; i++) {
      const r = (o.size ?? 40) * (0.5 + 1.2 * Z.rnd(i, seed)), v = sp * (0.6 + 0.8 * Z.rnd(i, seed + 1));
      const y = Z.fract(Z.rnd(i, seed + 2) + t * v / (H + 400)) * (H + 400) - 200;
      const x = ((Z.rnd(i, seed + 3) * (W + 400) + wind * v * t) % (W + 400) + (W + 400)) % (W + 400) - 200;
      const g = ctx.createRadialGradient(x, y, 0, x, y, r);
      g.addColorStop(0, `rgba(255,255,255,${0.75 * (o.alpha ?? 1)})`); g.addColorStop(0.55, `rgba(240,246,255,${0.35 * (o.alpha ?? 1)})`); g.addColorStop(1, 'rgba(240,246,255,0)');
      ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2);
      ctx.globalAlpha = 0.25 * (o.alpha ?? 1); ctx.lineWidth = 1; ctx.strokeStyle = 'rgba(120,138,168,0.6)'; ctx.beginPath(); ctx.arc(x, y, r * 0.55, 0, Z.TAU); ctx.stroke(); ctx.globalAlpha = 1;
    }
    ctx.restore();
  };
  // light shafts through a window (screen) and soft light leaks
  G.shafts = (ctx, t, o = {}) => {
    const x = o.x ?? W * 0.8, y = o.y ?? -100, n = o.n ?? 6, ang = o.angle ?? 2.2, len = o.len ?? 1900, a0 = o.alpha ?? 0.35;
    ctx.save(); ctx.globalCompositeOperation = o.comp || 'screen';
    for (let i = 0; i < n; i++) {
      const off = (i - n / 2) * (o.gap ?? 70) + Math.sin(t * 0.4 + i) * 12, w = (o.width ?? 60) * (0.6 + 0.8 * Z.rnd(i, 7));
      const ax = Math.cos(ang), ay = Math.sin(ang), px = -ay, py = ax;
      const x0 = x + px * off, y0 = y + py * off, x1 = x0 + ax * len, y1 = y0 + ay * len;
      const g = ctx.createLinearGradient(x0, y0, x1, y1);
      const al = a0 * (0.6 + 0.4 * Math.sin(t * 0.7 + i * 1.3));
      g.addColorStop(0, `rgba(${o.rgb || '255,248,235'},${al})`); g.addColorStop(1, `rgba(${o.rgb || '255,248,235'},0)`);
      ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(x0 - px * w / 2, y0 - py * w / 2); ctx.lineTo(x0 + px * w / 2, y0 + py * w / 2);
      ctx.lineTo(x1 + px * w * 1.6, y1 + py * w * 1.6); ctx.lineTo(x1 - px * w * 1.6, y1 - py * w * 1.6); ctx.closePath(); ctx.fill();
    }
    ctx.restore();
  };
  G.leak = (ctx, t, o = {}) => {
    ctx.save(); ctx.globalCompositeOperation = o.comp || 'screen';
    const blobs = o.blobs || [[0.15, 0.2, '255,214,196'], [0.85, 0.75, '196,224,255']];
    blobs.forEach(([fx, fy, rgb], i) => {
      const x = W * fx + Math.sin(t * 0.3 + i * 2) * 140, y = H * fy + Math.cos(t * 0.27 + i) * 90, r = (o.r ?? 700) * (0.8 + 0.2 * Math.sin(t * 0.5 + i));
      const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, `rgba(${rgb},${o.alpha ?? 0.45})`); g.addColorStop(1, `rgba(${rgb},0)`);
      ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2);
    });
    ctx.restore();
  };
  // a shockwave ring with chromatic fringes, from time t0
  G.shock = (ctx, t, t0, o = {}) => {
    const d = t - t0; if (d < 0 || d > (o.life ?? 0.6)) return;
    const k = E.outCubic(d / (o.life ?? 0.6)), r = (o.r ?? 900) * k, x = o.x ?? W / 2, y = o.y ?? H / 2;
    ctx.save(); ctx.lineWidth = (o.w ?? 18) * (1 - k);
    for (const [dx, col] of [[-5, '255,80,110'], [5, '80,180,255'], [0, o.rgb || '255,255,255']]) { ctx.strokeStyle = `rgba(${col},${(1 - k) * 0.85})`; ctx.beginPath(); ctx.arc(x + dx, y, r, 0, Z.TAU); ctx.stroke(); }
    ctx.restore();
  };

  // ------------------------------------------------------------------ transitions
  // smear: A streaks in the motion direction and fades as B snaps in with a small overshoot (pose-to-pose cut)
  Z.transition('smear', (ctx, A, B, k, o) => {
    const dir = o.dir ?? 1, n = 6;
    ctx.save();
    ctx.drawImage(B, 0, 0);
    const ka = 1 - E.outQuad(k);
    for (let i = 0; i < n; i++) {
      ctx.globalAlpha = ka * (1 / n) * 1.6;
      const dx = dir * (k * 260 + i * 26) , sx = 1 + 0.06 * k * i / n;
      ctx.drawImage(A, dx - (sx - 1) * W / 2, 0, W * sx, H);
    }
    ctx.restore();
  });
  // whip: A whips off sideways with motion blur, B whips in from the other side and settles
  Z.transition('whip', (ctx, A, B, k, o) => {
    const dir = o.dir ?? -1, e = E.inOutCubic(k), off = dir * W * e, n = 6, blur = Math.sin(Math.PI * k);
    ctx.save();
    for (let j = n; j >= 0; j--) {
      const sm = j * 34 * blur * -dir;
      ctx.globalAlpha = j ? 0.14 * blur : 1;
      ctx.drawImage(A, off + sm, 0); ctx.drawImage(B, off - dir * W + sm, 0);
    }
    ctx.restore();
  });
  // whiteout: A dissolves into paper white, B emerges from it
  Z.transition('whiteout', (ctx, A, B, k, o) => {
    ctx.save();
    if (k < 0.5) { ctx.drawImage(A, 0, 0); ctx.globalAlpha = E.inOutSine(k * 2); ctx.fillStyle = o.color || P.frost; ctx.fillRect(0, 0, W, H); }
    else { ctx.drawImage(B, 0, 0); ctx.globalAlpha = 1 - E.inOutSine((k - 0.5) * 2); ctx.fillStyle = o.color || P.frost; ctx.fillRect(0, 0, W, H); }
    ctx.restore();
  });
})();
