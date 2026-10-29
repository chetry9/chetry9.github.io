gsap.defaults({ease:'power3.out'});
const tl=gsap.timeline({paused:true});const CUES=[];const cue=(t,y)=>CUES.push([+t.toFixed(3),y]);
const show=(id,t)=>tl.set('#'+id,{opacity:1,visibility:'visible'},t);const hide=(id,t)=>tl.set('#'+id,{opacity:0,visibility:'hidden'},t);
const flash=(t,o=.5)=>{tl.fromTo('#flash',{opacity:0},{opacity:o,duration:.04,ease:'none',immediateRender:false},t).to('#flash',{opacity:0,duration:.22},t+.04)};
let rs=5; const rnd=()=>(rs=(rs*16807)%2147483647)/2147483647;
const burst=(t,x,y)=>{for(let i=0;i<30;i++){const a=rnd()*Math.PI*2,d=200+rnd()*520;tl.fromTo('#p'+i,{x:x-540,y:y-900,opacity:1,scale:1+rnd()*1.5},{x:x-540+Math.cos(a)*d,y:y-900+Math.sin(a)*d,opacity:0,duration:.7+rnd()*.4,ease:'expo.out',immediateRender:false},t);}};
const tap=(x,y,t)=>{tl.fromTo('#tap',{left:x,top:y,opacity:.9,scale:.5},{opacity:0,scale:1.6,duration:.45,immediateRender:false},t);cue(t,'tap');};
const head=(html,t)=>{tl.to('#hl',{opacity:0,y:-30,filter:'blur(12px)',duration:.15,ease:'power2.in'},t-.15);tl.set('#hlt',{innerHTML:html},t);tl.fromTo('#hl',{opacity:0,y:40,scale:1.3,filter:'blur(14px)'},{opacity:1,y:0,scale:1,filter:'blur(0px)',duration:.25,ease:'expo.out',immediateRender:false},t);cue(t,'hit');};
const callIn=(id,t,from)=>{tl.fromTo(id,{opacity:0,x:from,scale:.7},{opacity:1,x:0,scale:1,duration:.35,ease:'back.out(2)'},t);cue(t,'pop');};
const callOut=(id,t)=>tl.to(id,{opacity:0,scale:.8,duration:.2},t);
tl.set('.call',{opacity:0},0); tl.set('#END',{opacity:0,visibility:'hidden'},0);

/* 0-2.6 hook: phone flies in, hero */
cue(0,'boom'); cue(.1,'vo:0');
tl.fromTo('#ph',{y:160,rotateX:22,rotateY:-12,scale:.86,transformPerspective:2400},{y:0,rotateX:6,rotateY:-8,scale:1,duration:.8,ease:'expo.out'},0); cue(0,'swoosh');
tl.fromTo('#hl',{opacity:1,scale:1.05,filter:'blur(3px)'},{opacity:1,scale:1,filter:'blur(0px)',duration:.4,ease:'expo.out'},0);
const ex=['Web Hosting','AI Tools','VPN & Security']; [0,1,2].forEach(i=>tl.set('#expl',{textContent:ex[i]},.6+i*.6));
const st={a:0,c:0}; tl.to(st,{a:100,c:50,duration:1.2,ease:'power2.out',onUpdate:()=>{st1.textContent=Math.round(st.a);st3.textContent=Math.round(st.c)}},.7); cue(.7,'count');
tl.to('#ph',{rotateY:4,rotateX:3,duration:2,ease:'sine.inOut'},.8);

/* 2.6-6.2 : 100+ tools, scroll to categories */
head('<span class="or">100+</span> TOOLS REVIEWED',2.65);
callIn('#k0',2.9,-200);
tap(300,640,3.5); tl.to('#bat',{scale:.94,duration:.08,yoyo:true,repeat:1},3.5);
tl.to('#pg1',{y:-560,duration:.9,ease:'power3.inOut'},3.7); cue(3.7,'scroll');
callIn('#k1',4.3,200);
tl.fromTo('#pg1 .cc',{opacity:0,y:30},{opacity:1,y:0,duration:.25,stagger:.05,immediateRender:false},4.2);
tl.to('#pg1',{y:-760,duration:1.2,ease:'power1.inOut'},4.8);
tl.to('#ph',{rotateY:-6,duration:2,ease:'sine.inOut'},3.8);
callOut('#k0',5.8); callOut('#k1',5.85);

/* 6.2-10.2 : top 5 ranking */
tl.to('#ph',{scale:.9,rotateY:-25,x:-120,filter:'blur(6px)',duration:.18,ease:'power3.in'},6.0); cue(6.0,'whip');
tl.set('#pg1',{opacity:0},6.2); tl.set('#pg3',{opacity:1,y:0},6.2);
tl.to('#ph',{scale:1,rotateY:-6,x:0,filter:'blur(0px)',duration:.35,ease:'expo.out'},6.2);
tl.fromTo('#stk',{x:0,opacity:1},{x:1700,opacity:0,duration:.35,immediateRender:false},6.05);
head('TOP <span class="or">5</span> PER CATEGORY',6.25);
tl.fromTo('#pg3 .rk2',{opacity:0,x:120},{opacity:1,x:0,duration:.3,stagger:.12,immediateRender:false},6.4);
callIn('#k2',6.7,-200);
tl.to('#pg3',{y:-430,duration:1.6,ease:'power2.inOut'},7.6); cue(7.6,'scroll');
tl.fromTo('#pg3 .rk2:first-of-type',{},{},0);
tl.to('#pg3 .rk2 .scb b',{scale:1.25,duration:.15,yoyo:true,repeat:1,stagger:.25},8.3); cue(8.3,'ding'); cue(8.55,'ding'); cue(8.8,'ding');
callIn('#k3',8.5,200);
tl.to('#ph',{scale:1.06,duration:1.6,ease:'none'},8.4);
callOut('#k2',9.9); callOut('#k3',9.95);

/* 10.2-12.6 : reviews page search & filter */
tl.to('#ph',{scale:.9,rotateY:25,x:120,filter:'blur(6px)',duration:.18,ease:'power3.in'},10.0); cue(10.0,'whip');
tl.set('#pg3',{opacity:0},10.2); tl.set('#pg4',{opacity:1},10.2); tl.set('#urlt',{textContent:'bestdigitools.com/reviews/'},10.2);
tl.to('#ph',{scale:1,rotateY:-4,x:0,filter:'blur(0px)',duration:.35,ease:'expo.out'},10.2);
tl.fromTo('#stk',{x:0,opacity:1},{x:1700,opacity:0,duration:.35,immediateRender:false},10.05);
head('SEARCH. FILTER. <span class="or">COMPARE.</span>',10.25);
tl.to('#pg4',{y:-330,duration:.6,ease:'power3.inOut'},10.5); cue(10.5,'scroll');
tl.set('#sph',{textContent:''},11.0); const q={n:0}; tl.to(q,{n:8,duration:.5,ease:'none',onUpdate:()=>{sq2.textContent='AI tools'.slice(0,Math.round(q.n))}},11.0); for(let i=0;i<5;i++)cue(11+i*.1,'key');
tap(110,940,11.5); tl.set('#ch0',{className:'on'},11.55);
tap(130,1010,11.8); tl.to('#apf',{scale:.92,duration:.08,yoyo:true,repeat:1},11.8);
tl.to('#pg4',{y:-560,duration:.5,ease:'power3.inOut'},11.95); tl.fromTo('#res',{opacity:0,y:40},{opacity:1,y:0,duration:.35},12.05); cue(12.05,'ding');
callIn('#k4',11.1,-200); callOut('#k4',12.4);

/* 12.6-15.2 : end card */
tl.to('#ph',{y:-200,scale:.6,opacity:0,filter:'blur(14px)',duration:.35,ease:'power3.in'},12.45); tl.to('#hl',{opacity:0,duration:.2},12.45); cue(12.45,'whoosh');
show('END',12.6); cue(12.6,'impact'); cue(12.7,'vo:4'); cue(12.6,'outro');
tl.fromTo('#lgo',{opacity:0,scale:.4,filter:'blur(24px)'},{opacity:1,scale:1,filter:'blur(0px)',duration:.55,ease:'expo.out'},12.6); burst(12.65,540,620); flash(12.6,.35);
tl.fromTo('#follow',{opacity:0,y:60,scale:.8},{opacity:1,y:0,scale:1,duration:.45,ease:'back.out(1.8)'},13.2); cue(13.2,'pop');
tl.to('#fbtn',{scale:1.08,duration:.3,yoyo:true,repeat:1,ease:'sine.inOut'},13.7);
tl.set('#fbt',{textContent:'✓ Following'},14.4); tl.to('#fbtn',{background:'linear-gradient(180deg,#2bd46b,#16a34a)',duration:.2},14.4); cue(14.4,'fclick');
cue(2.7,'vo:1'); cue(6.3,'vo:2'); cue(10.3,'vo:3');
tl.to('#cam',{scale:1.04,duration:15.2,ease:'none'},0);
const END=15.2; tl.set({}, {}, END);
tl.eventCallback('onUpdate',()=>caption(tl.time()));
window.DURATION=END; window.CUES=CUES.sort((a,b)=>a[0]-b[0]); window.seek=s=>{tl.seek(s,false);caption(s)};
window.ready=document.fonts.ready.then(()=>Promise.all([...document.images].map(i=>i.complete?1:new Promise(r=>{i.onload=i.onerror=r}))));
