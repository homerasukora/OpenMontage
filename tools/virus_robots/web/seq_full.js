// VIRUS2027 · "10 billion robots" — full sequence, timed to web/data/timing.json (VO + Musk clips).
export async function buildShots(K) {
  const { THREE, PAL, makeRobot, gridFloor, wireSphere, HUD, ease, FX, footage } = K;
  const { C } = HUD;
  const W = K.W;
  const v3 = (x, y, z) => new THREE.Vector3(x, y, z);
  const ASPECT = K.W / K.H;
  const sm = x => { x = Math.min(Math.max(x, 0), 1); return x * x * (3 - 2 * x); };
  const seg = (t, a, b) => sm((t - a) / (b - a));
  const lerp = (a, b, k) => a + (b - a) * k;
  const pulse = (t, at, len = .25) => (t >= at && t < at + len) ? 1 - (t - at) / len : 0;
  const INK_DARK = new THREE.Color(0x090806), INK_LIGHT = new THREE.Color(0xe8e3db), SIG = new THREE.Color(0xff531f);
  const MUT_LIGHT = '#5d5852';

  // ---------- timing ----------
  const TM = await (await fetch('/web/data/timing.json')).json();
  const WORDS = await (await fetch('/web/data/vo_words.json')).json();
  const SEG = Object.fromEntries(TM.segments.map(s => [s.key, s]));
  const norm = w => w.toLowerCase().replace(/[^a-z0-9]/g, '');
  const wt = (word, after = 0) => { const n = norm(word); const x = WORDS.find(w => norm(w.w).startsWith(n) && w.s >= after - .3); if (!x) console.log('word not found', word); return x ? x.s : after; };
  const B = k => { const i = TM.segments.findIndex(s => s.key === k); const p = TM.segments[i - 1]; return p ? (p.e + TM.segments[i].s) / 2 : 0; };
  const muskAt = (key, srcT) => SEG[key].s + (srcT - SEG[key].src[0]);
  const DUR = TM.dur;

  // ---------- helpers ----------
  function lights(scene, { key = 3.2, rim = 2.4, amb = .25, keyPos = [2.5, 3, 2.5], rimPos = [-3, 2.5, -3] } = {}) {
    scene.add(new THREE.HemisphereLight(0xffffff, 0x202020, amb));
    const k = new THREE.DirectionalLight(0xffffff, key); k.position.set(...keyPos); scene.add(k);
    const r = new THREE.DirectionalLight(0xffffff, rim); r.position.set(...rimPos); scene.add(r);
  }
  const cam = (fov = 34) => new THREE.PerspectiveCamera(fov, ASPECT, .05, 300);
  const once = fn => { const v = fn(); return () => v; }; // evaluated eagerly so every frame is independent
  const orbitPos = (c, r, a, h) => v3(c.x + Math.sin(a) * r, h, c.z + Math.cos(a) * r);
  function setCam(camera, pos, look) { camera.position.copy(pos); camera.lookAt(look); camera.updateMatrixWorld(); }
  function headTurn(bot, yaw, pitch = 0) {
    const hb = bot.root.getObjectByName('mixamorigHead'); if (!hb) return;
    hb.rotation.y += yaw; hb.rotation.x += pitch; bot.root.updateMatrixWorld(true);
  }
  const mat = (color = 0xbdbdbd, rough = .55) => {
    const u = { value: 1 };
    const m = FX.makeDissolvable(new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: .15 }), u);
    m.reveal = v => { u.value = v; }; return m;
  };
  const box = (w, h, d, m) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
  function redacted(g, pre, word, { y, size = 120, p = 1, ink = C.paper, bar = C.paper, accent = C.signal, alpha = 1 } = {}) {
    if (p <= 0 || alpha <= 0) return;
    g.save(); g.globalAlpha = alpha; g.font = `800 ${size}px "Barlow Condensed"`; g.letterSpacing = `${-.015 * size}px`;
    let w1 = g.measureText(pre).width, w2 = g.measureText(word).width;
    if (w1 + w2 > W - 130) { size *= (W - 130) / (w1 + w2); g.font = `800 ${size}px "Barlow Condensed"`; g.letterSpacing = `${-.015 * size}px`; w1 = g.measureText(pre).width; w2 = g.measureText(word).width; }
    const x0 = W / 2 - (w1 + w2) / 2;
    g.fillStyle = ink; g.fillText(pre, x0, y);
    g.fillStyle = accent; g.fillText(word, x0 + w1, y);
    const cover = 1 - ease.out(p * 1.4);
    if (cover > 0) { g.fillStyle = bar; g.fillRect(x0 + w1 + w2 * (1 - cover) - 4, y - size * .78, w2 * cover + 10, size * .86); }
    g.restore();
  }
  function counter(g, val, { y, size = 168, color = C.paper, lead = 0, reveal = 1, leadLen = 0 } = {}) {
    const s = Math.round(val).toLocaleString('en-US');
    const parts = lead && s.length >= leadLen ? [{ t: s.slice(0, lead), c: C.signal }, { t: s.slice(lead) }] : [{ t: s }];
    HUD.headline(g, [parts], { y, size, reveal, color });
  }
  const label = (g, text, p, { color = C.soft, align = 'left', dy = 36, alpha = 1, size = 18 } = {}) =>
    HUD.mono(g, text, p.x, p.y + dy, { size, color, align, alpha });

  const shots = [];
  const addShot = s => { s.dur = s.end - s.start; shots.push(s); return s; };

  // ---------- crowd helpers: bake a posed robot into static geometry for instancing ----------
  const BGU = await import('three/addons/utils/BufferGeometryUtils.js');
  function bakeRobot(anim = 'idle', at = 1.3) {
    const b = makeRobot({ dots: false, visor: false }).play(anim); b.pose(at); b.root.updateMatrixWorld(true);
    const out = {}; const v = new THREE.Vector3();
    b.root.traverse(o => {
      if (!o.isSkinnedMesh) return;
      const src = o.geometry, n = src.attributes.position.count, pos = new Float32Array(n * 3);
      for (let i = 0; i < n; i++) { o.getVertexPosition(i, v); v.applyMatrix4(o.matrixWorld); pos[i * 3] = v.x; pos[i * 3 + 1] = v.y; pos[i * 3 + 2] = v.z; }
      const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); if (src.index) g.setIndex(src.index.clone());
      g.computeVertexNormals(); out[/Joints/i.test(o.name) ? 'joint' : 'surf'] = g;
    });
    return out;
  }
  function proxyFigure() {
    const parts = [];
    const add = (geo, x, y, z, rx = 0) => { geo.rotateX(rx); geo.translate(x, y, z); parts.push(geo.toNonIndexed()); };
    add(new THREE.SphereGeometry(.12, 8, 6), 0, 1.5, 0);
    add(new THREE.CapsuleGeometry(.17, .38, 3, 8), 0, 1.12, 0);
    add(new THREE.CapsuleGeometry(.065, .62, 2, 6), -.11, .45, 0); add(new THREE.CapsuleGeometry(.065, .62, 2, 6), .11, .45, 0);
    add(new THREE.CapsuleGeometry(.05, .5, 2, 6), -.27, 1.0, 0); add(new THREE.CapsuleGeometry(.05, .5, 2, 6), .27, 1.0, 0);
    parts.forEach(p => { p.deleteAttribute('uv'); });
    const g = BGU.mergeGeometries(parts); g.computeVertexNormals(); return g;
  }
  function crowd(scene, { cols = [-22, 22], rows = [-32, 8], sx = 1.25, sz = 1.45, near = (x, z) => Math.abs(x) < 7 && z > -9 && z < 5, skip = (x, z) => Math.abs(x) < .6 && Math.abs(z) < .6, seed = 3, color = 0xcfcfcf } = {}) {
    const baked = bakeRobot('idle', 1.3), r = FX.rng(seed);
    const surf = new THREE.MeshStandardMaterial({ color, roughness: .38, metalness: .25 }), joint = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: .5, metalness: .4 });
    const nearM = [], farM = [], m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), sc = new THREE.Vector3(1, 1, 1);
    for (let ix = cols[0]; ix <= cols[1]; ix++) for (let iz = rows[0]; iz <= rows[1]; iz++) {
      const x = ix * sx + (iz % 2) * sx * .5 + (r() - .5) * .25, z = iz * sz + (r() - .5) * .25;
      if (skip(x, z)) continue;
      q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), (r() - .5) * .3);
      m4.compose(new THREE.Vector3(x, 0, z), q, sc);
      (near(x, z) ? nearM : farM).push(m4.clone());
    }
    const inst = (geo, m, list) => { const im = new THREE.InstancedMesh(geo, m, list.length); list.forEach((mm, i) => im.setMatrixAt(i, mm)); im.frustumCulled = false; scene.add(im); return im; };
    inst(baked.surf, surf, nearM); inst(baked.joint, joint, nearM); inst(proxyFigure(), surf, farM);
    return { near: nearM.length, far: farM.length };
  }

  // ======================= ACT 1a · DARK · hook: one robot -> camera pulls back to an endless crowd =======================
  {
    const start = 0, end = B('L2');
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(32);
    lights(scene, { key: 3.4, rim: 3.0, amb: .18, keyPos: [3, 5, 4], rimPos: [-3, 3, -4] });
    scene.fog = new THREE.Fog(PAL.bg, 18, 75);
    const bot = makeRobot().play('idle'); scene.add(bot.root);
    const samp = new FX.RobotSampler(bot, 9000, 3);
    const swA = new FX.Swarm(9000, { color: INK_LIGHT, size: 2.6, seed: 4 }).scatter(v3(0, 1.3, 0), 1.6, 4);
    lines.add(swA.points);
    const info = crowd(scene, { rows: [-30, -1], cols: [-20, 20], near: (x, z) => Math.abs(x) < 6 && z > -9 }); console.log('crowd', JSON.stringify(info));
    lines.fog = new THREE.Fog(PAL.bg, 6, 60);
    lines.add(gridFloor(PAL.paper, { step: 1.45, opacity: .25, size: 60, zFar: -90 }));
    const head = v3();
    const T0 = .9, T1 = end - .15;   // pull-back window
    const K = t => ease.inOut(Math.min(Math.max((t - T0) / (T1 - T0), 0), 1));
    addShot({
      name: 'a1_hook', mode: 'dark', start, end, scene, lines, camera, mixTone: .42,
      events: [{ t: .02, type: 'assemble', short: 1 }, { t: T0, type: 'riser', d: T1 - T0 }, { t: T0, type: 'counter', d: T1 - T0 }],
      update(lt, t) {
        bot.pose(t + 2);
        headTurn(bot, -.7 * (1 - seg(t, .5, 1.1)));
        bot.reveal(seg(t, .3, .75));
        if (t < 1.4) { swA.points.visible = true; swA.update(samp.sample(), seg(t, 0, .7), 0, t, { fade: 1 - seg(t, .75, 1.2) }); } else swA.points.visible = false;
        const k = K(t);
        scene.fog.near = lerp(1.6, 18, seg(k, .05, .55)); scene.fog.far = lerp(2.6, 75, seg(k, 0, .55));
        const d = 1.35 * Math.pow(40 / 1.35, k);                 // distance grows exponentially -> constant-feeling zoom
        const el = lerp(.05, .74, seg(k, .12, .8)), az = lerp(.18, 0, k);
        const look = v3(0, lerp(1.45, 0, seg(k, .05, .8)), lerp(0, -16, seg(k, .1, 1)));
        setCam(camera, v3(look.x + Math.sin(az) * Math.cos(el) * d, look.y + Math.sin(el) * d, look.z + Math.cos(az) * Math.cos(el) * d), look);
        bot.bonePos('mixamorigHead', head); head.y += .1;
      },
      hud(g, lt, t) {
        const k = K(t);
        const val = t < T0 ? 1 : Math.round(Math.pow(10, 10 * k));
        const sz = lerp(130, 175, k);
        counter(g, val, { y: 400, size: sz, lead: 2, leadLen: 14, reveal: (t - .25) * 2.6 });
        HUD.headline(g, [[{ t: val === 1 ? 'HUMANOID ROBOT' : 'HUMANOID ROBOTS' }]], { y: 400 + sz * .72, size: lerp(64, 100, k), reveal: (t - .45) * 2.6, color: C.soft });
        const p = HUD.project(head, camera);
        if (t > .7 && t < T0 + .9) HUD.trackBox(g, p.x, p.y, { s: lerp(110, 30, seg(t, T0, T0 + .9)), label: ['UNIT 0001'], alpha: Math.min(1, (t - .7) * 4) * (1 - seg(t, T0 + .6, T0 + .9)) });
      },
    });
  }

  // ======================= ACT 1b · DARK · globe: more robots than people =======================
  {
    const start = B('L2'), end = B('L3');
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(32);
    const GC = v3(0, 1.45, 0), GR = 1.0;
    const globe = wireSphere(GR, PAL.paper, { lat: 12, lon: 20, opacity: .45 });
    const r = FX.rng(12), sph = n => { const a = new Float32Array(n * 3); for (let i = 0; i < n; i++) { const u = r() * 2 - 1, th = r() * 6.283, s = Math.sqrt(1 - u * u); a[i * 3] = Math.cos(th) * s; a[i * 3 + 1] = u; a[i * 3 + 2] = Math.sin(th) * s; } return a; };
    const NH = 1700, NR = 2300;
    const hu = sph(NH), ro = sph(NR);
    const mkPts = (arr, rad, color, size) => {
      const g = new THREE.BufferGeometry(); const p = arr.map(x => x * rad); g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
      return new THREE.Points(g, new THREE.PointsMaterial({ color, size, sizeAttenuation: false, transparent: true, depthWrite: false }));
    };
    const humans = mkPts(hu, GR * 1.004, PAL.paper, 3.0), robots = mkPts(ro, GR * 1.012, PAL.signal, 3.4);
    const gGroup = new THREE.Group(); gGroup.position.copy(GC); gGroup.add(humans, robots, globe);
    lines.add(gGroup);
    const gTargetsLocal = new Float32Array((NH + NR) * 3); gTargetsLocal.set(hu.map(x => x * GR), 0); gTargetsLocal.set(ro.map(x => x * GR), NH * 3);
    const gCols = new Float32Array((NH + NR) * 3);
    for (let i = 0; i < NH + NR; i++) { const c = i < NH ? INK_LIGHT : SIG; gCols[i * 3] = c.r; gCols[i * 3 + 1] = c.g; gCols[i * 3 + 2] = c.b; }
    const swG = new FX.Swarm(NH + NR, { color: INK_LIGHT, size: 2.6, seed: 8 }).scatter(GC, 2.5, 7); swG.setColors(gCols); lines.add(swG.points);
    const gWorld = new Float32Array(gTargetsLocal.length), tmp = v3();
    lines.fog = new THREE.Fog(PAL.bg, 3, 16);
    lines.add(gridFloor(PAL.paper, { step: .6, opacity: .32 }));
    addShot({
      name: 'a1_globe', mode: 'dark', start, end, scene, lines, camera, mixTone: .42,
      events: [{ t: start, type: 'cut' }, { t: start + .02, type: 'assemble' }],
      update(lt, t) {
        gGroup.rotation.y = t * .3; gGroup.updateMatrixWorld(true);
        const gp = seg(lt, .7, 1.2);
        globe.material.opacity = .45 * seg(lt, .4, 1.0);
        humans.visible = robots.visible = gp > 0; humans.material.opacity = gp;
        robots.geometry.setDrawRange(0, Math.floor(NR * seg(lt, .9, end - start - .2)));
        if (lt < 1.6) {
          swG.points.visible = true;
          for (let i = 0; i < gTargetsLocal.length; i += 3) { tmp.set(gTargetsLocal[i], gTargetsLocal[i + 1], gTargetsLocal[i + 2]).applyMatrix4(gGroup.matrixWorld); gWorld[i] = tmp.x; gWorld[i + 1] = tmp.y; gWorld[i + 2] = tmp.z; }
          swG.update(gWorld, seg(lt, 0, .95), 0, t, { swirl: .3, fade: 1 - seg(lt, 1.0, 1.5) });
        } else swG.points.visible = false;
        const a = lerp(.35, -.35, ease.inOut(lt / (end - start)));
        setCam(camera, orbitPos(v3(0, 0, 0), lerp(7.4, 6.4, ease.inOut(lt / (end - start))), a, 2.1), v3(0, 1.62, 0));
      },
      hud(g, lt, t) {
        HUD.headline(g, [[{ t: 'MORE ROBOTS' }], [{ t: 'THAN PEOPLE' }, { t: '?', c: C.signal }]], { y: 360, size: 150, reveal: (lt - .05) * 2 });
        const la = seg(lt, 1.1, 1.4);
        const pl = { x: W / 2 - 220, y: 560 }, pr = { x: W / 2 + 220, y: 560 };
        HUD.mono(g, 'HUMANS', pl.x, pl.y, { size: 24, weight: 600, alpha: la, align: 'center' });
        HUD.mono(g, '≈ 8.2B · UN', pl.x, pl.y + 30, { size: 17, color: C.muted, alpha: la, align: 'center' });
        HUD.mono(g, 'ROBOTS', pr.x, pr.y, { size: 24, weight: 600, alpha: la, align: 'center', color: C.signal });
        HUD.mono(g, '10B+ · FORECAST', pr.x, pr.y + 30, { size: 17, color: C.muted, alpha: la, align: 'center' });
      },
    });
  }

  // ======================= ACT 2 · LIGHT · army -> Musk screen =======================
  {
    const start = B('L3'), end = B('L5'), T4 = B('L4'), tM = SEG.MB.s;
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(34);
    lights(scene, { key: 3.0, rim: 1.6, amb: .55, keyPos: [3, 4, 4], rimPos: [-3, 3, -4] });
    const army = new THREE.Group(); scene.add(army);
    const bots = []; const cols = 5, rows = 7;
    for (let rr = 0; rr < rows; rr++) for (let c = 0; c < cols; c++) {
      const b = makeRobot({ dots: rr < 3 }).play('walk');
      b.root.position.set((c - 2) * 1.25 + (rr % 2) * .3, 0, -rr * 1.7); b.row = rr; b.phase = (rr * .37 + c * .61) % 1.2;
      army.add(b.root); bots.push(b);
    }
    const hero = bots[2];
    const hsamp = new FX.RobotSampler(hero, 9000, 21);
    const SC = v3(0, 1.55, -1.2);
    const screen = new FX.Screen(footage.musk_full, { height: .74, mode: 'light', contrast: 1.15, bright: .04 });
    screen.group.position.copy(SC); lines.add(screen.group);
    const sw = new FX.Swarm(screen.count, { color: INK_DARK, size: 2.7, seed: 31 }); lines.add(sw.points);
    const heroAtT4 = once(() => { hero.pose(T4 - start + hero.phase); army.position.z = -4 + (T4 - start) * .45; army.updateMatrixWorld(true); return hsamp.sample().slice(); });
    lines.fog = new THREE.Fog(PAL.paper, 6, 34);
    lines.add(gridFloor(PAL.bg, { step: 1.2, opacity: .42 }));
    const headP = v3();
    const tLeast = wt('least', SEG.L3.s), t2040 = wt('2040', SEG.L3.s);
    addShot({
      name: 'a2_army_musk', mode: 'light', start, end, scene, lines, camera, mixTone: .32,
      timeline: lt => seg(lt + start, start, t2040 + .5) * 1,
      events: [{ t: start, type: 'cut' }, { t: start + .1, type: 'build' }, { t: t2040 - .1, type: 'hit' }, { t: T4 - .2, type: 'disperse' }, { t: T4, type: 'assemble' }],
      update(lt, t) {
        const al = t - start;
        army.position.z = -4 + Math.min(al, T4 - start) * .45;
        for (const b of bots) {
          b.pose(al + b.phase);
          const rin = seg(t, start + .15 + (rows - 1 - b.row) * .12, start + .6 + (rows - 1 - b.row) * .12);
          const rout = seg(t, T4 - .25 + b.row * .07, T4 + .25 + b.row * .07);
          b.reveal(rin * (1 - rout));
        }
        army.updateMatrixWorld(true);
        // screen
        screen.setTime(Math.max(0, t - tM), t);
        screen.reveal(seg(t, T4 + .75, T4 + 1.35));
        if (t > T4 - .1 && t < T4 + 1.9) {
          sw.points.visible = true; screen.sampleTargets(); sw.setColors(screen.colors, .3);
          sw.originsFrom(heroAtT4()); sw.update(screen.targets, seg(t, T4 - .05, T4 + 1.2), 0, t, { swirl: .3, fade: 1 - seg(t, T4 + 1.2, T4 + 1.8) });
        } else sw.points.visible = false;
        // camera: low sweep over the army, then orbit the screen
        const armyCam = orbitPos(v3(0, 0, -2), 6.6, lerp(.65, .12, ease.inOut((t - start) / (T4 - start))), lerp(.7, 1.05, seg(t, start, T4)));
        const armyLook = v3(0, 1.45, -5);
        const ao = lerp(.55, -.55, ease.inOut((t - T4) / (end - T4)));
        const scrCam = orbitPos(SC, lerp(4.4, 3.7, ease.inOut((t - T4) / (end - T4))), ao, 1.85);
        const k = seg(t, T4 - .3, T4 + .9);
        setCam(camera, armyCam.lerp(scrCam, k), armyLook.lerp(SC.clone().add(v3(0, -.15, 0)), k));
        hero.bonePos('mixamorigHead', headP); headP.y += .1;
      },
      hud(g, lt, t) {
        if (t < T4 - .1) {
          HUD.headline(g, [[{ t: 'AT LEAST 10 BILLION', c: MUT_LIGHT }]], { y: 300, size: 76, reveal: (t - tLeast + .1) * 2.5, color: C.bg });
          HUD.headline(g, [[{ t: 'BY ', c: C.bg }, { t: '2040', c: C.signal }]], { y: 500, size: 210, reveal: (t - t2040 + .35) * 2.2, color: C.bg });
          const p = HUD.project(headP, camera);
          if (t > start + 1.1) HUD.callout(g, p.x, p.y, p.x + 150, p.y + 40, ['UNIT 0001', `x. 4197  y. ${1693 + Math.round(t * 7)}`], { color: C.bg, alpha: Math.min(1, (t - start - 1.1) * 4) * (1 - seg(t, T4 - .4, T4 - .2)) });
        } else if (t < tM + .4) {
          HUD.headline(g, [[{ t: 'HE WENT ', c: C.bg }, { t: 'FURTHER', c: C.signal }]], { y: 400, size: 140, reveal: (t - SEG.L4.s) * 2.4, color: C.bg });
        } else if (t < muskAt('MB', 3.25)) {
          HUD.headline(g, [[{ t: 'AT LEAST A ', c: C.bg }, { t: 'BILLION', c: C.signal }, { t: ' ROBOTS', c: C.bg }], [{ t: 'IN 10 YEARS', c: C.bg }]], { y: 330, size: 110, reveal: (t - muskAt('MB', .9)) * 2.4, color: C.bg });
        } else if (t < muskAt('MB', 6.7)) {
          HUD.headline(g, [[{ t: '5×', c: C.signal }, { t: ' THE OUTPUT', c: C.bg }], [{ t: 'OF A HUMAN', c: C.bg }]], { y: 330, size: 120, reveal: (t - muskAt('MB', 4.9)) * 2.4, color: C.bg });
        } else {
          HUD.headline(g, [[{ t: 'MORE PRODUCTIVE THAN', c: C.bg }]], { y: 330, size: 96, reveal: (t - muskAt('MB', 8.85)) * 2.6, color: C.bg });
          HUD.headline(g, [[{ t: 'ALL HUMANS ', c: C.bg }, { t: 'COMBINED', c: C.signal }]], { y: 430, size: 96, reveal: (t - muskAt('MB', 9.85)) * 2.6, color: C.bg });
        }
        if (t > T4 + 1.3) label(g, 'E. MUSK · 2026', HUD.project(screen.corner(-1, -1), camera), { color: MUT_LIGHT, alpha: seg(t, T4 + 1.3, T4 + 1.6) });
      },
    });
  }

  // ======================= ACT 3 · DARK · city =======================
  {
    const start = B('L5'), end = B('L6a');
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(36);
    lights(scene, { key: 3.8, rim: 2.2, amb: .1, keyPos: [-4, 6, 3], rimPos: [4, 3, -6] });
    const bands = [0, 1, 2, 3, 4, 5].map(() => mat(0xb5b5b5, .7));
    const r = FX.rng(77);
    for (const side of [-1, 1]) {
      for (let z = 4; z > -46;) {
        const d = 1.6 + r() * 2.2, w = 1.8 + r() * 3, h = 2 + Math.pow(r(), 1.6) * 9;
        const band = Math.min(5, Math.floor((4 - z) / 8));
        const m = box(w, h, d, bands[band]); m.position.set(side * (2.3 + w / 2 + r() * .4), h / 2, z - d / 2);
        scene.add(m);
        // rooftop boxes
        if (r() > .55) { const t = box(w * .3, .5, d * .3, bands[band]); t.position.set(m.position.x + (r() - .5) * w * .4, h + .25, m.position.z); scene.add(t); }
        z -= d + .25 + r() * .5;
      }
    }
    // street edges
    const se = []; for (const x of [-2.2, 2.2]) se.push(x, .002, 6, x, .002, -60);
    const sg = new THREE.BufferGeometry(); sg.setAttribute('position', new THREE.Float32BufferAttribute(se, 3));
    lines.add(new THREE.LineSegments(sg, new THREE.LineBasicMaterial({ color: PAL.paper, transparent: true, opacity: .55, fog: true })));
    lines.fog = new THREE.Fog(PAL.bg, 4, 40);
    lines.add(gridFloor(PAL.paper, { step: 1, opacity: .22 }));
    const hero = makeRobot().play('walk'); scene.add(hero.root);
    const walkers = [[-1.6, -9, 1, .3], [1.5, -14, -1, .9], [-1.4, -20, -1, .5], [1.7, -5, 1, .1]].map(([x, z, dir, ph]) => {
      const b = makeRobot({ dots: false }).play('walk'); b.root.position.set(x, 0, z); b.root.rotation.y = dir > 0 ? 0 : Math.PI; b.dir = dir; b.z0 = z; b.ph = ph; scene.add(b.root); return b;
    });
    const head = v3();
    addShot({
      name: 'a3_city', mode: 'dark', start, end, scene, lines, camera, mixTone: .4,
      events: [{ t: start, type: 'cut' }, { t: start + .05, type: 'build' }],
      update(lt, t) {
        bands.forEach((m, i) => m.reveal(seg(t, start + i * .07, start + .4 + i * .07)));
        hero.pose(lt + .4); hero.root.position.set(0, 0, -7 + lt * 1.05); hero.reveal(seg(t, start + .1, start + .5));
        for (const b of walkers) { b.pose(lt + b.ph); b.root.position.z = b.z0 + b.dir * lt * 1.05; b.reveal(seg(t, start + .2, start + .6)); }
        const p = ease.inOut(lt / (end - start));
        setCam(camera, v3(lerp(3, .8, p), lerp(9, 1.5, p), lerp(7, -1.2, p)), v3(0, lerp(1.0, 1.35, p), lerp(-10, -6, p)));
        hero.bonePos('mixamorigHead', head); head.y += .1;
      },
      hud(g, lt, t) {
        HUD.headline(g, [[{ t: 'WHAT WILL' }], [{ t: 'THEY DO' }, { t: '?', c: C.signal }]], { y: 360, size: 150, reveal: (t - SEG.L5.s) * 2.2 });
        const p = HUD.project(head, camera);
        if (lt > .9) HUD.trackBox(g, p.x, p.y, { s: 52, label: ['UNIT 0001', 'TASK: ?'], alpha: Math.min(1, (lt - .9) * 4) });
      },
    });
  }

  // ======================= ACT 4 · LIGHT · task vignettes (one per VO line, ~1.8 s each) =======================
  {
    const V = [
      { name: 'factory', start: B('L6a'), end: B('L6b'), word: 'FACTORY' },
      { name: 'warehouse', start: B('L6b'), end: B('L6c'), word: 'WAREHOUSE' },
      { name: 'groceries', start: B('L6c'), end: B('L6d'), word: 'GROCERIES' },
      { name: 'lawn', start: B('L6d'), end: B('L7'), word: 'LAWN' },
    ];
    for (const vg of V) {
      const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(36);
      lights(scene, { key: 3.0, rim: 1.8, amb: .55, keyPos: [3, 5, 4] });
      lines.fog = new THREE.Fog(PAL.paper, 5, 26); lines.add(gridFloor(PAL.bg, { step: .9, opacity: .38 }));
      const pm = mat(0xc4c4c4), dk = mat(0x3a3a3a);
      const props = new THREE.Group(); scene.add(props);
      const bot = makeRobot().play(vg.name === 'factory' ? 'idle' : 'walk'); scene.add(bot.root);
      let center = v3(0, 1, 0), cam0 = .75, cam1 = .25, rad = 4, camH = 1.7, upd = () => {}, follow = null;
      const D = vg.end - vg.start;
      if (vg.name === 'factory') {
        const belt = box(5, .12, .8, dk); belt.position.set(0, .8, .55); props.add(belt);
        for (let i = -2; i <= 2; i++) { const leg = box(.08, .8, .08, dk); leg.position.set(i * 1.1, .4, .55); props.add(leg); }
        const crates = []; for (let i = 0; i < 6; i++) { const c = box(.36, .3, .36, pm); props.add(c); crates.push(c); }
        upd = lt => crates.forEach((c, i) => { c.position.set(((i * .9 + lt * .9) % 5.4) - 2.7, 1.01, .55); });
        bot.root.position.set(0, 0, -.25);
        center = v3(0, 1.1, 0); cam0 = .75; cam1 = .3; rad = 4.0; camH = 1.8;
      } else if (vg.name === 'warehouse') {
        for (const x of [-1.35, 1.35]) for (let z = 1; z > -9; z -= 2.1) {
          for (const y of [0, .9, 1.8, 2.7]) { const sh = box(.9, .05, 2, pm); sh.position.set(x, y + .05, z); props.add(sh); }
          for (const dz of [-.95, .95]) for (const dx of [-.42, .42]) { const p = box(.05, 2.8, .05, dk); p.position.set(x + dx, 1.4, z + dz); props.add(p); }
          for (const y of [0, .9, 1.8]) for (const dz of [-.5, .4]) if ((x + z + y + dz) % 2 > -.6) { const c = box(.5, .42, .55, pm); c.position.set(x, y + .3, z + dz); props.add(c); }
        }
        upd = lt => { bot.root.position.set(0, 0, -2.6 + lt * .9); };
        center = v3(0, 1.15, -1.6); cam0 = .2; cam1 = -.1; rad = 4.6; camH = 1.6;
      } else if (vg.name === 'groceries') {
        const house = box(3.2, 2.6, 2.4, pm); house.position.set(.2, 1.3, -2.2); props.add(house);
        const roof = new THREE.Mesh(new THREE.CylinderGeometry(.01, 2.1, 1.3, 4, 1), pm); roof.rotation.y = Math.PI / 4; roof.scale.set(1.1, 1, .85); roof.position.set(.2, 3.25, -2.2); props.add(roof);
        const door = box(.8, 1.7, .05, dk); door.position.set(0, .85, -.98); props.add(door);
        const bag = box(.3, .36, .2, pm); scene.add(bag);
        const handP = v3();
        upd = lt => { bot.root.position.set(0, 0, -.55 + lt * .85); bot.root.rotation.y = 0; bot.root.updateMatrixWorld(true); bot.bonePos('mixamorigRightHand', handP); bag.position.copy(handP).add(v3(0, -.22, 0)); };
        follow = () => v3(0, 1.1, bot.root.position.z * .5); cam0 = .55; cam1 = .25; rad = 4.6; camH = 1.7;
      } else {
        const house = box(3, 2.4, 2.2, pm); house.position.set(-1.0, 1.2, -4.2); props.add(house);
        const roof = new THREE.Mesh(new THREE.CylinderGeometry(.01, 2, 1.2, 4, 1), pm); roof.rotation.y = Math.PI / 4; roof.position.set(-1.0, 3.0, -4.2); props.add(roof);
        const st = []; for (let x = -4; x <= 4; x += .5) st.push(x, .003, 2.5, x, .003, -3);
        const sg = new THREE.BufferGeometry(); sg.setAttribute('position', new THREE.Float32BufferAttribute(st, 3));
        lines.add(new THREE.LineSegments(sg, new THREE.LineBasicMaterial({ color: PAL.bg, transparent: true, opacity: .55 })));
        const mower = new THREE.Group(); const mb = box(.55, .28, .5, dk); mb.position.y = .2; mower.add(mb);
        const handle = box(.04, .04, .9, dk); handle.rotation.x = .75; handle.position.set(0, .55, -.38); mower.add(handle); props.add(mower);
        upd = lt => { const x = -.85 + lt * .8; bot.root.position.set(x, 0, .4); bot.root.rotation.y = Math.PI / 2; mower.position.set(x + .75, 0, .4); mower.rotation.y = Math.PI / 2; };
        follow = () => v3(bot.root.position.x + .35, 1.0, .3); cam0 = .5; cam1 = .2; rad = 4.4; camH = 1.6;
      }
      const head = v3();
      const sw = new FX.Swarm(4000, { color: INK_DARK, size: 2.6, seed: 50 + vg.start * 10 | 0 });
      const samp = new FX.RobotSampler(bot, 4000, 9);
      lines.add(sw.points);
      bot.pose(1); upd(0); bot.root.updateMatrixWorld(true); sw.scatter(follow ? follow() : center, 1.4, 3.5);
      addShot({
        name: 'a4_' + vg.name, mode: 'light', start: vg.start, end: vg.end, scene, lines, camera, mixTone: .32,
        events: [{ t: vg.start, type: 'cut' }, { t: vg.start + .02, type: 'assemble', short: 1 }],
        update(lt, t) {
          bot.pose(lt + 1); upd(lt); bot.root.updateMatrixWorld(true);
          pm.reveal(seg(lt, 0, .3)); dk.reveal(seg(lt, .03, .33)); bot.reveal(seg(lt, .12, .4));
          sw.update(samp.sample(), seg(lt, 0, .35), 0, t, { fade: 1 - seg(lt, .4, .65) }); sw.points.visible = lt < .7;
          const p = ease.inOut(lt / D), c = follow ? follow() : center;
          setCam(camera, orbitPos(c, rad, lerp(cam0, cam1, p), camH), c);
          bot.bonePos('mixamorigHead', head); head.y += .1;
        },
        hud(g, lt) {
          redacted(g, 'TASK: ', vg.word, { y: 380, size: 130, p: (lt - .05) * 2.2, ink: C.bg, bar: C.bg });
          const p = HUD.project(head, camera);
          if (lt > .35) HUD.trackBox(g, p.x, p.y, { s: 50, color: C.bg, label: ['UNIT 0001', 'TASK: ' + vg.word], alpha: Math.min(1, (lt - .35) * 5) });
        },
      });
    }
  }

  // ======================= ACT 5 · LIGHT · babysit screen -> robot pushes a human out of frame =======================
  {
    const start = B('L7'), end = B('L9'), T8 = B('L8');
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(34);
    lights(scene, { key: 3.0, rim: 1.8, amb: .55, keyPos: [3, 4, 4] });
    const SC = v3(0, 1.2, 0);
    const screen = new FX.Screen(footage.babysit_sofa, { height: 1.1, mode: 'light', contrast: 1.3, bright: .02 });
    screen.group.position.copy(SC); lines.add(screen.group);
    const swS = new FX.Swarm(screen.count, { color: INK_DARK, size: 2.7, seed: 61 }).scatter(SC, 2, 5);
    const human = makeRobot({ dots: false, visor: false, color: 0x6f6b66 }).play('idle'); scene.add(human.root);
    const bot = makeRobot().play('walk'); scene.add(bot.root);
    const hsamp = new FX.RobotSampler(human, 9000, 41);
    const swP = new FX.Swarm(9000, { color: INK_DARK, size: 2.6, seed: 62 });
    lines.add(swS.points, swP.points);
    lines.fog = new THREE.Fog(PAL.paper, 5, 26); lines.add(gridFloor(PAL.bg, { step: .9, opacity: .4 }));
    const scrAtT8 = once(() => { screen.setTime(T8 - start - .9, T8); return screen.sampleTargets().slice(); });
    const hand = v3(), hHead = v3(), rHead = v3();
    const tBaby = wt('babysit', SEG.L7.s), tTw = wt('20000', SEG.L8.s);
    const tIn = T8 + .4, tMeet = T8 + 1.85, tPush = T8 + 1.9, tGone = T8 + 3.9, tTurn = T8 + 2.75;
    let botAnim = 'walk', humAnim = 'idle';
    const setAnim = (who, name, cur) => { if (cur !== name) who.play(name); return name; };
    addShot({
      name: 'a5_babysit_replace', mode: 'light', start, end, scene, lines, camera, mixTone: .32,
      events: [{ t: start, type: 'cut' }, { t: start + .02, type: 'assemble' }, { t: T8 - .15, type: 'disperse' }, { t: T8 + .05, type: 'assemble' }, { t: tPush, type: 'hit' }, { t: tTw, type: 'hit' }],
      update(lt, t) {
        screen.setTime(Math.max(0, lt - .9), t);
        screen.reveal(seg(t, start + .7, start + 1.25) * (1 - seg(t, T8 - .2, T8 + .2)));
        if (t < start + 1.9) { swS.points.visible = true; screen.sampleTargets(); swS.setColors(screen.colors, .3); swS.update(screen.targets, seg(t, start, start + 1.1), 0, t, { swirl: .3, fade: 1 - seg(t, start + 1.1, start + 1.7) }); }
        else swS.points.visible = false;
        // human: assembles from the screen's particles, then gets shoved out to the left
        humAnim = setAnim(human, t < tPush ? 'idle' : 'walk', humAnim);
        human.pose(t < tPush ? lt + 2 : (t - tPush) * 1.6 + .3);
        const hx = t < tPush ? 0 : -(seg(t, tPush, tPush + .35) * .35 + Math.max(0, t - tPush - .2) * 1.15);
        human.root.position.set(hx, 0, 0); human.root.rotation.y = t < tPush ? 0 : -Math.PI / 2 * seg(t, tPush, tPush + .15);
        human.reveal(seg(t, T8 + .55, T8 + 1.0));
        if (t > T8 - .25 && t < T8 + 1.6) { swP.points.visible = true; swP.originsFrom(scrAtT8()); swP.update(hsamp.sample(), seg(t, T8 - .2, T8 + .9), 0, t, { swirl: .28, fade: 1 - seg(t, T8 + .95, T8 + 1.4) }); }
        else swP.points.visible = false;
        // robot: walks in from the right, takes the human's spot, turns to camera
        botAnim = setAnim(bot, t < tTurn + .2 ? 'walk' : 'idle', botAnim);
        bot.pose(t - tIn + .2);
        const bx = t < tMeet ? lerp(2.9, .45, seg(t, tIn, tMeet)) : lerp(.45, 0, seg(t, tMeet, tTurn));
        bot.root.position.set(bx, 0, 0); bot.root.rotation.y = -Math.PI / 2 * (1 - seg(t, tTurn, tTurn + .45));
        bot.reveal(seg(t, tIn - .1, tIn + .2));
        // camera
        const a = lerp(.65, -.65, ease.inOut(lt / (end - start)));
        const kk = seg(t, T8 - .3, T8 + .8);
        setCam(camera, orbitPos(v3(0, 0, 0), lerp(3.9, 6.2, kk), lerp(a, a * .3, kk), lerp(1.45, 1.55, kk)), v3(0, lerp(1.12, 1.15, kk), 0));
        bot.bonePos('mixamorigRightHand', hand); human.bonePos('mixamorigHead', hHead); bot.bonePos('mixamorigHead', rHead); hHead.y += .1; rHead.y += .1;
      },
      hud(g, lt, t) {
        if (t < T8 - .1) {
          redacted(g, 'TASK: ', 'BABYSITTING', { y: 380, size: 120, p: (t - tBaby + .1) * 1.8, ink: C.bg, bar: C.bg, alpha: seg(t, start + .3, start + .5) });
          if (t < tBaby - .1) HUD.mono(g, 'IN HIS OWN WORDS', W / 2, 300, { size: 22, align: 'center', color: MUT_LIGHT, alpha: seg(t, start + .4, start + .7), spacing: .22 });
          return;
        }
        HUD.headline(g, [[{ t: 'ONE ROBOT THAT', c: C.bg }], [{ t: 'COULD REPLACE ', c: C.bg }, { t: 'YOU', c: C.signal }, { t: '?', c: C.bg }]], { y: 300, size: 96, reveal: (t - SEG.L8.s) * 2, color: C.bg });
        if (t > tTw - .2) HUD.headline(g, [[{ t: 'FROM ', c: C.bg }, { t: '$20,000', c: C.signal }]], { y: 560, size: 150, reveal: (t - tTw + .15) * 2.2, color: C.bg });
        // labels
        const ph = HUD.project(hHead, camera);
        if (t > T8 + 1.0 && ph.x > -40) {
          const al = seg(t, T8 + 1.0, T8 + 1.3);
          HUD.trackBox(g, ph.x, ph.y, { s: 54, color: C.bg, side: 'left', label: [t < tPush ? 'HUMAN' : 'REPLACED'], alpha: al });
          if (t > tPush) { g.save(); g.globalAlpha = al; g.strokeStyle = C.signal; g.lineWidth = 3; g.beginPath(); g.moveTo(ph.x - 30, ph.y - 30); g.lineTo(ph.x + 30, ph.y + 30); g.moveTo(ph.x + 30, ph.y - 30); g.lineTo(ph.x - 30, ph.y + 30); g.stroke(); g.restore(); }
        }
        const pr = HUD.project(rHead, camera);
        if (t > tIn + .4) HUD.trackBox(g, pr.x, pr.y, { s: 54, color: C.bg, label: ['UNIT 0001'], alpha: seg(t, tIn + .4, tIn + .7) });
        const a = seg(t, tTw + .1, tTw + .4);
        if (a > 0) {
          const h = HUD.project(hand, camera), tx = h.x - 110 + Math.sin(t * 2.1) * 10, ty = h.y + 120;
          g.save(); g.globalAlpha = a; g.strokeStyle = C.bg; g.lineWidth = 2; g.beginPath(); g.moveTo(h.x, h.y); g.lineTo(tx + 60, ty - 24); g.stroke();
          g.translate(tx + 60, ty + 10); g.rotate(-.12 + Math.sin(t * 2.1) * .04);
          g.fillStyle = C.signal; g.beginPath(); g.moveTo(-60, -34); g.lineTo(44, -34); g.lineTo(66, 0); g.lineTo(44, 34); g.lineTo(-60, 34); g.closePath(); g.fill();
          g.fillStyle = C.bg; g.beginPath(); g.arc(46, 0, 6, 0, Math.PI * 2); g.fill();
          g.font = '800 44px "Barlow Condensed"'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('$20K', -8, 2); g.restore();
        }
      },
    });
  }

  // ======================= ACT 6 · DARK · the math: a calculator types it out =======================
  {
    const start = B('L9'), end = B('L10');
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(34);
    lights(scene, { key: 3.4, rim: 3.0, amb: .2, keyPos: [2, 4, 4], rimPos: [-3, 2, -5] });
    // background: robots trickling out one by one along the signal line
    const N = 6, line = [];
    for (let i = 0; i < N; i++) { const b = makeRobot({ dots: false }).play('walk'); b.root.rotation.y = Math.PI; b.i = i; scene.add(b.root); line.push(b); }
    const wl = []; for (let z = 4; z > -80; z -= .1) wl.push(new THREE.Vector3(Math.sin(z * 1.7) * .03 + 1.6, .003, z));
    lines.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(wl), new THREE.LineBasicMaterial({ color: PAL.signal, transparent: true })));
    lines.fog = new THREE.Fog(PAL.bg, 3, 30); lines.add(gridFloor(PAL.paper, { step: .8, opacity: .26 }));
    // calculator
    const CP = v3(0, 1.3, .4);
    const calc = new THREE.Group(); calc.position.copy(CP); calc.rotation.x = -.32; scene.add(calc);
    const bodyM = mat(0x8a8a8a, .5), keyM = mat(0xdedede, .45), opM = mat(0x555555, .45);
    const body = box(1.0, 1.62, .14, bodyM); calc.add(body);
    const bezel = box(.9, .4, .02, mat(0x222222)); bezel.position.set(0, .53, .075); calc.add(bezel);
    const LAYOUT = [['C', '±', '%', '÷'], ['7', '8', '9', '×'], ['4', '5', '6', '−'], ['1', '2', '3', '+'], ['0', '00', '.', '=']];
    const keys = {};
    LAYOUT.forEach((row, r) => row.forEach((ch, c) => {
      const isOp = c === 3 || r === 0;
      const k = box(.19, .15, .05, isOp ? opM : keyM); k.position.set(-.33 + c * .22, .2 - r * .19, .09); calc.add(k); keys[ch] = k;
    }));
    // display lives in the clean layer, glued to the calculator each frame
    const dc = document.createElement('canvas'); dc.width = 640; dc.height = 288; const dg = dc.getContext('2d');
    const dTex = new THREE.CanvasTexture(dc); dTex.colorSpace = THREE.SRGBColorSpace;
    const disp = new THREE.Mesh(new THREE.PlaneGeometry(.86, .36), new THREE.MeshBasicMaterial({ map: dTex, transparent: true }));
    const dispG = new THREE.Group(); dispG.add(disp); disp.position.set(0, .53, .088); lines.add(dispG);
    // printed key legends (clean layer)
    const kc = document.createElement('canvas'); kc.width = 512; kc.height = 512; const kg = kc.getContext('2d');
    kg.font = '600 46px "IBM Plex Mono"'; kg.textAlign = 'center'; kg.textBaseline = 'middle';
    LAYOUT.forEach((row, r) => row.forEach((ch, c) => { kg.fillStyle = (c === 3 || r === 0) ? '#ff531f' : '#14120f'; kg.fillText(ch, 64 + c * 128, 51 + r * 102); }));
    const kTex = new THREE.CanvasTexture(kc); kTex.colorSpace = THREE.SRGBColorSpace;
    const legend = new THREE.Mesh(new THREE.PlaneGeometry(.88, .95), new THREE.MeshBasicMaterial({ map: kTex, transparent: true, depthWrite: false }));
    legend.position.set(0, .2 - .19 * 2, .118); dispG.add(legend);
    // key schedule
    const tMil = wt('million', SEG.L9.s);
    const tTenB = WORDS.filter(w => w.s > tMil + 1).find(w => norm(w.w) === '10')?.s ?? (tMil + 2);
    const tYears = WORDS.filter(w => w.s > tMil + 1).find(w => norm(w.w).startsWith('10000'))?.s ?? (SEG.L9.e - 1.4);
    const sched = []; const type = (str, t0, dt) => [...str].forEach((ch, i) => sched.push({ ch, t: t0 + i * dt }));
    type('1000000', tMil - .45, .07);
    sched.push({ ch: 'C', t: tTenB - .35 });
    type('10000000000', tTenB - .2, .075);
    sched.push({ ch: '÷', t: tTenB + .7 });
    type('1000000', tTenB + .85, .07);
    sched.push({ ch: '=', t: tYears - .12 });
    const fmt = d => d ? Number(d).toLocaleString('en-US') : '0';
    function dispState(t) {
      let cur = '', hist = '', res = false;
      for (const k of sched) { if (k.t > t) break;
        if (k.ch === 'C') { cur = ''; hist = ''; }
        else if (k.ch === '÷') { hist = fmt(cur) + ' ÷'; cur = ''; }
        else if (k.ch === '=') { hist = hist + ' ' + fmt(cur) + ' ='; cur = '10000'; res = true; }
        else cur += k.ch; }
      return { cur: fmt(cur), hist, res };
    }
    let lastDisp = '';
    function drawDisplay(t) {
      const st = dispState(t), keyStr = JSON.stringify(st) + (Math.floor(t * 2) % 2);
      if (keyStr === lastDisp) return; lastDisp = keyStr;
      dg.fillStyle = '#0e0d0b'; dg.fillRect(0, 0, 640, 288);
      dg.fillStyle = '#77726b'; let hs = 34; dg.font = `500 ${hs}px "IBM Plex Mono"`; dg.textAlign = 'right';
      while (dg.measureText(st.hist).width > 590 && hs > 16) { hs -= 2; dg.font = `500 ${hs}px "IBM Plex Mono"`; }
      dg.fillText(st.hist, 610, 64);
      dg.fillStyle = st.res ? '#ff531f' : '#e8e3db'; dg.font = '600 96px "IBM Plex Mono"';
      let fs = 96; while (dg.measureText(st.cur).width > 590 && fs > 40) { fs -= 4; dg.font = `600 ${fs}px "IBM Plex Mono"`; }
      dg.fillText(st.cur, 610, 210);
      if (!st.res && Math.floor(t * 2) % 2) { dg.fillStyle = '#ff531f'; dg.fillRect(612, 150, 6, 70); }
      dTex.needsUpdate = true;
    }
    const pressed = t => { const k = [...sched].reverse().find(k => k.t <= t && t - k.t < .12); return k ? k.ch : null; };
    // particles assemble the calculator face
    const NP = 5000, faceLocal = new Float32Array(NP * 3), r = FX.rng(66);
    for (let i = 0; i < NP; i++) { faceLocal[i * 3] = (r() - .5) * 1.0; faceLocal[i * 3 + 1] = (r() - .5) * 1.62; faceLocal[i * 3 + 2] = .075; }
    const swC = new FX.Swarm(NP, { color: INK_LIGHT, size: 2.6, seed: 67 }).scatter(CP, 2, 5); lines.add(swC.points);
    const faceW = new Float32Array(NP * 3), tmp = v3();
    addShot({
      name: 'a6_math', mode: 'dark', start, end, scene, lines, camera, mixTone: .4,
      events: [{ t: start, type: 'cut' }, { t: start + .02, type: 'assemble' }, ...sched.map(k => ({ t: k.t, type: 'key' })), { t: tYears + .05, type: 'hit' }],
      update(lt, t) {
        for (const b of line) { b.pose(lt + b.i * .3); b.root.position.set(1.6, 0, -3 - b.i * 2.4 - lt * .8); b.reveal(seg(t, start + .6 + b.i * .9, start + .9 + b.i * .9)); }
        calc.rotation.y = Math.sin(lt * .5) * .12; calc.position.y = CP.y + Math.sin(lt * 1.3) * .02;
        const rv = seg(lt, .35, .85); bodyM.reveal(rv); keyM.reveal(seg(lt, .45, .95)); opM.reveal(seg(lt, .45, .95)); bezel.material.reveal(rv);
        const pk = pressed(t);
        for (const [ch, k] of Object.entries(keys)) k.position.z = ch === pk ? .065 : .09;
        calc.updateMatrixWorld(true); dispG.matrix.copy(calc.matrixWorld); dispG.matrixAutoUpdate = false; dispG.matrixWorldNeedsUpdate = true;
        disp.visible = lt > .8; legend.visible = lt > .95; drawDisplay(t);
        if (lt < 1.4) { swC.points.visible = true; for (let i = 0; i < NP * 3; i += 3) { tmp.set(faceLocal[i], faceLocal[i + 1], faceLocal[i + 2]).applyMatrix4(calc.matrixWorld); faceW[i] = tmp.x; faceW[i + 1] = tmp.y; faceW[i + 2] = tmp.z; } swC.update(faceW, seg(lt, 0, .7), 0, t, { fade: 1 - seg(lt, .75, 1.2) }); }
        else swC.points.visible = false;
        // camera: orbit, then push in on the display for the result
        const p = ease.inOut(lt / (end - start)), push = seg(t, tYears - .3, tYears + .6);
        const c = CP.clone().add(v3(0, lerp(0, .45, push), 0));
        setCam(camera, orbitPos(c, lerp(lerp(3.5, 2.9, p), 2.35, push), lerp(.55, -.35, p), lerp(2.0, 1.95, p) + .35 * push), c);
      },
      hud(g, lt, t) {
        if (t < tMil - .1) HUD.headline(g, [[{ t: 'NOW, THE ' }, { t: 'MATH', c: C.signal }]], { y: 380, size: 150, reveal: (t - SEG.L9.s) * 2.4 });
        else if (t < tYears - .1) {
          HUD.headline(g, [[{ t: '1,000,000 ROBOTS / YEAR' }]], { y: 330, size: 96, reveal: (t - tMil + .1) * 2.4 });
          HUD.mono(g, "TESLA'S TARGET", W / 2, 390, { size: 20, align: 'center', color: C.muted, alpha: seg(t, tMil + .3, tMil + .6) });
        } else {
          HUD.headline(g, [[{ t: '10,000', c: C.signal }, { t: ' YEARS' }]], { y: 380, size: 170, reveal: (t - tYears + .05) * 2.6 });
          HUD.mono(g, 'TO REACH 10 BILLION', W / 2, 440, { size: 22, align: 'center', color: C.muted, alpha: seg(t, tYears + .4, tYears + .7), spacing: .2 });
        }
      },
    });
  }

  // ======================= ACT 7 · DARK · something changes -> recursive =======================
  {
    const start = B('L10'), end = B('L11'), tMC = SEG.MC.s;
    const tS = wt('something', SEG.L10.s) - .3;
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(34);
    lights(scene, { key: 3.4, rim: 3.0, amb: .12 });
    const hero = makeRobot().play('idle'); scene.add(hero.root);
    const hs = new FX.RobotSampler(hero, 9000, 71);
    const CS = v3(0, 1.35, 0);
    const clone = new FX.Screen(footage.clone_body, { height: 1.45, mode: 'dark', contrast: 1.25 }); clone.group.position.copy(CS); lines.add(clone.group);
    const MS = v3(0, 2.75, -1.6);
    const musk = new FX.Screen(footage.musk_c, { height: .62, mode: 'dark', contrast: 1.15, bright: .04 }); musk.group.position.copy(MS); lines.add(musk.group);
    const R = [v3(-.95, 0, .5), v3(0, 0, -.45), v3(.95, 0, .5)].map((p, i) => { const b = makeRobot().play('idle'); b.root.position.copy(p); b.root.rotation.y = -p.x * .25; scene.add(b.root); b.s = new FX.RobotSampler(b, 7000, 80 + i); return b; });
    const swC = new FX.Swarm(clone.count, { color: INK_LIGHT, size: 2.7, seed: 72 });
    const swM = new FX.Swarm(musk.count, { color: INK_LIGHT, size: 2.4, seed: 73 });
    const sw12 = new FX.Swarm(7000, { color: INK_LIGHT, size: 2.5, seed: 74 }), sw23 = new FX.Swarm(7000, { color: INK_LIGHT, size: 2.5, seed: 75 });
    const sw01 = new FX.Swarm(7000, { color: INK_LIGHT, size: 2.5, seed: 76 });
    lines.add(swC.points, swM.points, sw12.points, sw23.points, sw01.points);
    lines.fog = new THREE.Fog(PAL.bg, 3, 18); lines.add(gridFloor(PAL.paper, { step: .8, opacity: .28 }));
    const heroAtS = once(() => { hero.pose(tS - start + 3); return hs.sample().slice(); });
    const cloneAtMC = once(() => { clone.setTime(tMC - tS - .8, tMC); return clone.sampleTargets().slice(); });
    const r1 = tMC + .25, r2 = tMC + .95, r3 = tMC + 1.75;
    const r1At = once(() => { R[0].pose(r2 - tMC + 1); return R[0].s.sample().slice(); });
    const r2At = once(() => { R[1].pose(r3 - tMC + 2); return R[1].s.sample().slice(); });
    const tRec = muskAt('MC', 38.24);
    addShot({
      name: 'a7_change', mode: 'dark', start, end, scene, lines, camera, mixTone: .42,
      glitch: lt => { const t = lt + start; return Math.max(pulse(t, tS, .35) * .9, pulse(t, tMC, .25) * .6, (t > start + .3 && t < tS) ? .12 * (Math.sin(t * 40) > .7 ? 1 : 0) : 0); },
      events: [{ t: start, type: 'cut' }, { t: tS, type: 'glitch' }, { t: tS + .02, type: 'assemble' }, { t: tMC - .1, type: 'disperse' }, { t: tMC + .05, type: 'assemble' }, { t: r2, type: 'assemble', short: 1 }, { t: r3, type: 'assemble', short: 1 }, { t: tRec, type: 'hit' }],
      update(lt, t) {
        hero.pose(Math.min(lt, tS - start) + 3); hero.root.position.set(0, 0, 0);
        hero.reveal(seg(t, start, start + .3) * (1 - seg(t, tS - .1, tS + .3)));
        // clone screen
        clone.setTime(Math.max(0, t - tS - .8), t);
        clone.reveal(seg(t, tS + .65, tS + 1.15) * (1 - seg(t, tMC - .15, tMC + .2)));
        if (t > tS - .1 && t < tS + 1.8) { swC.points.visible = true; clone.sampleTargets(); swC.setColors(clone.colors, .6); swC.originsFrom(heroAtS()); swC.update(clone.targets, seg(t, tS - .05, tS + 1.05), 0, t, { swirl: .3, fade: 1 - seg(t, tS + 1.1, tS + 1.7) }); }
        else swC.points.visible = false;
        // musk screen + recursive robots
        musk.setTime(Math.max(0, t - tMC), t);
        musk.reveal(seg(t, tMC + .55, tMC + 1.0));
        if (t > tMC - .2 && t < tMC + 1.6) { swM.points.visible = true; musk.sampleTargets(); swM.setColors(musk.colors, .6); swM.originsFrom(cloneAtMC()); swM.update(musk.targets, seg(t, tMC - .15, tMC + .9), 0, t, { swirl: .3, fade: 1 - seg(t, tMC + .9, tMC + 1.5) }); }
        else swM.points.visible = false;
        R.forEach((b, i) => b.pose(t - tMC + 1 + i));
        R[0].reveal(seg(t, r1 - .1, r1 + .35)); R[1].reveal(seg(t, r2 + .45, r2 + .85)); R[2].reveal(seg(t, r3 + .45, r3 + .85));
        if (t > r1 - .3 && t < r1 + .9) { sw01.points.visible = true; sw01.originsFrom(cloneAtMC()); sw01.update(R[0].s.sample(), seg(t, r1 - .3, r1 + .3), 0, t, { fade: 1 - seg(t, r1 + .35, r1 + .8) }); } else sw01.points.visible = false;
        if (t > r2 - .05 && t < r2 + 1.3) { sw12.points.visible = true; sw12.originsFrom(r1At()); sw12.update(R[1].s.sample(), seg(t, r2, r2 + .75), 0, t, { swirl: .35, fade: 1 - seg(t, r2 + .8, r2 + 1.2) }); } else sw12.points.visible = false;
        if (t > r3 - .05 && t < r3 + 1.3) { sw23.points.visible = true; sw23.originsFrom(r2At()); sw23.update(R[2].s.sample(), seg(t, r3, r3 + .75), 0, t, { swirl: .35, fade: 1 - seg(t, r3 + .8, r3 + 1.2) }); } else sw23.points.visible = false;
        // camera
        const kk = seg(t, tMC - .2, tMC + .8);
        const a = lerp(lerp(-.5, .2, ease.inOut((t - start) / (tMC - start))), lerp(-.25, .25, ease.inOut((t - tMC) / (end - tMC))), kk);
        setCam(camera, orbitPos(v3(0, 0, 0), lerp(3.8, 7.4, kk), a, lerp(1.5, 1.75, kk)), v3(0, lerp(1.3, 1.55, kk), lerp(0, -.3, kk)));
      },
      hud(g, lt, t) {
        if (t < tMC - .1) {
          HUD.headline(g, [[{ t: 'EITHER THE PLAN IS WRONG', c: C.soft }]], { y: 300, size: 70, reveal: (t - SEG.L10.s) * 2.4 });
          HUD.headline(g, [[{ t: 'OR SOMETHING ' }, { t: 'CHANGES', c: C.signal }]], { y: 440, size: 130, reveal: (t - tS - .05) * 2.4 });
          if (t > tS + 1.1) label(g, 'CLONE ROBOTICS · SYNTHETIC HUMAN', HUD.project(clone.corner(-1, -1), camera), { alpha: seg(t, tS + 1.1, tS + 1.4) });
        } else {
          if (t < tRec - .15) HUD.headline(g, [[{ t: 'ROBOTS MAKING ' }, { t: 'ROBOTS', c: C.signal }]], { y: 330, size: 120, reveal: (t - tMC - .1) * 2.4 });
          else HUD.headline(g, [[{ t: 'A RECURSIVE ' }, { t: 'EFFECT', c: C.signal }]], { y: 330, size: 130, reveal: (t - tRec + .15) * 2.6 });
          if (t > tMC + .9) label(g, 'E. MUSK · 2026', HUD.project(musk.corner(-1, -1), camera), { alpha: seg(t, tMC + .9, tMC + 1.2), dy: 30, size: 16 });
        }
      },
    });
  }

  // ======================= ACT 8 · DARK · the 2027 marker =======================
  {
    const start = B('L11'), end = B('L12');
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(34);
    const X = y => (y - 2027) * .9;
    const pts = [], posts = [];
    pts.push(X(2023), .002, 0, X(2041), .002, 0);
    for (let y = 2024; y <= 2040; y++) { const h = y % 5 === 0 || y === 2024 ? .9 : .45; if (y !== 2027) pts.push(X(y), 0, 0, X(y), h, 0); posts.push(y); }
    const pg = new THREE.BufferGeometry(); pg.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
    lines.add(new THREE.LineSegments(pg, new THREE.LineBasicMaterial({ color: PAL.paper, transparent: true, opacity: .6 })));
    const p27g = new THREE.BufferGeometry(); p27g.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0, 0, 1, 0], 3));
    const p27 = new THREE.Line(p27g, new THREE.LineBasicMaterial({ color: PAL.signal })); lines.add(p27);
    const ring = wireSphere(.12, PAL.signal, { lat: 6, lon: 8, opacity: .9 }); lines.add(ring);
    const N = 5000, col = []; const tg = new Float32Array(N * 3);
    const sw = new FX.Swarm(N, { color: SIG, size: 2.4, seed: 91 }).scatter(v3(0, 1.2, 0), 2, 7, .6); lines.add(sw.points);
    lines.fog = new THREE.Fog(PAL.bg, 3, 22); lines.add(gridFloor(PAL.paper, { step: .9, opacity: .22 }));
    const tFirst = wt('first', SEG.L11.s), tLate = wt('late', SEG.L11.s);
    addShot({
      name: 'a8_2027', mode: 'dark', start, end, scene, lines, camera, mixTone: .42, noChrome: true,
      events: [{ t: start, type: 'cut' }, { t: tLate - .7, type: 'riser', d: .9 }, { t: tLate + .2, type: 'hit', big: 1 }],
      update(lt, t) {
        const grow = seg(t, tLate - .3, tLate + .5);
        const h = lerp(.9, 1.6, grow); p27g.attributes.position.setY(1, h); p27g.attributes.position.needsUpdate = true;
        ring.position.set(0, h, 0); ring.rotation.y = t; ring.visible = grow > .05;
        for (let i = 0; i < N; i++) { tg[i * 3] = 0; tg[i * 3 + 1] = (i / N) * h; tg[i * 3 + 2] = 0; }
        sw.update(tg, seg(t, tLate - .9, tLate + .3), 0, t, { swirl: .2, fade: 1 - seg(t, tLate + .4, tLate + 1.0) });
        sw.points.visible = t > tLate - 1 && t < tLate + 1.1;
        const p = ease.inOut(seg(t, start, tLate));
        const cx = lerp(X(2038), 0, p);
        setCam(camera, v3(cx + lerp(1.4, .5, p), lerp(1.3, 1.35, p), lerp(4.6, 5.6, p)), v3(cx - lerp(.8, 0, p), lerp(.6, 1.05, p), 0));
        this._posts = posts;
      },
      hud(g, lt, t) {
        for (const y of posts) {
          const is27 = y === 2027; if (is27 && t > tLate - .15) continue; const h = is27 ? lerp(.9, 1.6, seg(t, tLate - .3, tLate + .5)) : (y % 5 === 0 || y === 2024 ? .9 : .45);
          const p = HUD.project(v3(X(y), h + .12, 0), camera);
          if (p.x < -50 || p.x > W + 50) continue;
          HUD.mono(g, String(y), p.x, p.y, { size: is27 ? 30 : 22, align: 'center', color: is27 ? C.signal : C.soft, weight: is27 ? 600 : 500, alpha: is27 ? 1 : .8 });
        }
        if (t < tLate - .1) HUD.headline(g, [[{ t: 'FIRST ROBOTS FOR' }], [{ t: 'OUTSIDE CUSTOMERS' }, { t: '?', c: C.signal }]], { y: 360, size: 120, reveal: (t - tFirst + .1) * 2.2 });
        else {
          HUD.mono(g, 'REPORTEDLY', W / 2, 290, { size: 22, align: 'center', color: C.muted, spacing: .24, alpha: seg(t, tLate - .2, tLate + .1) });
          HUD.headline(g, [[{ t: 'LATE ' }, { t: '2027', c: C.signal }]], { y: 450, size: 190, reveal: (t - tLate + .05) * 2.6 });
        }
      },
    });
  }

  // ======================= ACT 9 · DARK · coincidence? 2027 =======================
  {
    const start = B('L12'), end = DUR;
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(34);
    lights(scene, { key: 1.6, rim: 4.2, amb: .06, keyPos: [2, 3, 4], rimPos: [0, 3, -6] });
    const tCoin = wt('coincidence', SEG.L12.s) + .25, tEnd = SEG.L13.s;
    const army = []; const r = FX.rng(5);
    for (let rr = 0; rr < 5; rr++) for (let c = 0; c < 5; c++) {
      const b = makeRobot({ dots: rr < 2 }).play('idle'); b.root.position.set((c - 2) * 1.15 + (rr % 2) * .25, 0, -rr * 1.5); b.yaw = (r() > .5 ? 1 : -1) * (.6 + r() * .5); b.d = r() * .25; b.ph = r() * 3;
      scene.add(b.root); army.push(b);
    }
    lines.fog = new THREE.Fog(PAL.bg, 3, 18); lines.add(gridFloor(PAL.paper, { step: .9, opacity: .22 }));
    addShot({
      name: 'a9_end', mode: 'dark', start, end, scene, lines, camera, mixTone: .42,
      events: [{ t: start, type: 'cut' }, { t: start + .05, type: 'build' }, { t: tCoin, type: 'turn' }, { t: tEnd + .45, type: 'hit', big: 1 }],
      update(lt, t) {
        for (const b of army) {
          b.pose(t + b.ph);
          headTurn(b, b.yaw * (1 - seg(t, tCoin + b.d, tCoin + b.d + .22)));
          b.reveal(seg(t, start + .05 + b.d, start + .5 + b.d) * (1 - seg(t, tEnd + .1 + b.d, tEnd + .6 + b.d)));
        }
        const p = ease.inOut(lt / (end - start));
        setCam(camera, v3(0, lerp(1.3, 1.5, p), lerp(6.5, 5.2, p)), v3(0, lerp(1.25, 1.6, p), -2));
      },
      hud(g, lt, t) {
        if (t < tEnd - .05) HUD.headline(g, [[{ t: 'COINCIDENCE' }, { t: '?', c: C.signal }]], { y: 400, size: 150, reveal: (t - tCoin + .3) * 2.4 });
        else {
          HUD.mono(g, 'EVERY PREDICTION LEADS TO', W / 2, 770, { size: 28, align: 'center', color: C.soft, alpha: seg(t, tEnd, tEnd + .3), spacing: .22 });
          HUD.headline(g, [[{ t: '2027', c: C.signal }]], { y: 1010, size: 320, reveal: (t - tEnd - .35) * 2.4 });
          HUD.mono(g, 'FOLLOW THE SIGNAL', W / 2, 1110, { size: 24, align: 'center', alpha: seg(t, SEG.L13.e + .2, SEG.L13.e + .6), spacing: .24 });
        }
      },
    });
  }

  return shots;
}
