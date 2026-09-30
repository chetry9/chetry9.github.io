// Frame-accurate renderer: drives window.renderAt(t) in headless Chromium and pipes frames to ffmpeg.
// usage:
//   node render.mjs shots <t1,t2,...> <outdir>            -> PNG stills
//   node render.mjs video <fps> <from> <to> <out.mp4>     -> lossless-ish chunk
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const REC = process.env.REC_DIR;
const FFMPEG = process.env.FFMPEG || 'ffmpeg';
const [mode, ...args] = process.argv.slice(2);

const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--disable-web-security', '--force-color-profile=srgb', '--hide-scrollbars'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('PAGE ERROR', e.message));
await page.goto(pathToFileURL(path.join(here, 'index.html')).href + '?rec=' + encodeURIComponent(pathToFileURL(REC).href));
await page.evaluate(() => window.ready);
const duration = await page.evaluate(() => window.DURATION);

if (mode === 'info') {
  console.log(JSON.stringify(await page.evaluate(() => ({ d: window.DURATION, ...window.TIMELINE })), null, 1));
} else if (mode === 'shots') {
  const [list, out] = args; mkdirSync(out, { recursive: true });
  for (const t of list.split(',').map(Number)) {
    await page.evaluate(t => window.renderAt(t), t);
    await page.screenshot({ path: path.join(out, `t${t.toFixed(2).padStart(6, '0')}.png`) });
  }
} else if (mode === 'video') {
  const fps = +args[0], from = +args[1], to = Math.min(+args[2], duration), out = args[3];
  const n0 = Math.round(from * fps), n1 = Math.round(to * fps);
  const ff = spawn(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '8', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const cdp = await page.context().newCDPSession(page);
  const t0 = Date.now();
  for (let n = n0; n < n1; n++) {
    await page.evaluate(t => window.renderAt(t), n / fps);
    const { data } = await cdp.send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true });
    const buf = Buffer.from(data, 'base64');
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((n - n0) % 120 === 0) console.error(`[${out}] ${n - n0}/${n1 - n0} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
}
await browser.close();
