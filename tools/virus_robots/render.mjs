// Usage:
//   node render.mjs stills <outDir> 1.5,6,10.2,...   -> PNG stills at given times
//   node render.mjs video  <out.mp4> [fps=30] [from] [to]
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.ttf': 'font/ttf', '.glb': 'model/gltf-binary', '.png': 'image/png', '.json': 'application/json' };

function serve() {
  return new Promise(res => {
    const srv = http.createServer((req, rsp) => {
      const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { rsp.writeHead(404); return rsp.end(); }
      rsp.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' });
      fs.createReadStream(p).pipe(rsp);
    });
    srv.listen(0, '127.0.0.1', () => res(srv));
  });
}

const [mode, out, a3, a4, a5] = process.argv.slice(2);
const srv = await serve();
const port = srv.address().port;
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--use-gl=angle'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => console.log('[pageerror]', e.message));
await page.goto(`http://127.0.0.1:${port}/web/index.html?seq=${process.env.SEQ || 'v2demo'}`);
await page.waitForFunction(() => window.__ready !== undefined);
await page.evaluate(() => window.__ready);
const DUR = await page.evaluate(() => window.DURATION);
console.log('duration', DUR, JSON.stringify(await page.evaluate(() => window.SHOTS)));

async function frame(t) {
  await page.evaluate(t => window.renderAt(t), t);
  const b64 = await page.evaluate(() => document.getElementById('out').toDataURL('image/png').split(',')[1]);
  return Buffer.from(b64, 'base64');
}

if (mode === 'events') {
  fs.writeFileSync(out, JSON.stringify(await page.evaluate(() => window.EVENTS), null, 1)); console.log('wrote', out);
} else if (mode === 'stills') {
  fs.mkdirSync(out, { recursive: true });
  for (const t of a3.split(',').map(Number)) {
    const f = path.join(out, `still_${t.toFixed(2).replace('.', '_')}s.png`);
    fs.writeFileSync(f, await frame(t)); console.log('wrote', f);
  }
} else if (mode === 'video') {
  const fps = Number(a3 || 30), from = Number(a4 || 0), to = Number(a5 || DUR);
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', '-preset', 'medium', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round((to - from) * fps); const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    const buf = await frame(from + i / fps);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 30 === 0) console.log(`frame ${i}/${n}  ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log('wrote', out);
}
await browser.close(); srv.close();
