// v2 demo: particle assembly/dispersal + footage screens in the 3D space.
export async function buildShots(K) {
  const { THREE, PAL, makeRobot, gridFloor, HUD, ease, FX, footage } = K;
  const { C } = HUD;
  const v3 = (x, y, z) => new THREE.Vector3(x, y, z);
  const ASPECT = K.W / K.H;
  const sm = t => { t = Math.min(Math.max(t, 0), 1); return t * t * (3 - 2 * t); };
  const seg = (lt, a, b) => sm((lt - a) / (b - a));
  const INK_DARK = new THREE.Color(0x090806), INK_LIGHT = new THREE.Color(0xe8e3db); // THREE.Color hex -> linear

  function lights(scene, { key = 3.2, rim = 2.4, amb = .25, keyPos = [2.5, 3, 2.5], rimPos = [-3, 2.5, -3] } = {}) {
    scene.add(new THREE.HemisphereLight(0xffffff, 0x202020, amb));
    const k = new THREE.DirectionalLight(0xffffff, key); k.position.set(...keyPos); scene.add(k);
    const r = new THREE.DirectionalLight(0xffffff, rim); r.position.set(...rimPos); scene.add(r);
  }
  const cam = (fov = 34) => new THREE.PerspectiveCamera(fov, ASPECT, .05, 200);
  // morph origins are sampled once at a fixed moment so any frame can be rendered independently
  const once = (fn) => { let v = null; return () => v ?? (v = fn()); };

  // redaction headline: text revealed by a shrinking bar
  function redacted(g, pre, word, { y, size = 120, p = 1, ink = C.paper, bar = C.paper, accent = C.signal } = {}) {
    g.save(); g.font = `800 ${size}px "Barlow Condensed"`; g.letterSpacing = `${-.015 * size}px`;
    const w1 = g.measureText(pre).width, w2 = g.measureText(word).width, x0 = K.W / 2 - (w1 + w2) / 2;
    g.fillStyle = ink; g.fillText(pre, x0, y);
    g.fillStyle = accent; g.fillText(word, x0 + w1, y);
    const cover = 1 - ease.out(p);
    if (cover > 0) { g.fillStyle = bar; g.fillRect(x0 + w1 + w2 * (1 - cover) - 4, y - size * .78, w2 * cover + 10, size * .86); }
    g.restore();
  }

  const shots = [];

  // ---------- D1 · LIGHT · robot assembles -> disperses -> babysitting footage assembles ----------
  {
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(34);
    lights(scene, { key: 3.0, rim: 1.8, amb: .55, keyPos: [3, 4, 4] });
    const bot = makeRobot().play('idle'); scene.add(bot.root);
    const samp = new FX.RobotSampler(bot, 9000, 11);
    const screen = new FX.Screen(footage.babysit_sofa, { height: 1.3, mode: 'light', contrast: 1.3, bright: .02 });
    screen.group.position.set(.05, 1.05, -.2); screen.group.rotation.y = -.12; lines.add(screen.group);
    const swA = new FX.Swarm(9000, { color: INK_DARK, size: 2.6, seed: 5 }).scatter(v3(0, 1.1, 0), 2.2, 5.5);
    const swB = new FX.Swarm(screen.count, { color: INK_DARK, size: 2.8, seed: 9 });
    lines.add(swA.points, swB.points);
    lines.fog = new THREE.Fog(PAL.paper, 5, 26);
    lines.add(gridFloor(PAL.bg, { step: .9, opacity: .4 }));
    const T_DIS = 3.7;
    const robotAtDis = once(() => { bot.pose(T_DIS + 2); return samp.sample().slice(); });
    const head = v3();
    shots.push({
      name: 'd1_babysit', mode: 'light', dur: 7.2, scene, lines, camera, mixTone: .32,
      timeline: lt => .52 + lt * .004,
      update(lt, t) {
        // robot
        bot.pose(lt + 2);
        const rev = seg(lt, 1.25, 2.05) * (1 - seg(lt, T_DIS, T_DIS + .45));
        bot.reveal(rev);
        const tgt = samp.sample();
        swA.update(tgt, seg(lt, 0, 1.9) * 1.0, 0, t, { fade: 1 - seg(lt, 1.9, 2.4) });
        swA.points.visible = lt < 2.5;
        // morph robot -> screen
        const showB = lt > T_DIS - .05;
        swB.points.visible = showB && lt < 6;
        screen.setTime(Math.max(0, lt - 5.0), t);
        if (showB) {
          swB.originsFrom(robotAtDis());
          screen.sampleTargets(); swB.setColors(screen.colors, .35);
          swB.update(screen.targets, seg(lt, T_DIS, T_DIS + 1.5), 0, t, { swirl: .3, fade: 1 - seg(lt, 5.2, 5.8) });
        }
        screen.reveal(seg(lt, 4.7, 5.35));
        bot.root.visible = rev > .001;
        // camera: slow push + drift
        const p = ease.inOut(lt / 7.2);
        camera.position.set(.9 - .7 * p, 1.3, 4.6 - .6 * p);
        camera.lookAt(0, 1.15, 0); camera.updateMatrixWorld();
        bot.bonePos('mixamorigHead', head); head.y += .1;
      },
      hud(g, lt) {
        if (lt < T_DIS + .3) {
          HUD.headline(g, [[{ t: 'WHAT WILL', c: C.bg }], [{ t: 'THEY DO', c: C.bg }, { t: '?', c: C.signal }]], { y: 360, size: 150, reveal: (lt - 1.2) * 1.8, color: C.bg });
          const p = HUD.project(head, camera);
          if (lt > 2.1 && lt < T_DIS) HUD.trackBox(g, p.x, p.y, { s: 64, color: C.bg, label: ['UNIT 0001', 'TASK: PENDING'], alpha: Math.min(1, (lt - 2.1) * 4) });
        } else if (lt > 5.0) {
          redacted(g, 'TASK: ', 'BABYSITTING', { y: 380, size: 120, p: (lt - 5.15) * 1.6, ink: C.bg, bar: C.bg });
          const c = HUD.project(screen.corner(1, -1), camera);
          HUD.mono(g, 'REC · 00:00:0' + Math.floor(lt - 5), c.x, c.y + 34, { size: 17, align: 'right', color: '#5d5852', alpha: seg(lt, 5.3, 5.6) });
        }
      },
    });
  }

  // ---------- D2 · DARK · archive clip assembles in the void, plays, disperses ----------
  {
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(34);
    const screen = new FX.Screen(footage.musk_placeholder, { height: .82, mode: 'dark', contrast: 1.2 });
    screen.group.position.set(0, 1.55, 0); screen.group.rotation.y = .22; lines.add(screen.group);
    const sw = new FX.Swarm(screen.count, { color: INK_LIGHT, size: 3.2, seed: 21 }).scatter(v3(0, 1.5, 0), 2, 6, .8);
    lines.add(sw.points);
    lines.fog = new THREE.Fog(PAL.bg, 3, 18);
    lines.add(gridFloor(PAL.paper, { step: .8, opacity: .3 }));
    shots.push({
      name: 'd2_archive', mode: 'dark', dur: 5.8, scene, lines, camera, mixTone: .4,
      timeline: lt => .3 + seg(lt, 0, 5.8) * .7,
      update(lt, t) {
        screen.setTime(Math.max(0, lt - 1.5), t);
        screen.sampleTargets(); sw.setColors(screen.colors, .75);
        const d = seg(lt, 4.5, 5.8);
        sw.update(screen.targets, seg(lt, 0, 1.6), d, t, { fade: 1 - seg(lt, 1.7, 2.2) + seg(lt, 4.45, 4.6) });
        screen.reveal(seg(lt, 1.1, 1.75) * (1 - seg(lt, 4.45, 4.9)));
        const p = ease.inOut(lt / 5.8);
        camera.position.set(-.5 + .9 * p, 1.6, 4.9 - .5 * p);
        camera.lookAt(0, 1.45, 0); camera.updateMatrixWorld();
      },
      hud(g, lt) {
        HUD.headline(g, [[{ t: 'BY ' }, { t: '2040', c: C.signal }]], { y: 420, size: 200, reveal: (lt - .3) * 1.8 });
        const c = HUD.project(screen.corner(-1, -1), camera);
        const a = seg(lt, 1.8, 2.1) * (1 - seg(lt, 4.4, 4.6));
        HUD.mono(g, 'FII8 · RIYADH · 29.10.2024', c.x, c.y + 38, { size: 18, color: C.soft, alpha: a });
      },
    });
  }

  // ---------- D3 · LIGHT · price ----------
  {
    const scene = new THREE.Scene(), lines = new THREE.Scene(), camera = cam(32);
    lights(scene, { key: 3.0, rim: 1.8, amb: .55, keyPos: [3, 4, 4] });
    const bot = makeRobot().play('idle'); scene.add(bot.root);
    const samp = new FX.RobotSampler(bot, 9000, 17);
    const sw = new FX.Swarm(9000, { color: INK_DARK, size: 2.6, seed: 33 }).scatter(v3(0, 1.1, 0), 2.2, 5.5);
    lines.add(sw.points);
    lines.fog = new THREE.Fog(PAL.paper, 5, 26);
    lines.add(gridFloor(PAL.bg, { step: .9, opacity: .4 }));
    const hand = v3(), head = v3();
    shots.push({
      name: 'd3_price', mode: 'light', dur: 5.6, scene, lines, camera, mixTone: .32,
      timeline: lt => .55,
      update(lt, t) {
        bot.pose(lt + 6);
        const rev = seg(lt, .9, 1.6) * (1 - seg(lt, 4.5, 4.9));
        bot.reveal(rev);
        const tgt = samp.sample();
        sw.update(tgt, seg(lt, 0, 1.5), seg(lt, 4.5, 5.6), t, { fade: 1 - seg(lt, 1.5, 1.9) + seg(lt, 4.45, 4.55) });
        const p = ease.inOut(lt / 5.6);
        camera.position.set(-.6 + .4 * p, 1.35, 4.9 - .5 * p);
        camera.lookAt(0, 1.32, 0); camera.updateMatrixWorld();
        bot.bonePos('mixamorigRightHand', hand); bot.bonePos('mixamorigHead', head);
      },
      hud(g, lt) {
        HUD.headline(g, [[{ t: 'ONE ROBOT THAT COULD REPLACE YOU', c: '#5d5852' }]], { y: 300, size: 58, reveal: (lt - .9) * 2, color: C.bg });
        HUD.headline(g, [[{ t: 'FROM ', c: C.bg }, { t: '$20,000', c: C.signal }]], { y: 460, size: 170, reveal: (lt - 1.6) * 2, color: C.bg });
        // price tag hanging from the wrist
        const a = seg(lt, 1.8, 2.2) * (1 - seg(lt, 4.4, 4.6));
        if (a > 0) {
          const h = HUD.project(hand, camera), sway = Math.sin(lt * 2.1) * 10;
          const tx = h.x - 120 + sway, ty = h.y + 120;
          g.save(); g.globalAlpha = a; g.strokeStyle = C.bg; g.lineWidth = 2;
          g.beginPath(); g.moveTo(h.x, h.y); g.lineTo(tx + 60, ty - 24); g.stroke();
          g.translate(tx + 60, ty + 10); g.rotate(-.12 + Math.sin(lt * 2.1) * .04);
          g.fillStyle = C.signal; g.beginPath(); g.moveTo(-60, -34); g.lineTo(44, -34); g.lineTo(66, 0); g.lineTo(44, 34); g.lineTo(-60, 34); g.closePath(); g.fill();
          g.fillStyle = C.bg; g.beginPath(); g.arc(46, 0, 6, 0, Math.PI * 2); g.fill();
          g.font = '800 44px "Barlow Condensed"'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('$20K', -8, 2);
          g.restore();
        }
      },
    });
  }
  return shots;
}
