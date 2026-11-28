// Particle swarms (assemble / disperse), footage screens, voxel dissolve for meshes.
import * as THREE from 'three';

const srgbToLin = c => Math.pow(c, 2.2);

// ---------- deterministic rng ----------
export function rng(seed = 1) { let s = seed >>> 0 || 1; return () => (s = (s * 16807) % 2147483647) / 2147483647; }
const smooth = t => { t = Math.min(Math.max(t, 0), 1); return t * t * (3 - 2 * t); };
const easeInOut = t => { t = Math.min(Math.max(t, 0), 1); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };

// ---------- voxel dissolve on standard materials ----------
export function makeDissolvable(mat, uni) {
  mat.onBeforeCompile = sh => {
    sh.uniforms.uReveal = uni;
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWP;')
      .replace('#include <fog_vertex>', '#include <fog_vertex>\nvWP = (modelMatrix * vec4(transformed, 1.)).xyz;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform float uReveal; varying vec3 vWP;\nfloat dh31(vec3 p){ return fract(sin(dot(p, vec3(12.9898,78.233,37.719))) * 43758.5453); }')
      .replace('void main() {', 'void main() {\n  if (dh31(floor(vWP * 26.)) > uReveal) discard;');
  };
  mat.customProgramCacheKey = () => 'dissolve';
  return mat;
}

// ---------- particle swarm ----------
const swarmVert = `
  attribute float aAlpha; attribute vec3 aColor; uniform float uSize; varying vec3 vC; varying float vA;
  void main(){ vC = aColor; vA = aAlpha; vec4 mv = modelViewMatrix * vec4(position, 1.);
    gl_PointSize = uSize; gl_Position = projectionMatrix * mv; }`;
const swarmFrag = `
  varying vec3 vC; varying float vA;
  void main(){ vec2 d = gl_PointCoord - .5; if (dot(d,d) > .25) discard; gl_FragColor = vec4(vC, vA); }`;

export class Swarm {
  // n particles; color: THREE.Color (linear) used when no per-point colors are given
  constructor(n, { color = new THREE.Color(1, 1, 1), size = 2.6, seed = 7 } = {}) {
    this.n = n; this.base = color;
    const r = rng(seed);
    this.pos = new Float32Array(n * 3); this.col = new Float32Array(n * 3); this.alpha = new Float32Array(n);
    this.origin = new Float32Array(n * 3); this.dir = new Float32Array(n * 3);
    this.delay = new Float32Array(n); this.phase = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      this.delay[i] = r() * .45; this.phase[i] = r() * 6.283;
      const u = r() * 2 - 1, a = r() * 6.283, s = Math.sqrt(1 - u * u);
      this.dir[i * 3] = Math.cos(a) * s; this.dir[i * 3 + 1] = u * .6 + .25; this.dir[i * 3 + 2] = Math.sin(a) * s;
      this.col[i * 3] = color.r; this.col[i * 3 + 1] = color.g; this.col[i * 3 + 2] = color.b;
    }
    this.rand = r;
    const g = new THREE.BufferGeometry();
    this.aPos = new THREE.BufferAttribute(this.pos, 3); this.aCol = new THREE.BufferAttribute(this.col, 3); this.aAl = new THREE.BufferAttribute(this.alpha, 1);
    g.setAttribute('position', this.aPos); g.setAttribute('aColor', this.aCol); g.setAttribute('aAlpha', this.aAl);
    this.mat = new THREE.ShaderMaterial({ uniforms: { uSize: { value: size } }, vertexShader: swarmVert, fragmentShader: swarmFrag,
      transparent: true, depthTest: false, depthWrite: false });
    this.points = new THREE.Points(g, this.mat); this.points.frustumCulled = false;
  }
  // scatter origins in a shell around center
  scatter(center, rMin = 2.5, rMax = 6, ySquash = .7) {
    const r = this.rand;
    for (let i = 0; i < this.n; i++) {
      const u = r() * 2 - 1, a = r() * 6.283, s = Math.sqrt(1 - u * u), d = rMin + (rMax - rMin) * Math.pow(r(), .7);
      this.origin[i * 3] = center.x + Math.cos(a) * s * d;
      this.origin[i * 3 + 1] = Math.max(.02, center.y + u * d * ySquash);
      this.origin[i * 3 + 2] = center.z + Math.sin(a) * s * d;
    }
    return this;
  }
  // use another position buffer (e.g. a previous form) as origins
  originsFrom(buf) { for (let i = 0; i < this.n * 3; i++) this.origin[i] = buf[i % buf.length]; return this; }
  // per-point colours, optionally lifted toward the swarm base colour so they read against the background
  setColors(buf, lift = 0) {
    const b = this.base, n = Math.min(this.n * 3, buf.length);
    for (let i = 0; i < n; i += 3) {
      this.col[i] = buf[i] + (b.r - buf[i]) * lift; this.col[i + 1] = buf[i + 1] + (b.g - buf[i + 1]) * lift; this.col[i + 2] = buf[i + 2] + (b.b - buf[i + 2]) * lift;
    }
    this.aCol.needsUpdate = true;
  }
  // a = assemble progress 0..1, d = disperse progress 0..1, t = time for swirl
  update(targets, a, d, t, { swirl = .22, spread = 3.2, fade = 1 } = {}) {
    const n = this.n, P = this.pos, O = this.origin, T = targets, D = this.dir;
    for (let i = 0; i < n; i++) {
      const k = i * 3, ph = this.phase[i];
      const e = easeInOut((a - this.delay[i]) / .55);
      const q = Math.pow(smooth((d - this.delay[i] * .7) / .6), 1.5);
      const w = (1 - e) * swirl + q * swirl * .6;
      const sx = Math.sin(t * 1.3 + ph) * w, sy = Math.cos(t * 1.1 + ph * 1.7) * w, sz = Math.sin(t * .9 + ph * 2.3) * w;
      const tx = T[k % T.length], ty = T[(k + 1) % T.length], tz = T[(k + 2) % T.length];
      P[k] = O[k] + (tx - O[k]) * e + D[k] * q * spread + sx;
      P[k + 1] = O[k + 1] + (ty - O[k + 1]) * e + D[k + 1] * q * spread + sy;
      P[k + 2] = O[k + 2] + (tz - O[k + 2]) * e + D[k + 2] * q * spread + sz;
      const appear = smooth((a - this.delay[i] * .5) / .25);
      this.alpha[i] = appear * (1 - smooth((d - .35 - this.delay[i] * .5) / .45)) * fade;
    }
    this.aPos.needsUpdate = true; this.aAl.needsUpdate = true;
  }
}

// sample world-space vertex positions of a robot (skinned) into buf
export class RobotSampler {
  constructor(robot, n, seed = 3) {
    this.meshes = []; robot.root.traverse(o => { if (o.isSkinnedMesh) this.meshes.push(o); });
    const r = rng(seed); this.idx = [];
    const counts = this.meshes.map(m => m.geometry.attributes.position.count), total = counts.reduce((a, b) => a + b, 0);
    for (let i = 0; i < n; i++) {
      let v = Math.floor(r() * total), m = 0; while (v >= counts[m]) { v -= counts[m]; m++; }
      this.idx.push([m, v]);
    }
    this.buf = new Float32Array(n * 3); this.v = new THREE.Vector3();
  }
  sample() {
    const v = this.v;
    for (let i = 0; i < this.idx.length; i++) {
      const [m, k] = this.idx[i], mesh = this.meshes[m];
      mesh.getVertexPosition(k, v); v.applyMatrix4(mesh.matrixWorld);
      this.buf[i * 3] = v.x; this.buf[i * 3 + 1] = v.y; this.buf[i * 3 + 2] = v.z;
    }
    return this.buf;
  }
}

// ---------- footage ----------
export async function loadFootage(names) {
  const man = await (await fetch('/web/footage/manifest.json')).json();
  const clips = {};
  for (const name of names) {
    const m = man[name]; if (!m) throw new Error('no clip ' + name);
    const frames = await Promise.all(Array.from({ length: m.frames }, async (_, i) => {
      const blob = await (await fetch(`/web/footage/${name}/${String(i + 1).padStart(4, '0')}.jpg`)).blob();
      return createImageBitmap(blob, { imageOrientation: 'flipY' });
    }));
    clips[name] = { ...m, name, images: frames };
  }
  return clips;
}

const screenVert = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }`;
const screenFrag = `
  precision highp float; varying vec2 vUv;
  uniform sampler2D map; uniform float uReveal, uContrast, uBright, uTime; uniform vec3 uDark, uPaper;
  float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
  float bayer4(vec2 p){ p = mod(floor(p), 4.);
    float i = p.x + p.y * 4.;
    float m[16]; m[0]=0.;m[1]=8.;m[2]=2.;m[3]=10.;m[4]=12.;m[5]=4.;m[6]=14.;m[7]=6.;m[8]=3.;m[9]=11.;m[10]=1.;m[11]=9.;m[12]=15.;m[13]=7.;m[14]=13.;m[15]=5.;
    for (int k = 0; k < 16; k++) if (float(k) == i) return m[k] / 16.; return 0.; }
  void main(){
    vec2 cell = floor(vUv * vec2(36., 52.));
    if (h(cell) > uReveal) discard;
    // tape wobble
    vec2 uv = vUv; uv.x += (h(vec2(floor(uv.y * 90.), floor(uTime * 15.))) - .5) * .004;
    vec3 c = texture2D(map, uv).rgb;
    float l = dot(c, vec3(.299, .587, .114));
    l = clamp((l - .5) * uContrast + .5 + uBright, 0., 1.);
    // 6-level ordered dither at 2px
    float lv = 6.; float dl = floor(l * lv + bayer4(gl_FragCoord.xy / 2.)) / lv;
    l = mix(l, dl, .55);
    l *= .9 + .1 * sin(gl_FragCoord.y * 3.14159 / 1.5);
    l += (h(gl_FragCoord.xy + uTime * 31.) - .5) * .08;
    vec3 col = mix(uDark, uPaper, clamp(l, 0., 1.));
    gl_FragColor = vec4(pow(col, vec3(2.2)), 1.);
  }`;

export class Screen {
  // clip from loadFootage; height in world units; mode 'light' | 'dark' controls frame colour
  constructor(clip, { height = 1.6, mode = 'light', contrast = 1.25, bright = 0 } = {}) {
    this.clip = clip; this.h = height; this.w = height * clip.aspect;
    this.tex = new THREE.Texture(clip.images[0]); this.tex.flipY = false; this.tex.colorSpace = THREE.NoColorSpace; this.tex.needsUpdate = true;
    this.uni = {
      map: { value: this.tex }, uReveal: { value: 0 }, uContrast: { value: contrast }, uBright: { value: bright }, uTime: { value: 0 },
      uDark: { value: new THREE.Vector3(.035, .031, .024) }, uPaper: { value: new THREE.Vector3(.91, .89, .86) },
    };
    this.group = new THREE.Group();
    this.mesh = new THREE.Mesh(new THREE.PlaneGeometry(this.w, this.h),
      new THREE.ShaderMaterial({ uniforms: this.uni, vertexShader: screenVert, fragmentShader: screenFrag }));
    this.group.add(this.mesh);
    // thin border + signal corner brackets
    const lc = mode === 'light' ? new THREE.Color(0x090806) : new THREE.Color(0xe8e3db);
    const bw = this.w / 2 + .03, bh = this.h / 2 + .03;
    const border = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(bw * 2, bh * 2)),
      new THREE.LineBasicMaterial({ color: lc, transparent: true, opacity: .55 }));
    const L = Math.min(this.w, this.h) * .12, o = .08, br = [];
    for (const [sx, sy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
      const x = sx * (bw + o), y = sy * (bh + o);
      br.push(x, y, 0, x - sx * L, y, 0, x, y, 0, x, y - sy * L, 0);
    }
    const bg = new THREE.BufferGeometry(); bg.setAttribute('position', new THREE.Float32BufferAttribute(br, 3));
    const brackets = new THREE.LineSegments(bg, new THREE.LineBasicMaterial({ color: new THREE.Color('#ff531f'), transparent: true }));
    this.border = border; this.brackets = brackets;
    this.group.add(border, brackets);
    // particle targets: grid over the plane
    this.nx = Math.round(Math.sqrt(8200 * clip.aspect)); this.ny = Math.round(this.nx / clip.aspect);
    this.targets = new Float32Array(this.nx * this.ny * 3); this.colors = new Float32Array(this.nx * this.ny * 3);
    this.cv = document.createElement('canvas'); this.cv.width = this.nx; this.cv.height = this.ny;
    this.cg = this.cv.getContext('2d', { willReadFrequently: true });
    this.v = new THREE.Vector3();
  }
  get count() { return this.nx * this.ny; }
  frameAt(t) { const c = this.clip; return Math.min(c.images.length - 1, Math.max(0, Math.floor(t * c.fps))); }
  setTime(t, time = 0) {
    const f = this.frameAt(t);
    if (this.tex.image !== this.clip.images[f]) { this.tex.image = this.clip.images[f]; this.tex.needsUpdate = true; }
    this.uni.uTime.value = time; this._f = f;
  }
  reveal(v) {
    this.uni.uReveal.value = v; this.mesh.visible = v > 0;
    this.border.material.opacity = .55 * smooth(v * 1.5); this.brackets.material.opacity = smooth(v * 1.5);
    this.border.visible = this.brackets.visible = v > 0;
  }
  // world-space grid points + per-point colour (linear) from current frame
  sampleTargets() {
    this.group.updateMatrixWorld(true);
    const img = this.clip.images[this._f ?? 0];
    this.cg.save(); this.cg.scale(1, -1); this.cg.drawImage(img, 0, -this.ny, this.nx, this.ny); this.cg.restore(); // undo flipY
    const d = this.cg.getImageData(0, 0, this.nx, this.ny).data;
    const c = this.uni.uContrast.value, b = this.uni.uBright.value, dk = this.uni.uDark.value, pp = this.uni.uPaper.value;
    let i = 0;
    for (let y = 0; y < this.ny; y++) for (let x = 0; x < this.nx; x++, i++) {
      this.v.set((x / (this.nx - 1) - .5) * this.w, (.5 - y / (this.ny - 1)) * this.h, 0).applyMatrix4(this.mesh.matrixWorld);
      this.targets[i * 3] = this.v.x; this.targets[i * 3 + 1] = this.v.y; this.targets[i * 3 + 2] = this.v.z;
      const p = (y * this.nx + x) * 4;
      let l = (d[p] * .299 + d[p + 1] * .587 + d[p + 2] * .114) / 255; l = Math.min(1, Math.max(0, (l - .5) * c + .5 + b));
      this.colors[i * 3] = srgbToLin(dk.x + (pp.x - dk.x) * l); this.colors[i * 3 + 1] = srgbToLin(dk.y + (pp.y - dk.y) * l); this.colors[i * 3 + 2] = srgbToLin(dk.z + (pp.z - dk.z) * l);
    }
    return this.targets;
  }
  // corner in world space (for HUD labels): sx, sy in -1..1
  corner(sx, sy, out = new THREE.Vector3()) {
    this.group.updateMatrixWorld(true);
    return out.set(sx * (this.w / 2 + .03), sy * (this.h / 2 + .03), 0).applyMatrix4(this.mesh.matrixWorld);
  }
}
