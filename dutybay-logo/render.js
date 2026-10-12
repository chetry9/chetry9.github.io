// Renders logo.html frame-by-frame into an MP4 using Playwright + ffmpeg.
// Usage: node render.js <width> <height> <out.mp4|out.webm|out.mov> [fps] [stillTime]
// .webm (VP9) and .mov (ProRes 4444) are rendered with a transparent background.
// A file name containing "_light" uses white text, for placing on dark backgrounds.
// A file name containing "_Icon" renders the icon mark alone, centred.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');

(async () => {
  const [w = 1920, h = 1080, out = 'out.mp4', fps = 60, still] = process.argv.slice(2);
  const W = +w, H = +h, FPS = +fps;
  const alpha = /\.(webm|mov)$/i.test(out);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  await page.goto('file://' + path.join(__dirname, 'logo.html') + `?w=${W}&h=${H}&capture=1${alpha ? '&transparent=1' : ''}${/_light/.test(out) ? '&light=1' : ''}${/_Icon/.test(out) ? '&icon=1' : ''}`);
  await page.waitForFunction(() => window.ready === true);

  if (still !== undefined) {
    await page.evaluate(t => window.renderAt(t), +still);
    await page.screenshot({ path: out, omitBackground: alpha });
    await browser.close();
    return;
  }

  const duration = await page.evaluate(() => window.DURATION);
  const frames = Math.round(duration * FPS);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    ...(/\.webm$/i.test(out)
      ? ['-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', '20', '-row-mt', '1', '-auto-alt-ref', '0']
      : /\.mov$/i.test(out)
        ? ['-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', '-vendor', 'apl0', '-qscale:v', '12']
        : ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', '-preset', 'slow', '-movflags', '+faststart']),
    out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < frames; i++) {
    await page.evaluate(t => window.renderAt(t), i / FPS);
    const buf = await page.screenshot({ type: 'png', omitBackground: alpha });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
})();
