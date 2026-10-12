const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const mode = process.argv[2];
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files','--disable-web-security'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.resolve('index.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(async()=>{for(const f of ['800 40px Anek Bangla','700 40px Anek Bangla','600 40px Hind Siliguri','700 40px Hind Siliguri','800 40px Poppins','600 40px Poppins'])await document.fonts.load(f,'অআ Aa1');}); await page.waitForTimeout(500);
  if (mode === 'stills') {
    const ts = process.argv.slice(3).map(Number);
    for (const t of ts) { await page.evaluate(t => render(t), t); await page.screenshot({ path: `stills/s_${t}.jpg`, type: 'jpeg', quality: 80 }); }
  } else {
    const fps = 30, dur = +process.argv[3], start = +(process.argv[4]||0), end = +(process.argv[5]||dur);
    const out = process.argv[6] || 'frames.mp4';
    const ff = spawn('ffmpeg', ['-y','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p',out], { stdio: ['pipe','ignore','inherit'] });
    for (let f = Math.round(start*fps); f < Math.round(end*fps); f++) {
      await page.evaluate(t => render(t), f / fps);
      const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (f % 150 === 0) console.error('frame', f);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
