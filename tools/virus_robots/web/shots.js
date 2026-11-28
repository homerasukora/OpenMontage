// Style-test sequence: "10 billion robots" (VIRUS2027). Each shot = 3D scene + clean line layer + HUD.
export async function buildShots(K) {
  const { THREE, PAL, makeRobot, gridFloor, wireSphere, HUD, ease } = K;
  const { C } = HUD;
  const v3 = (x, y, z) => new THREE.Vector3(x, y, z);
  const ASPECT = K.W / K.H;

  function lights(scene, { key = 3.2, rim = 2.4, amb = .25, keyPos = [2.5, 3, 2.5], rimPos = [-3, 2.5, -3] } = {}) {
    scene.add(new THREE.HemisphereLight(0xffffff, 0x202020, amb));
    const k = new THREE.DirectionalLight(0xffffff, key); k.position.set(...keyPos); scene.add(k);
    const r = new THREE.DirectionalLight(0xffffff, rim); r.position.set(...rimPos); scene.add(r);
  }
  const cam = (fov = 34) => new THREE.PerspectiveCamera(fov, ASPECT, .05, 200);

  const shots = [];

  // ---------------- 01 · DARK · single unit + counter ----------------
  {
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(30);
    lights(scene, { key: 3.6, rim: 3.2, amb: .12, keyPos: [2, 2.5, 3], rimPos: [-2.5, 2, -2] });
    const bot = makeRobot().play('idle');
    scene.add(bot.root);
    lines.fog = new THREE.Fog(PAL.bg, 3, 14);
    lines.add(gridFloor(PAL.paper, { step: .6, opacity: .35 }));
    const head = v3();
    shots.push({
      name: '01_unit', index: '01 / 05  SIGNAL DETECTED', mode: 'dark', dur: 4.6, scene, lines, camera, mixTone: .42,
      update(lt) {
        bot.pose(lt + 2);
        const p = ease.inOut(lt / 4.6);
        camera.position.set(.38 - .3 * p, 1.42, 2.0 - .45 * p);
        camera.lookAt(0, 1.62, 0);
        camera.updateMatrixWorld();
        bot.bonePos('mixamorigHead', head); head.y += .1;
      },
      hud(g, lt) {
        // counter 0 -> 10,000,000,000
        const k = ease.inOut((lt - .3) / 2.2);
        const val = Math.round(Math.pow(k, 3) * 1e10);
        const s = val.toLocaleString('en-US');
        const parts = s.length >= 14 ? [{ t: s.slice(0, 2), c: C.signal }, { t: s.slice(2) }] : [{ t: s }];
        HUD.headline(g, [parts], { y: 400, size: 168, reveal: lt * 2.2 });
        HUD.headline(g, [[{ t: 'HUMANOID ROBOTS' }]], { y: 515, size: 92, reveal: (lt - .5) * 2.2, color: C.soft });
        const p = HUD.project(head, camera);
        if (lt > 1.1) HUD.trackBox(g, p.x, p.y, { s: 84, label: ['UNIT 0000000001', `x. ${Math.round(4197 + lt * 13)}  y. 1693`], alpha: Math.min(1, (lt - 1.1) * 4) });
        HUD.mono(g, 'STATUS: ACTIVE', 64, 1420, { size: 19, color: C.muted, alpha: lt > 1.6 ? 1 : 0 });
      },
    });
  }

  // ---------------- 02 · LIGHT · the army ----------------
  {
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(36);
    lights(scene, { key: 3.0, rim: 1.6, amb: .55, keyPos: [3, 4, 4], rimPos: [-3, 3, -4] });
    const army = new THREE.Group(); scene.add(army);
    const bots = [];
    const cols = 5, rows = 9;
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      const b = makeRobot({ dots: r < 3 }).play('walk');
      b.root.position.set((c - (cols - 1) / 2) * 1.25 + (r % 2) * .3, 0, -r * 1.7);
      b.phase = (r * 0.37 + c * 0.61) % 1.2;
      army.add(b.root); bots.push(b);
    }
    lines.fog = new THREE.Fog(PAL.paper, 6, 34);
    lines.add(gridFloor(PAL.bg, { step: 1.2, opacity: .45 }));
    const heads = [v3(), v3(), v3()];
    const pick = [bots[2], bots[1], bots[8]];
    shots.push({
      name: '02_army', index: '02 / 05  ARCHIVE: FORECAST', mode: 'light', dur: 4.6, scene, lines, camera, mixTone: .32,
      update(lt) {
        for (const b of bots) b.pose(lt + b.phase);
        army.position.z = -2.2 + lt * 1.05;
        const p = ease.inOut(lt / 4.6);
        camera.position.set(.6 - .9 * p, .55 + .35 * p, 5.2);
        camera.lookAt(0, 1.55, -6);
        camera.updateMatrixWorld();
        pick.forEach((b, i) => { b.bonePos('mixamorigHead', heads[i]); heads[i].y += .1; });
      },
      hud(g, lt) {
        HUD.tag(g, 'ON RECORD · E. MUSK · FII RIYADH · 29 OCT 2024', K.W / 2, 300, { size: 20 });
        HUD.headline(g, [[{ t: 'BY ', c: C.bg }, { t: '2040', c: C.signal }]], { y: 520, size: 210, reveal: (lt - .15) * 2, color: C.bg });
        const p0 = HUD.project(heads[0], camera), p1 = HUD.project(heads[1], camera), p2 = HUD.project(heads[2], camera);
        if (lt > .9) HUD.callout(g, p0.x, p0.y, p0.x + 150, p0.y + 40, ['PROJECTED: 10B+', `x. 4197  y. ${1693 + Math.round(lt * 7)}`], { color: C.bg, alpha: Math.min(1, (lt - .9) * 4) });
        if (lt > 1.4) HUD.trackBox(g, p1.x, p1.y, { s: 58, color: C.bg, side: 'left', label: ['UNIT 0002'], alpha: Math.min(1, (lt - 1.4) * 4) });
        if (lt > 1.8) HUD.trackBox(g, p2.x, p2.y, { s: 44, color: C.bg, label: ['UNIT 0007'], alpha: Math.min(1, (lt - 1.8) * 4) });
      },
    });
  }

  // ---------------- 03 · DARK · humans vs robots spheres ----------------
  {
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(34);
    lights(scene, { key: 3.4, rim: 3, amb: .15 });
    const sA = wireSphere(.62, PAL.paper, { opacity: .55 }); sA.position.set(-.78, .95, .4);
    const sB = wireSphere(.95, PAL.signal, { opacity: .85 }); sB.position.set(.62, 1.2, -.3);
    lines.add(sA, sB);
    // humans: point cloud inside sphere A
    const pts = []; let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    while (pts.length < 2400 * 3) { const x = rnd() * 2 - 1, y = rnd() * 2 - 1, z = rnd() * 2 - 1; if (x * x + y * y + z * z < 1) pts.push(x * .56, y * .56, z * .56); }
    const pg = new THREE.BufferGeometry(); pg.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
    const cloud = new THREE.Points(pg, new THREE.PointsMaterial({ color: PAL.paper, size: 2.2, sizeAttenuation: false, transparent: true, opacity: .7 }));
    cloud.position.copy(sA.position); lines.add(cloud);
    const bot = makeRobot().play('idle'); bot.root.scale.setScalar(.9); bot.root.position.set(.62, .5, -.3); scene.add(bot.root);
    lines.fog = new THREE.Fog(PAL.bg, 4, 16);
    lines.add(gridFloor(PAL.paper, { step: .8, opacity: .3 }));
    shots.push({
      name: '03_ratio', index: '03 / 05  COMPARISON', mode: 'dark', dur: 4.4, scene, lines, camera, mixTone: .42,
      update(lt) {
        bot.pose(lt + 5);
        sA.rotation.y = lt * .25; sB.rotation.y = -lt * .2; cloud.rotation.y = lt * .3;
        const p = ease.inOut(lt / 4.4), a = -.25 + .35 * p;
        camera.position.set(Math.sin(a) * 8.8 - .1, 1.9, Math.cos(a) * 8.8);
        camera.lookAt(-.1, 1.3, 0); camera.updateMatrixWorld();
      },
      hud(g, lt) {
        HUD.headline(g, [[{ t: 'MORE ROBOTS' }], [{ t: 'THAN PEOPLE' }, { t: '?', c: C.signal }]], { y: 380, size: 150, reveal: (lt - .1) * 1.8 });
        const a = HUD.project(sA.position.clone().add(v3(0, -.85, 0)), camera);
        const b = HUD.project(sB.position.clone().add(v3(0, -1.2, 0)), camera);
        const al = Math.min(1, Math.max(0, (lt - 1) * 3));
        HUD.mono(g, 'HUMANS', a.x, a.y, { size: 24, align: 'center', alpha: al, weight: 600 });
        HUD.mono(g, '≈ 8.2B · UN 2025', a.x, a.y + 32, { size: 18, align: 'center', color: C.muted, alpha: al });
        HUD.mono(g, 'ROBOTS', b.x, b.y, { size: 24, align: 'center', alpha: al, color: C.signal, weight: 600 });
        HUD.mono(g, '10B+ · FORECAST 2040', b.x, b.y + 32, { size: 18, align: 'center', color: C.muted, alpha: al });
      },
    });
  }

  // ---------------- 04 · LIGHT · archive screen + walker ----------------
  {
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(36);
    lights(scene, { key: 3.0, rim: 2, amb: .5 });
    // archive screen (placeholder until real footage is licensed/selected)
    const sc = document.createElement('canvas'); sc.width = 640; sc.height = 400; const sg = sc.getContext('2d');
    const screenTex = new THREE.CanvasTexture(sc); screenTex.colorSpace = THREE.SRGBColorSpace;
    const drawScreen = (lt) => {
      let seed = Math.floor(lt * 12) + 1; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
      const gr = sg.createRadialGradient(320, 200, 20, 320, 200, 380); gr.addColorStop(0, '#d8d3cb'); gr.addColorStop(1, '#3a3632');
      sg.fillStyle = gr; sg.fillRect(0, 0, 640, 400);
      // silhouette at a podium
      sg.fillStyle = '#0c0b0a'; sg.beginPath(); sg.ellipse(320, 150, 52, 64, 0, 0, Math.PI * 2); sg.fill();
      sg.beginPath(); sg.moveTo(200, 400); sg.quadraticCurveTo(210, 225, 320, 222); sg.quadraticCurveTo(430, 225, 440, 400); sg.fill();
      sg.fillStyle = '#2a2724'; sg.fillRect(250, 300, 140, 100);
      for (let i = 0; i < 1600; i++) { sg.fillStyle = `rgba(255,255,255,${rnd() * .18})`; sg.fillRect(rnd() * 640, rnd() * 400, 2, 2); }
      for (let y = 0; y < 400; y += 4) { sg.fillStyle = 'rgba(0,0,0,.18)'; sg.fillRect(0, y, 640, 2); }
      sg.fillStyle = '#e8e3db'; sg.font = '600 18px "IBM Plex Mono"'; sg.fillText('ARCHIVE FOOTAGE · PLACEHOLDER', 20, 34);
      sg.fillText('FII · RIYADH · 2024', 20, 380);
      screenTex.needsUpdate = true;
    };
    const screen = new THREE.Mesh(new THREE.PlaneGeometry(1.92, 1.2), new THREE.MeshBasicMaterial({ map: screenTex, toneMapped: false }));
    const frame = new THREE.Mesh(new THREE.BoxGeometry(2.04, 1.32, .08), new THREE.MeshStandardMaterial({ color: 0x111111, roughness: .6 }));
    frame.position.set(-1.7, 1.45, -4.4); frame.rotation.y = .5; screen.position.set(0, 0, .045); frame.add(screen); scene.add(frame);
    const stand = new THREE.Mesh(new THREE.CylinderGeometry(.03, .03, 1.3), frame.material); stand.scale.y = .6; stand.position.set(-1.7, .4, -4.4); scene.add(stand);
    const bot = makeRobot().play('walk'); scene.add(bot.root);
    lines.fog = new THREE.Fog(PAL.paper, 6, 30);
    lines.add(gridFloor(PAL.bg, { step: 1, opacity: .4 }));
    // orange signal line on the floor
    const wl = []; for (let z = 3; z > -40; z -= .1) wl.push(Math.sin(z * 2.2) * .05 + .02 * Math.sin(z * 9), .002, z);
    const wg = new THREE.BufferGeometry().setFromPoints(wl.reduce((a, _, i) => (i % 3 ? a : a.concat(new THREE.Vector3(wl[i], wl[i + 1], wl[i + 2]))), []));
    const wave = new THREE.Line(wg, new THREE.LineBasicMaterial({ color: PAL.signal })); lines.add(wave);
    const head = v3();
    shots.push({
      name: '04_task', index: '04 / 05  OPEN QUESTION', mode: 'light', dur: 4.6, scene, lines, camera, mixTone: .32,
      update(lt) {
        drawScreen(lt);
        bot.pose(lt);
        bot.root.position.set(0, 0, -4.2 + lt * .95);
        const p = ease.inOut(lt / 4.6);
        camera.position.set(1.2 - .5 * p, 1.1, 4.0 - .3 * p);
        camera.lookAt(-.35, 1.0, -2.5); camera.updateMatrixWorld();
        bot.bonePos('mixamorigHead', head); head.y += .1;
      },
      hud(g, lt) {
        HUD.headline(g, [[{ t: 'WHAT WILL', c: C.bg }], [{ t: 'THEY DO', c: C.bg }, { t: '?', c: C.signal }]], { y: 400, size: 160, reveal: (lt - .1) * 1.8, color: C.bg });
        const p = HUD.project(head, camera);
        if (lt > 1) HUD.trackBox(g, p.x, p.y, { s: 70, color: C.bg, label: ['TASK: ███████', 'ACCESS: PARTIAL'], alpha: Math.min(1, (lt - 1) * 4) });
      },
    });
  }

  // ---------------- 05 · DARK · end anchor ----------------
  {
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(34);
    lines.fog = new THREE.Fog(PAL.bg, 2, 20);
    lines.add(gridFloor(PAL.paper, { step: .8, opacity: .3 }));
    shots.push({
      name: '05_anchor', index: '05 / 05  TRANSMISSION END', mode: 'dark', dur: 2.6, scene, lines, camera,
      update(lt) { camera.position.set(0, 1.2, 4 - lt * .3); camera.lookAt(0, .6, -6); camera.updateMatrixWorld(); },
      hud(g, lt) {
        HUD.mono(g, 'EVERY PREDICTION LEADS TO', K.W / 2, 760, { size: 26, align: 'center', color: C.soft, alpha: Math.min(1, lt * 3), spacing: .22 });
        HUD.headline(g, [[{ t: '2027', c: C.signal }]], { y: 1000, size: 300, reveal: (lt - .2) * 2 });
        HUD.mono(g, 'FOLLOW THE SIGNAL', K.W / 2, 1100, { size: 22, align: 'center', alpha: Math.min(1, Math.max(0, (lt - .9) * 3)), spacing: .22 });
      },
    });
  }

  return shots;
}
