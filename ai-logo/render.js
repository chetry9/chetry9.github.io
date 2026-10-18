// Renders logo.html frame-by-frame with Playwright + ffmpeg.
// Usage: node render.js <variant 1|2|3> <size> <out.mov|out.webm|out.mp4|out.png> [fps] [stillTime]
// .mov (ProRes 4444) and .webm (VP9) keep the transparent background; .mp4 is rendered on a dark backdrop.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');

(async () => {
  const [v = 1, size = 1080, out = 'out.mov', fps = 30, still] = process.argv.slice(2);
  const S = +size, FPS = +fps;
  const alpha = !/\.mp4$/i.test(out);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: S, height: S } });
  await page.goto('file://' + path.join(__dirname, 'logo.html') + `?v=${v}&w=${S}&h=${S}&capture=1${process.env.FIT ? '&fit=' + process.env.FIT : ''}${alpha ? '&transparent=1' : ''}`);
  await page.waitForFunction(() => window.ready === true);
  const shot = () => page.screenshot({ type: 'png', omitBackground: alpha });

  if (still !== undefined) {
    await page.evaluate(t => window.renderAt(t), +still);
    require('fs').writeFileSync(out, await shot());
    return browser.close();
  }

  const frames = Math.round(await page.evaluate(() => window.DURATION) * FPS);
  const codec = /\.webm$/i.test(out)
    ? ['-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', '22', '-row-mt', '1', '-auto-alt-ref', '0']
    : /\.mov$/i.test(out)
      ? ['-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', '-vendor', 'apl0', '-qscale:v', '13']
      : ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '17', '-preset', 'slow', '-movflags', '+faststart'];
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-', ...codec, out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < frames; i++) {
    await page.evaluate(t => window.renderAt(t), i / FPS);
    const buf = await shot();
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
})();
