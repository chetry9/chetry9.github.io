const { chromium } = require('/opt/node22/lib/node_modules/playwright');
(async()=>{
 const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1080,height:1920}});
 const errs=[]; p.on('pageerror',e=>errs.push(e.message)); p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
 await p.goto('http://127.0.0.1:8765/index.html'); await p.evaluate(()=>document.fonts.ready);
 const ts=process.argv.slice(2).map(Number);
 for(const t of ts){await p.evaluate(t=>seek(t),t); await p.screenshot({path:`prev/f_${t.toFixed(2)}.jpg`,type:'jpeg',quality:70});}
 console.log(errs.join('\n')); await b.close();
})();
