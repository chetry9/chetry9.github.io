// Renders logo.html frame-by-frame into an MP4 using Playwright + ffmpeg.
// Usage: node render.js <width> <height> <out.mp4> [fps] [stillTime]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');

(async () => {
  const [w = 1920, h = 1080, out = 'out.mp4', fps = 60, still] = process.argv.slice(2);
  const W = +w, H = +h, FPS = +fps;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  await page.goto('file://' + path.join(__dirname, 'logo.html') + `?w=${W}&h=${H}&capture=1`);
  await page.waitForFunction(() => window.ready === true);

  if (still !== undefined) {
    await page.evaluate(t => window.renderAt(t), +still);
    await page.screenshot({ path: out });
    await browser.close();
    return;
  }

  const duration = await page.evaluate(() => window.DURATION);
  const frames = Math.round(duration * FPS);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', '-preset', 'slow', '-movflags', '+faststart', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < frames; i++) {
    await page.evaluate(t => window.renderAt(t), i / FPS);
    const buf = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
})();
