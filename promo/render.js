const {chromium}=require('playwright-core');const {spawn}=require('child_process');const fs=require('fs');
const [page,out,FF]=process.argv.slice(2);const FPS=30;
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
 const p=await b.newPage({viewport:{width:1920,height:1080}});
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('http://127.0.0.1:8765/'+page);await p.evaluate(()=>window.ready);
 const dur=await p.evaluate(()=>window.DURATION);fs.writeFileSync(out+'.cues.json',JSON.stringify({dur,cues:await p.evaluate(()=>window.CUES)}));
 const ff=spawn(FF,['-v','error','-y','-f','image2pipe','-framerate',''+FPS,'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p',out+'.video.mp4'],{stdio:['pipe','inherit','inherit']});
 const N=Math.ceil(dur*FPS);
 for(let i=0;i<N;i++){await p.evaluate(t=>seek(t),i/FPS);const buf=await p.screenshot({type:'jpeg',quality:95});if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));if(i%150==0)console.log('frame',i,'/',N);}
 ff.stdin.end();await new Promise(r=>ff.on('close',r));await b.close();console.log('done');
})();
