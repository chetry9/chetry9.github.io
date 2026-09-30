const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const fs=require('fs');
(async()=>{
 const mode=process.argv[2];
 const b=await chromium.launch();
 const p=await b.newPage({viewport:{width:1080,height:1920}});
 await p.goto('file://'+__dirname+'/index.html');
 await p.evaluate(()=>document.fonts.ready);
 await p.waitForTimeout(800);
 const fonts=await p.evaluate(()=>[...document.fonts].filter(f=>f.status=='loaded').map(f=>f.family+f.weight).join(','));
 console.log('loaded:',fonts);
 if(mode==='test'){
  for(const t of process.argv.slice(3).map(Number)){
   await p.evaluate(t=>render(t),t);
   await p.screenshot({path:`test_${t}.jpg`,type:'jpeg',quality:80});
  }
 }else{
  fs.mkdirSync('frames',{recursive:true});
  const N=15*30;
  for(let i=0;i<N;i++){await p.evaluate(t=>render(t),i/30);
   await p.screenshot({path:`frames/f${String(i).padStart(4,'0')}.png`});}
 }
 await b.close();
})();
