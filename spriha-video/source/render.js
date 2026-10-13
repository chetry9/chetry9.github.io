const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const { spawn } = require('child_process');
(async()=>{
 const FPS=30;
 const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1080,height:1920}});
 await p.goto('http://127.0.0.1:8765/index.html'); await p.evaluate(()=>document.fonts.ready);
 const D=await p.evaluate(()=>DUR); const N=Math.round(D*FPS);
 const ff=spawn('ffmpeg',['-v','error','-y','-f','image2pipe','-framerate',String(FPS),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','medium','-crf','16','-pix_fmt','yuv420p','video_only.mp4'],{stdio:['pipe','inherit','inherit']});
 for(let i=0;i<N;i++){
  await p.evaluate(t=>seek(t),i/FPS);
  const buf=await p.screenshot({type:'jpeg',quality:95});
  if(!ff.stdin.write(buf)) await new Promise(r=>ff.stdin.once('drain',r));
  if(i%150===0) console.log('frame',i,'/',N);
 }
 ff.stdin.end(); await new Promise(r=>ff.on('close',r)); await b.close(); console.log('done');
})();
