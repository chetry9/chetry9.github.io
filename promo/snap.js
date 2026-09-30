const {chromium}=require('playwright-core');
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
 const p=await b.newPage({viewport:{width:1920,height:1080}});
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('http://127.0.0.1:8765/'+(process.argv[2]||'part1.html'));
 await p.evaluate(()=>window.ready);
 console.log('dur',await p.evaluate(()=>window.DURATION));
 for(const t of process.argv.slice(3).map(Number)){await p.evaluate(t=>seek(t),t);await p.screenshot({path:`snap_${t}.jpg`,type:'jpeg',quality:70});}
 await b.close();})();
