// VIRUS2027 "signal" renderer: 3D scene -> ASCII-digit dither -> clean line layer -> HUD -> analog/CRT pass.
// Deterministic: window.renderAt(t) draws the frame for time t (seconds).
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';
import * as FX from './fx.js';

const W = 1080, H = 1920;
export const PAL = {
  bg: new THREE.Color('#090806'), paper: new THREE.Color('#e8e3db'),
  signal: new THREE.Color('#ff531f'), soft: '#b8b2aa', muted: '#77726b',
};

const canvas = document.getElementById('out');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.autoClear = false;

const rtOpts = { type: THREE.HalfFloatType, samples: 4 };
const rtScene = new THREE.WebGLRenderTarget(W, H, rtOpts);
const rtLines = new THREE.WebGLRenderTarget(W, H, rtOpts);
const rtComp = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType });

// ---------- glyph atlas (digits sorted by ink coverage) ----------
const CELL = { w: 9, h: 14 };
function buildGlyphAtlas() {
  const chars = ' .:-1774235069 8'.split('').filter((c, i, a) => a.indexOf(c) === i);
  const gw = 28, gh = 44;
  const c = document.createElement('canvas');
  const g = c.getContext('2d', { willReadFrequently: true });
  c.width = gw; c.height = gh;
  const cov = chars.map(ch => {
    g.clearRect(0, 0, gw, gh); g.fillStyle = '#000'; g.fillRect(0, 0, gw, gh);
    g.fillStyle = '#fff'; g.font = '600 38px "IBM Plex Mono"'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText(ch, gw / 2, gh / 2 + 2);
    const d = g.getImageData(0, 0, gw, gh).data; let s = 0;
    for (let i = 0; i < d.length; i += 4) s += d[i];
    return { ch, s };
  }).sort((a, b) => a.s - b.s);
  const atlas = document.createElement('canvas');
  atlas.width = gw * cov.length; atlas.height = gh;
  const ag = atlas.getContext('2d');
  ag.fillStyle = '#000'; ag.fillRect(0, 0, atlas.width, gh);
  ag.fillStyle = '#fff'; ag.font = '600 38px "IBM Plex Mono"'; ag.textAlign = 'center'; ag.textBaseline = 'middle';
  cov.forEach((o, i) => ag.fillText(o.ch, i * gw + gw / 2, gh / 2 + 2));
  const tex = new THREE.CanvasTexture(atlas);
  tex.minFilter = THREE.LinearMipmapLinearFilter; tex.magFilter = THREE.LinearFilter;
  return { tex, n: cov.length };
}

// ---------- HUD canvas ----------
const hudCanvas = document.createElement('canvas');
hudCanvas.width = W; hudCanvas.height = H;
const hud = hudCanvas.getContext('2d');
const hudTex = new THREE.CanvasTexture(hudCanvas);
hudTex.colorSpace = THREE.NoColorSpace; // sampled raw (display space)
const srgbVec = hex => new THREE.Vector3(((hex >> 16) & 255) / 255, ((hex >> 8) & 255) / 255, (hex & 255) / 255);

// ---------- passes ----------
const quadGeo = new THREE.PlaneGeometry(2, 2);
const quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
const VERT = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }`;

const compMat = new THREE.ShaderMaterial({
  uniforms: {
    tScene: { value: rtScene.texture }, tLines: { value: rtLines.texture }, tHud: { value: hudTex },
    tGlyph: { value: null }, nGlyph: { value: 1 }, res: { value: new THREE.Vector2(W, H) },
    cell: { value: new THREE.Vector2(CELL.w, CELL.h) }, light: { value: 0 },
    bg: { value: srgbVec(0x090806) }, paper: { value: srgbVec(0xe8e3db) }, signal: { value: srgbVec(0xff531f) },
    mixTone: { value: 0.25 }, asciiAmt: { value: 1 }, lo: { value: 0.05 }, hi: { value: 1.0 },
  },
  vertexShader: VERT,
  fragmentShader: `
    precision highp float; varying vec2 vUv;
    uniform sampler2D tScene, tLines, tHud, tGlyph; uniform float nGlyph, light, mixTone, asciiAmt, lo, hi;
    uniform vec2 res, cell; uniform vec3 bg, paper, signal;
    vec3 lin2srgb(vec3 c){ return pow(max(c,0.), vec3(1./2.2)); }
    vec3 srgb2lin(vec3 c){ return pow(max(c,0.), vec3(2.2)); }
    void main(){
      vec2 px = vUv * res;
      vec2 cid = floor(px / cell);
      vec2 c0 = cid * cell;
      // average 4 taps inside the cell (scene RT is linear -> convert to display space)
      vec3 col = vec3(0.);
      col += texture2D(tScene, (c0 + cell*vec2(.25,.25)) / res).rgb;
      col += texture2D(tScene, (c0 + cell*vec2(.75,.25)) / res).rgb;
      col += texture2D(tScene, (c0 + cell*vec2(.25,.75)) / res).rgb;
      col += texture2D(tScene, (c0 + cell*vec2(.75,.75)) / res).rgb;
      col = lin2srgb(col * .25);
      vec3 fine = lin2srgb(texture2D(tScene, vUv).rgb);
      float l = dot(col, vec3(.299,.587,.114));
      float lf = dot(fine, vec3(.299,.587,.114));
      float sig = smoothstep(.18,.38, col.r - col.b) * smoothstep(.10,.22, col.r - col.g);
      float sigF = smoothstep(.18,.38, fine.r - fine.b) * smoothstep(.10,.22, fine.r - fine.g);
      float v = light > .5 ? 1. - l : l;
      float d = smoothstep(lo, hi, v);
      d = max(d, sig * .85);
      float gi = floor(clamp(d, 0., .999) * nGlyph);
      vec2 inC = fract(px / cell);
      vec2 guv = vec2((gi + inC.x) / nGlyph, 1. - inC.y);
      float gm = texture2D(tGlyph, guv).r;
      vec3 base = light > .5 ? paper : bg;
      vec3 ink  = light > .5 ? bg : paper;
      ink = mix(ink, signal, sig);
      vec3 asc = mix(base, ink, gm);
      // tone layer keeps the 3D form readable
      vec3 tone = light > .5 ? mix(bg, paper, smoothstep(.0, 1., lf)) : mix(bg, paper, smoothstep(.0, 1., lf));
      tone = mix(tone, signal * (.55 + .6*lf), sigF);
      vec3 sceneOut = mix(asc, tone, mixTone);
      sceneOut = mix(tone, sceneOut, asciiAmt);
      // clean line layer
      vec4 ln = texture2D(tLines, vUv);
      vec3 lnc = lin2srgb(ln.rgb / max(ln.a, 1e-4));
      sceneOut = mix(sceneOut, lnc, clamp(ln.a, 0., 1.));
      // HUD (premultiplied canvas -> straight)
      vec4 h = texture2D(tHud, vUv);
      sceneOut = mix(sceneOut, h.rgb, h.a);
      gl_FragColor = vec4(sceneOut, 1.);
    }`,
});
const compQuad = new THREE.Mesh(quadGeo, compMat);
const compScene = new THREE.Scene(); compScene.add(compQuad);

const crtMat = new THREE.ShaderMaterial({
  uniforms: {
    tIn: { value: rtComp.texture }, res: { value: new THREE.Vector2(W, H) }, time: { value: 0 },
    glitch: { value: 0 }, ca: { value: 1.6 }, light: { value: 0 }, flash: { value: 0 },
  },
  vertexShader: VERT,
  fragmentShader: `
    precision highp float; varying vec2 vUv;
    uniform sampler2D tIn; uniform vec2 res; uniform float time, glitch, ca, light, flash;
    float hash(vec2 p){ p = fract(p*vec2(123.34, 456.21)); p += dot(p, p+45.32); return fract(p.x*p.y); }
    vec3 samp(vec2 uv){ return texture2D(tIn, clamp(uv, vec2(0.), vec2(1.))).rgb; }
    void main(){
      vec2 uv = vUv;
      vec2 cc = uv - .5; float r2 = dot(cc*vec2(1., res.y/res.x*.56), cc*vec2(1., res.y/res.x*.56));
      uv = .5 + cc * (1. + .035 * r2);
      float fr = floor(time * 24.);
      // glitch bands
      float bandH = mix(14., 90., hash(vec2(fr, 3.)));
      float band = floor(uv.y * res.y / bandH);
      float on = step(1. - glitch * .55, hash(vec2(band, fr)));
      uv.x += (hash(vec2(band*1.7, fr)) - .5) * .09 * glitch * on;
      // micro jitter
      uv.x += (hash(vec2(floor(uv.y*res.y/2.), fr)) - .5) * .0007;
      float caPx = ca + glitch * 16. * (.4 + on) + 1.8 * r2 * 4.;
      vec2 o = vec2(caPx / res.x, 0.);
      // analog softness: 3-tap horizontal blur per channel
      vec2 b = vec2(1.1 / res.x, 0.);
      float R = (samp(uv + o - b).r + samp(uv + o).r*2. + samp(uv + o + b).r) * .25;
      float G = (samp(uv - b).g + samp(uv).g*2. + samp(uv + b).g) * .25;
      float B = (samp(uv - o - b).b + samp(uv - o).b*2. + samp(uv - o + b).b) * .25;
      vec3 col = vec3(R, G, B);
      // faint ghost (tape echo)
      col = mix(col, samp(uv - vec2(7./res.x, 0.)), .07);
      // scanlines
      float sl = .5 + .5 * sin(gl_FragCoord.y * 3.14159 * 2. / 3.);
      col *= 1. - .11 * sl;
      // rolling bar
      float roll = smoothstep(.0, .06, abs(fract(uv.y*.7 - time*.09) - .5));
      col *= mix(.965, 1., roll);
      // grain
      float n = hash(gl_FragCoord.xy + fr * 17.13) - .5;
      col += n * (light > .5 ? .075 : .06);
      // vignette
      float vig = smoothstep(1.15, .35, length(cc * vec2(1., .9)));
      col *= mix(.72, 1., vig);
      // flicker
      col *= 1. + .018 * sin(time * 61.) + flash;
      gl_FragColor = vec4(clamp(col, 0., 1.), 1.);
    }`,
});
const crtScene = new THREE.Scene(); crtScene.add(new THREE.Mesh(quadGeo, crtMat));

// occluder material for drawing scene depth into the line layer
const depthOnly = new THREE.MeshBasicMaterial({ colorWrite: false });

// ---------- robots ----------
let gltf = null;
export function makeRobot(opts = {}) {
  const root = SkeletonUtils.clone(gltf.scene);
  const uReveal = { value: 1 };
  const surf = FX.makeDissolvable(new THREE.MeshStandardMaterial({ color: opts.color ?? 0xcfcfcf, roughness: .38, metalness: .25 }), uReveal);
  const joint = FX.makeDissolvable(new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: .5, metalness: .4 }), uReveal);
  const extras = [];
  root.traverse(o => {
    if (o.isMesh) {
      o.frustumCulled = false;
      o.material = /Joints/i.test(o.name) ? joint : surf;
    }
  });
  const sig = new THREE.MeshBasicMaterial({ color: PAL.signal });
  const dot = (bone, r = .028, off = [0, 0, .06]) => {
    const b = root.getObjectByName(bone); if (!b) return;
    root.updateMatrixWorld(true);
    const ws = new THREE.Vector3(); b.getWorldScale(ws); const k = 1 / ws.x; // bones live in a scaled (cm) space
    const m = new THREE.Mesh(new THREE.SphereGeometry(r * k, 12, 8), sig);
    m.position.set(off[0] * k, off[1] * k, off[2] * k);
    b.add(m); extras.push(m);
  };
  if (opts.dots !== false) {
    dot('mixamorigLeftLeg', .022, [0, 0, .05]); dot('mixamorigRightLeg', .022, [0, 0, .05]);
    dot('mixamorigLeftHand', .016, [0, .03, 0]); dot('mixamorigRightHand', .016, [0, .03, 0]);
    dot('mixamorigSpine2', .02, [0, .06, .11]);
  }
  // Optimus-style black face plate on the head
  if (opts.visor !== false) {
    const hb = root.getObjectByName('mixamorigHead');
    if (hb) {
      root.updateMatrixWorld(true);
      const ws = new THREE.Vector3(); hb.getWorldScale(ws); const k = 1 / ws.x;
      const visor = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 20),
        new THREE.MeshStandardMaterial({ color: 0x060606, roughness: .15, metalness: .5 }));
      visor.scale.set(.074 * k, .058 * k, .05 * k);
      visor.position.set(0, .095 * k, .1 * k);
      hb.add(visor); extras.push(visor);
    }
  }
  const mixer = new THREE.AnimationMixer(root);
  const clips = {}; gltf.animations.forEach(c => clips[c.name] = c);
  let action = null;
  const api = {
    root, mixer,
    play(name, timeScale = 1) {
      if (action) action.stop();
      action = mixer.clipAction(clips[name]); action.timeScale = timeScale; action.play();
      return api;
    },
    pose(t) { mixer.setTime(t); root.updateMatrixWorld(true); },
    reveal(v) { uReveal.value = v; root.visible = v > .001; extras.forEach(e => e.visible = v > .7); },
    bonePos(name, out = new THREE.Vector3()) {
      const b = root.getObjectByName(name); root.updateMatrixWorld(true); return b.getWorldPosition(out);
    },
  };
  return api;
}

export function gridFloor(color, { size = 40, step = 1, zNear = 12, zFar = -80, opacity = .5 } = {}) {
  const pts = [];
  for (let x = -size; x <= size; x += step) pts.push(x, 0, zNear, x, 0, zFar);
  for (let z = zNear; z >= zFar; z -= step) pts.push(-size, 0, z, size, 0, z);
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
  return new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color, transparent: true, opacity, fog: true }));
}

export function wireSphere(radius, color, { lat = 10, lon = 16, opacity = .8 } = {}) {
  const pts = []; const seg = 64;
  for (let i = 1; i < lat; i++) {
    const phi = Math.PI * i / lat, y = Math.cos(phi) * radius, r = Math.sin(phi) * radius;
    for (let s = 0; s < seg; s++) {
      const a0 = s / seg * Math.PI * 2, a1 = (s + 1) / seg * Math.PI * 2;
      pts.push(Math.cos(a0) * r, y, Math.sin(a0) * r, Math.cos(a1) * r, y, Math.sin(a1) * r);
    }
  }
  for (let j = 0; j < lon; j++) {
    const a = j / lon * Math.PI * 2;
    for (let s = 0; s < seg; s++) {
      const p0 = Math.PI * s / seg, p1 = Math.PI * (s + 1) / seg;
      pts.push(Math.cos(a) * Math.sin(p0) * radius, Math.cos(p0) * radius, Math.sin(a) * Math.sin(p0) * radius,
               Math.cos(a) * Math.sin(p1) * radius, Math.cos(p1) * radius, Math.sin(a) * Math.sin(p1) * radius);
    }
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
  return new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color, transparent: true, opacity }));
}

// ---------- HUD helpers ----------
export const ease = {
  out: t => 1 - Math.pow(1 - Math.min(Math.max(t, 0), 1), 3),
  inOut: t => { t = Math.min(Math.max(t, 0), 1); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; },
  clamp: t => Math.min(Math.max(t, 0), 1),
};
const C = { paper: '#e8e3db', bg: '#090806', signal: '#ff531f', soft: '#b8b2aa', muted: '#77726b' };
export const HUD = {
  C, W, H,
  project(v, cam) { const p = v.clone().project(cam); return { x: (p.x * .5 + .5) * W, y: (-p.y * .5 + .5) * H, vis: p.z < 1 }; },
  mono(g, text, x, y, { size = 22, color = C.paper, align = 'left', weight = 500, spacing = .16, alpha = 1 } = {}) {
    g.save(); g.globalAlpha = alpha; g.font = `${weight} ${size}px "IBM Plex Mono"`; g.fillStyle = color;
    g.textBaseline = 'alphabetic'; g.letterSpacing = `${spacing * size}px`; g.textAlign = align;
    g.fillText(text.toUpperCase(), x, y); g.restore();
  },
  // multi-line headline. parts: [[{t:'BY ', c:paper}, {t:'2040', c:signal}], ...]
  headline(g, lines, { y, size = 150, reveal = 1, lh = .9, align = 'center', x = W / 2, color = C.paper, smear = 0 } = {}) {
    g.save(); g.font = `800 ${size}px "Barlow Condensed"`; g.textBaseline = 'alphabetic'; g.letterSpacing = `${-0.015 * size}px`;
    lines.forEach((parts, i) => {
      const r = ease.out((reveal - i * .18) / .8);
      if (r <= 0) return;
      const ly = y + i * size * lh;
      const total = parts.reduce((s, p) => s + g.measureText(p.t).width, 0);
      let cx = align === 'center' ? x - total / 2 : align === 'right' ? x - total : x;
      // vertical mask reveal
      g.save(); g.beginPath(); g.rect(0, ly - size * .82, W, size * .95); g.clip();
      const dy = (1 - r) * size * .9;
      for (const p of parts) {
        g.fillStyle = p.c ?? color;
        if (smear > 0) { g.globalAlpha = .25 * smear; g.fillText(p.t, cx - 10 * smear, ly + dy); g.fillText(p.t, cx + 14 * smear, ly + dy); g.globalAlpha = 1; }
        g.fillText(p.t, cx, ly + dy); cx += g.measureText(p.t).width;
      }
      g.restore();
    });
    g.restore();
  },
  trackBox(g, x, y, { s = 70, label = [], color = C.paper, accent = C.signal, alpha = 1, side = 'right', reticle = false } = {}) {
    g.save(); g.globalAlpha = alpha; g.strokeStyle = color; g.lineWidth = 2;
    g.strokeRect(x - s / 2, y - s / 2, s, s);
    g.fillStyle = accent; g.beginPath(); g.arc(x, y, 6, 0, Math.PI * 2); g.fill();
    if (reticle) { g.strokeStyle = accent; g.lineWidth = 3; g.beginPath(); g.arc(x, y, s * .62, 0, Math.PI * 2); g.stroke(); }
    const lx = side === 'right' ? x + s / 2 + 14 : x - s / 2 - 14;
    label.forEach((l, i) => HUD.mono(g, l, lx, y - s / 2 + 18 + i * 26, { size: 19, color, align: side === 'right' ? 'left' : 'right', spacing: .08 }));
    g.restore();
  },
  callout(g, x, y, tx, ty, lines, { color = C.paper, accent = C.signal, alpha = 1 } = {}) {
    g.save(); g.globalAlpha = alpha; g.strokeStyle = accent; g.lineWidth = 3;
    g.beginPath(); g.arc(x, y, 34, 0, Math.PI * 2); g.stroke();
    g.strokeStyle = color; g.lineWidth = 1.5; g.beginPath(); g.moveTo(x + 34 * Math.sign(tx - x), y); g.lineTo(tx, ty); g.stroke();
    lines.forEach((l, i) => HUD.mono(g, l, tx + 8, ty - 6 + i * 26, { size: 19, color, spacing: .08 }));
    g.strokeStyle = accent; g.lineWidth = 2; g.beginPath(); g.moveTo(tx + 8, ty + 4); g.lineTo(tx + 150, ty + 4); g.stroke();
    g.restore();
  },
  tag(g, text, x, y, { size = 22, fill = C.signal, color = C.bg, align = 'center' } = {}) {
    g.save(); g.font = `600 ${size}px "IBM Plex Mono"`; g.letterSpacing = `${.18 * size}px`;
    const w = g.measureText(text).width + size * 1.4, h = size * 1.75;
    const x0 = align === 'center' ? x - w / 2 : x;
    g.fillStyle = fill; g.fillRect(x0, y - h / 2, w, h);
    g.fillStyle = color; g.textBaseline = 'middle'; g.textAlign = 'left'; g.fillText(text, x0 + size * .7, y + 1);
    g.restore();
  },
};

let vMark = null;
async function loadImage(src) { const im = new Image(); im.src = src; await im.decode(); return im; }

// ---------- boot ----------
let shots = [], DURATION = 0;
async function boot() {
  await Promise.all([
    document.fonts.load('800 100px "Barlow Condensed"'), document.fonts.load('700 100px "Barlow Condensed"'),
    document.fonts.load('400 20px "IBM Plex Mono"'), document.fonts.load('500 20px "IBM Plex Mono"'), document.fonts.load('600 20px "IBM Plex Mono"'),
  ]);
  const atlas = buildGlyphAtlas();
  compMat.uniforms.tGlyph.value = atlas.tex; compMat.uniforms.nGlyph.value = atlas.n;
  gltf = await new GLTFLoader().loadAsync('/assets/Xbot.glb');
  vMark = await loadImage('/assets/v_mark_from_video.png');
  const man = await (await fetch('/web/footage/manifest.json')).json();
  const footage = await FX.loadFootage(Object.keys(man));
  const seq = new URLSearchParams(location.search).get('seq') || 'v2demo';
  const { buildShots } = await import(`./seq_${seq}.js`);
  shots = await buildShots({ THREE, PAL, makeRobot, gridFloor, wireSphere, HUD, ease, W, H, FX, footage });
  let t0 = 0; for (const s of shots) { if (s.start === undefined) s.start = t0; else t0 = s.start; t0 += s.dur; }
  DURATION = t0;
  window.EVENTS = shots.flatMap(s => s.events || []);
  window.DURATION = DURATION;
  window.SHOTS = shots.map(s => ({ name: s.name, start: s.start, dur: s.dur }));
}

function chrome(g, t, shot, lt) {
  const light = shot.mode === 'light';
  const fg = light ? C.bg : C.paper, mut = light ? '#5d5852' : C.muted;
  // top labels (below platform status bar)
  // bottom: progress rule + V mark
  if (shot.noChrome) return;
  // timeline 2024 -> 2040 with an unexplained 2027 marker
  const py = 1500, pw = 640, px = (W - pw) / 2;
  const yr = y => px + pw * (y - 2024) / 16;
  g.fillStyle = light ? 'rgba(9,8,6,.25)' : 'rgba(232,227,219,.25)'; g.fillRect(px, py, pw, 2);
  const prog = shot.timeline ? shot.timeline(lt) : t / DURATION;
  g.fillStyle = fg; g.fillRect(px, py, pw * prog, 2);
  for (const [y, lab] of [[2024, '2024'], [2027, '2027'], [2040, '2040']]) {
    const x = yr(y), is27 = y === 2027;
    g.fillStyle = is27 ? C.signal : mut; g.fillRect(x - 1, py - 9, 2, 20);
    HUD.mono(g, lab + (is27 ? ' ?' : ''), x, py + 36, { size: 16, align: 'center', color: is27 ? C.signal : mut, spacing: .12, alpha: is27 ? (.55 + .45 * Math.abs(Math.sin(t * 2.2))) : 1 });
  }
  g.fillStyle = C.signal; g.beginPath(); g.arc(px + pw * prog, py + 1, 5, 0, Math.PI * 2); g.fill();
  if (vMark) {
    const vw = 70, vh = vw * vMark.height / vMark.width;
    g.save(); if (light) g.filter = 'invert(1) brightness(.12)'; g.drawImage(vMark, W / 2 - vw / 2, py + 64, vw, vh); g.restore();
  }
}

function renderAt(t) {
  t = Math.min(Math.max(t, 0), DURATION - 1e-4);
  const shot = shots.find(s => t >= s.start && t < s.start + s.dur) || shots[shots.length - 1];
  const lt = t - shot.start;
  shot.update(lt, t);
  const light = shot.mode === 'light';
  const bgc = light ? PAL.paper : PAL.bg;
  // 1. scene -> rtScene
  renderer.setRenderTarget(rtScene); renderer.setClearColor(bgc, 1); renderer.clear();
  renderer.render(shot.scene, shot.camera);
  // 2. lines: occluders depth-only, then lines
  renderer.setRenderTarget(rtLines); renderer.setClearColor(0x000000, 0); renderer.clear();
  shot.scene.overrideMaterial = depthOnly;
  const bgSave = shot.scene.background; shot.scene.background = null;
  renderer.render(shot.scene, shot.camera);
  shot.scene.overrideMaterial = null; shot.scene.background = bgSave;
  renderer.render(shot.lines, shot.camera);
  // 3. HUD
  hud.clearRect(0, 0, W, H);
  shot.hud(hud, lt, t);
  chrome(hud, t, shot, lt);
  hudTex.needsUpdate = true;
  // 4. composite
  compMat.uniforms.light.value = light ? 1 : 0;
  compMat.uniforms.mixTone.value = shot.mixTone ?? .38;
  renderer.setRenderTarget(rtComp); renderer.clear(); renderer.render(compScene, quadCam);
  // 5. CRT
  const cg = shot.cutGlitch === false ? 0 : 1;
  const cut = cg * Math.max(0, 1 - lt / .28), cutOut = cg * Math.max(0, 1 - (shot.dur - lt) / .12);
  crtMat.uniforms.glitch.value = Math.min(1, Math.max(cut, cutOut * .7, shot.glitch ? shot.glitch(lt) : 0));
  crtMat.uniforms.flash.value = cut * .12;
  crtMat.uniforms.time.value = t; crtMat.uniforms.light.value = light ? 1 : 0;
  renderer.setRenderTarget(null); renderer.clear(); renderer.render(crtScene, quadCam);
  return shot.name;
}

window.renderAt = renderAt;
window.__ready = boot().then(() => { renderAt(0); return true; }).catch(e => { console.error(e); window.__error = String(e.stack || e); throw e; });
