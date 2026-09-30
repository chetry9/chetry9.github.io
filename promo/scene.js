/* Upscore Tech service promo — deterministic scene.
 * Every visual is a pure function of time: window.renderAt(t) paints the frame for t seconds.
 * Rec frames are the phone screen recording, pre-extracted at 60fps (status bar cropped). */
(() => {
const Q = new URLSearchParams(location.search);
const REC_DIR = Q.get('rec') || '../rec';
const REC_FPS = 60, REC_LAST = 4378;

/* ---------------- math ---------------- */
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, k) => a + (b - a) * k;
const prog = (t, a, b) => clamp((t - a) / (b - a));
const eOutCubic = k => 1 - Math.pow(1 - k, 3);
const eInCubic = k => k * k * k;
const eInOutCubic = k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
const eOutExpo = k => k >= 1 ? 1 : 1 - Math.pow(2, -10 * k);
const eOutQuint = k => 1 - Math.pow(1 - k, 5);
const eOutBack = k => { const c1 = 1.5, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); };
// trapezoid velocity profile: accelerate over `a` of the span, cruise, decelerate over `a`
const trap = (u, a = .22) => {
  const v = 1 / (1 - a);
  if (u < a) return v * u * u / (2 * a);
  if (u > 1 - a) return 1 - v * (1 - u) * (1 - u) / (2 * a);
  return v * (a / 2 + (u - a));
};
const $ = id => document.getElementById(id);

function fx(el, o, blur = 0, tx = 0, ty = 0, sc = 1, extra = '') {
  el.style.opacity = o;
  el.style.visibility = o <= 0.001 ? 'hidden' : 'visible';
  el.style.filter = blur > 0.05 ? `blur(${blur.toFixed(2)}px)` : 'none';
  el.style.transform = `translate(${tx.toFixed(2)}px,${ty.toFixed(2)}px) scale(${sc.toFixed(4)}) ${extra}`;
}
// blur-rise reveal (reference style): in at `s`, out at `e`
function reveal(el, t, s, e, o = {}) {
  const d = o.d ?? .9, dy = o.dy ?? 34, bl = o.blur ?? 18, od = o.od ?? .55, ody = o.ody ?? -26;
  const pin = eOutCubic(prog(t, s, s + d));
  const pout = e == null ? 0 : eInCubic(prog(t, e, e + od));
  const op = pin * (1 - pout);
  fx(el, op, bl * (1 - pin) + bl * .8 * pout, (o.dx ?? 0) * (1 - pin), dy * (1 - pin) + ody * pout, lerp(o.s0 ?? 1, 1, pin) * lerp(1, o.s1 ?? 1, pout));
  return op;
}
// split "text with *accent* words" into spans; returns array of word spans
function words(container, text, cls = '') {
  container.innerHTML = '';
  const out = [];
  text.split(/(\*[^*]+\*)/).forEach(part => {
    if (!part) return;
    const acc = part.startsWith('*') && part.endsWith('*');
    part.replace(/\*/g, '').split(/(\s+)/).forEach(tok => {
      if (!tok) return;
      if (/^\s+$/.test(tok)) { container.appendChild(document.createTextNode(' ')); return; }
      const sp = document.createElement('span');
      sp.className = 'w ' + cls + (acc ? ' serif gtxt' : '');
      sp.textContent = tok;
      container.appendChild(sp); out.push(sp);
    });
  });
  return out;
}
function staggerWords(ws, t, s, e, st = .075, o = {}) {
  ws.forEach((w, i) => reveal(w, t, s + i * st, e == null ? null : e + i * (o.ost ?? .035), o));
}

/* ---------------- timeline ---------------- */
const CFG = window.PROMO_CFG || {};
const PD = CFG.pd || [10, 10, 10, 10];   // seconds each service is presented (fitted to the voice-over)
const T = {
  hookIn: .35, hookOut: 3.5,
  phoneIn: 4.15, phoneInEnd: 5.65,
  type0: 5.85, dtc: .066,
  enter: 8.85, res: 9.2, glow: 9.95, tap: 10.65, toRec: 10.95,
};
// rec segments: global t -> recording time r
const SEG = [];
let tc = T.toRec;
const seg = (dur, r0, r1, ease = 'lin', cut = false) => { SEG.push({ t0: tc, t1: tc + dur, r0, r1, ease, cut }); tc += dur; };
const P = [];
const present = (r, i) => { const d = PD[i]; P.push({ t0: tc, t1: tc + d, r, i }); SEG.push({ t0: tc, t1: tc + d, r0: r, r1: r, ease: 'lin' }); tc += d; };
seg(5.8, 3.0, 8.8);                     // splash + hero
seg(11 / 1.4, 14.0, 25.0, 'lin', true); // skip the accidental contact-page detour
seg(1.0, 25.0, 25.8, 'out');
present(25.8, 0);
seg(5.4, 25.8, 32.4, 'trap');
present(32.4, 1);
seg(1.2, 32.4, 33.3, 'trap');
present(33.3, 2);
seg(1.8, 33.3, 35.2, 'trap');
present(35.2, 3);
seg(5.0, 35.2, 41.5, 'trap');
seg(3.2, 67.4, 70.6, 'out', true);      // CTA block
const REC_END = tc;
const OUT = { t0: REC_END - .55 };
OUT.end = OUT.t0 + (CFG.outroLen || 7.2);
const DURATION = OUT.end;
T.A0 = SEG[0].t0; T.B0 = SEG[1].t0;

function recAt(t) {
  let s = SEG[0];
  for (const x of SEG) { if (t >= x.t0) s = x; }
  const u = clamp((t - s.t0) / (s.t1 - s.t0));
  const k = s.ease === 'out' ? 1 - Math.pow(1 - u, 2) : s.ease === 'trap' ? trap(u) : u;
  return { r: lerp(s.r0, s.r1, k), seg: s };
}
const frameOf = r => clamp(Math.round(r * REC_FPS) + 1, 1, REC_LAST);
const srcOf = n => `${REC_DIR}/${String(n).padStart(5, '0')}.jpg`;

/* ---------------- services ---------------- */
const SV = [
  { n: '01', short: 'Web & App', title: ['Web & App', '*Development*'],
    def: 'Fast, secure, <b>conversion-focused</b> websites and web apps — custom-built to rank on Google and turn visitors into customers.',
    box: [23.3, 276.2, 402.7, 612.1],
    items: ['Custom Website Design & Development', 'Web Application Development', 'SaaS Development', 'WordPress Development', 'Shopify Website Design', 'Wix Development', 'Squarespace Development', 'Webflow Development', 'Landing Page Design & Development', 'eCommerce Website Development', 'CMS Development', 'Website Redesign & Optimization'] },
  { n: '02', short: 'Digital Marketing', title: ['Result-Driven', 'Digital *Marketing*'],
    def: 'SEO, paid ads and content built around <b>real buyer intent</b> — more traffic, qualified leads and measurable ROI.',
    box: [23.3, 68.4, 400.6, 407.5],
    items: ['Search Engine Optimization (SEO)', 'Social Media Marketing (SMM)', 'Paid Advertising / PPC', 'Google Ads', 'Meta Ads', 'Email Marketing', 'Conversion Rate Optimization', 'Content Marketing', 'Marketing Analytics & Reporting'] },
  { n: '03', short: 'AI Automation', title: ['AI Automation &', 'Intelligent *Systems*'],
    def: 'AI agents, chatbots and automated workflows that work <b>24/7</b> — so your team spends time on growth, not busywork.',
    box: [22.3, 189.3, 401.6, 528.4],
    items: ['AI Automation', 'AI Agents', 'AI Chatbots', 'Business Process Automation', 'AI-Powered Workflows', 'CRM Automation', 'Lead Generation Automation', 'Customer Support Automation', 'AI Content Automation', 'AI Integration & API Automation', 'Custom AI Solutions'] },
  { n: '04', short: 'Video & Content', title: ['Video Production', '& *Content*'],
    def: 'Scroll-stopping reels, YouTube content, motion graphics and AI video that <b>capture attention</b> and build your brand.',
    box: [23.3, 266.6, 401.6, 629.0],
    items: ['Professional Video Editing', 'AI Video Creation', 'Short-form Video (Reels / Shorts / TikTok)', 'Long-form YouTube Videos', 'Social Media Video Content', 'UGC-style Videos', 'Motion Graphics', 'Explainer Videos', 'AI Avatar Videos', 'Video Ads', 'YouTube Content Production'] },
];

/* ---------------- build DOM ---------------- */
const panel = $('panel'), floats = $('floats');
floats.style.zIndex = 6; $('phoneWrap').style.zIndex = 5; panel.style.zIndex = 6;
SV.forEach((s, i) => {
  const g = document.createElement('div'); g.className = 'abs'; g.style.inset = '0'; panel.appendChild(g); s.g = g;
  g.innerHTML = `<div class="pnum"><span class="n">${s.n} / 04</span><span class="line"></span><span class="kicker">Core Service</span></div>
    <div class="ptitle"><div class="t1"></div><div class="t2"></div></div>
    <div class="pdef">${s.def}</div><div class="chips"></div>`;
  s.num = g.querySelector('.pnum');
  s.w1 = words(g.querySelector('.t1'), s.title[0]);
  s.w2 = words(g.querySelector('.t2'), s.title[1]);
  s.defEl = g.querySelector('.pdef');
  const ch = g.querySelector('.chips');
  // long lists: tighten rows so everything fits
  if (s.items.length > 10) { ch.style.gap = '10px 14px'; }
  s.chips = s.items.map(txt => {
    const c = document.createElement('div'); c.className = 'chip';
    c.innerHTML = `<span class="dot"></span><span>${txt}</span><i class="sheen"></i>`;
    ch.appendChild(c); return c;
  });
  const f = document.createElement('div'); f.className = 'abs'; f.style.inset = '0'; floats.appendChild(f); s.f = f;
});

function FLOATS_web() {
  return `<div class="fc fa" style="left:64px;top:170px;width:330px">
      <div class="h">PageSpeed</div>
      <div style="display:flex;align-items:center;gap:18px;margin-top:14px">
        <svg width="112" height="112" viewBox="0 0 112 112"><circle cx="56" cy="56" r="46" fill="none" stroke="rgba(93,255,158,.14)" stroke-width="9"/>
        <circle class="arc" cx="56" cy="56" r="46" fill="none" stroke="#5dff9e" stroke-width="9" stroke-linecap="round" transform="rotate(-90 56 56)" stroke-dasharray="289" stroke-dashoffset="289"/>
        <text class="num" x="56" y="66" text-anchor="middle" font-family="Inter" font-weight="800" font-size="34" fill="#fff">0</text></svg>
        <div style="font-size:15px;line-height:1.9;color:#c7cdf0"><div>Performance</div><div>SEO-ready</div><div>Mobile-first</div></div>
      </div></div>
    <div class="fc fb" style="left:92px;top:585px;width:360px;padding:0;overflow:hidden">
      <div style="display:flex;gap:7px;padding:14px 16px;border-bottom:1px solid rgba(255,255,255,.07)"><i style="width:11px;height:11px;border-radius:50%;background:#ff5f57"></i><i style="width:11px;height:11px;border-radius:50%;background:#febc2e"></i><i style="width:11px;height:11px;border-radius:50%;background:#28c840"></i><span style="margin-left:10px;font-size:12px;color:#7f89b8;font-family:'JetBrains Mono'">build.js</span></div>
      <div class="code" style="padding:14px 18px 18px"><div class="ln"><span class="c">// launch-ready in weeks</span></div><div class="ln"><span class="k">const</span> site = <span class="t">build</span>({</div><div class="ln">  stack: [<span class="s">'WordPress'</span>, <span class="s">'Shopify'</span>],</div><div class="ln">  design: <span class="s">'custom'</span>,</div><div class="ln">  seo: <span class="k">true</span>, speed: <span class="s">'fast'</span></div><div class="ln">});</div></div></div>`;
}
function FLOATS_mkt() {
  return `<div class="fc fa" style="left:60px;top:160px;width:360px">
      <div class="h">Traffic &amp; Leads</div>
      <div class="big">Growth <span class="gtxt">↗</span></div>
      <svg width="316" height="130" viewBox="0 0 316 130" style="margin-top:8px;overflow:visible">
        <defs><linearGradient id="ag" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7c6bff" stop-opacity=".55"/><stop offset="1" stop-color="#7c6bff" stop-opacity="0"/></linearGradient>
        <linearGradient id="lg" x1="0" x2="1"><stop offset="0" stop-color="#5b8cff"/><stop offset="1" stop-color="#d27dff"/></linearGradient></defs>
        <g stroke="rgba(255,255,255,.06)"><line x1="0" y1="32" x2="316" y2="32"/><line x1="0" y1="72" x2="316" y2="72"/><line x1="0" y1="112" x2="316" y2="112"/></g>
        <path class="area" d="M0 118 C40 112 60 104 90 100 S140 92 170 76 S230 56 260 34 S300 12 316 8 L316 130 L0 130 Z" fill="url(#ag)" opacity="0"/>
        <path class="ln" d="M0 118 C40 112 60 104 90 100 S140 92 170 76 S230 56 260 34 S300 12 316 8" fill="none" stroke="url(#lg)" stroke-width="4" stroke-linecap="round" stroke-dasharray="420" stroke-dashoffset="420"/>
        <circle class="pt" cx="316" cy="8" r="7" fill="#fff" opacity="0"/>
      </svg></div>
    <div class="fc fb" style="left:96px;top:600px;width:340px">
      <div class="h">Funnel</div>
      ${['Impressions', 'Clicks', 'Leads', 'Customers'].map((l, k) => `<div style="margin-top:${k ? 10 : 14}px"><div style="display:flex;justify-content:space-between;font-size:14px;color:#c7cdf0;margin-bottom:6px"><span>${l}</span></div><div style="height:12px;border-radius:6px;background:rgba(255,255,255,.06);overflow:hidden"><i class="fb${k}" style="display:block;height:100%;width:0;border-radius:6px;background:linear-gradient(90deg,#3d6dff,#b07bff)"></i></div></div>`).join('')}
    </div>`;
}
function FLOATS_ai() {
  return `<div class="fc fa" style="left:58px;top:150px;width:372px;height:360px">
      <div class="h">Workflow · live</div>
      <svg width="330" height="290" style="position:absolute;left:22px;top:52px;overflow:visible">
        <path id="wfp" d="M60 30 C60 70 60 60 60 95 M60 125 C60 160 150 150 170 180 M60 125 C60 160 60 160 60 215" fill="none" stroke="rgba(140,150,255,.35)" stroke-width="2" stroke-dasharray="5 6"/>
        <circle class="p1" r="5" fill="#8fb0ff"/><circle class="p2" r="5" fill="#d27dff"/><circle class="p3" r="5" fill="#5dff9e"/>
      </svg>
      <div class="node n0" style="left:22px;top:62px"><i style="background:linear-gradient(135deg,#3d6dff,#46c8ff)"></i>New lead</div>
      <div class="node n1" style="left:22px;top:158px;border-color:rgba(160,120,255,.6);box-shadow:0 0 24px rgba(140,100,255,.35)"><i style="background:linear-gradient(135deg,#8b5cff,#d27dff)"></i>AI Agent</div>
      <div class="node n2" style="left:170px;top:236px"><i style="background:linear-gradient(135deg,#ff9d5c,#ff5c8a)"></i>CRM updated</div>
      <div class="node n3" style="left:22px;top:282px"><i style="background:linear-gradient(135deg,#25d366,#5dff9e)"></i>Reply sent</div>
    </div>
    <div class="fc fb" style="left:96px;top:600px;width:350px">
      <div class="h">AI Assistant</div>
      <div class="bubble u m0">Hi! Can I book a strategy call?</div>
      <div class="bubble b m1" style="display:flex;gap:5px;width:64px;justify-content:center"><i class="td" style="width:7px;height:7px;border-radius:50%;background:#fff;display:block"></i><i class="td" style="width:7px;height:7px;border-radius:50%;background:#fff;display:block"></i><i class="td" style="width:7px;height:7px;border-radius:50%;background:#fff;display:block"></i></div>
      <div class="bubble b m2">Of course — you're booked for Tuesday, 10:00 ✓</div>
    </div>`;
}
function FLOATS_vid() {
  const clips = (arr) => arr.map(([l, w, c]) => `<i class="clip" style="left:${l}%;width:${w}%;background:${c}"></i>`).join('');
  return `<div class="fc fa" style="left:44px;top:170px;width:400px">
      <div class="h" style="justify-content:space-between"><span style="display:flex;gap:8px;align-items:center">Timeline</span><span class="tcode" style="color:#fff;letter-spacing:.05em">00:00:00</span></div>
      <div style="position:relative;height:130px;margin-top:16px">
        <div class="track" style="top:0">${clips([[0, 26, 'linear-gradient(90deg,#3d6dff,#6b7bff)'], [27, 18, 'linear-gradient(90deg,#8b5cff,#b07bff)'], [46, 30, 'linear-gradient(90deg,#3d6dff,#46c8ff)'], [77, 23, 'linear-gradient(90deg,#d27dff,#ff7eb6)']])}</div>
        <div class="track" style="top:34px">${clips([[10, 14, 'rgba(255,200,90,.85)'], [40, 22, 'rgba(255,200,90,.85)'], [70, 12, 'rgba(255,200,90,.85)']])}</div>
        <div class="track wave" style="top:68px;background:rgba(93,255,158,.08)"></div>
        <div class="track" style="top:102px">${clips([[0, 100, 'rgba(93,255,158,.28)']])}</div>
        <i class="ph" style="position:absolute;top:-8px;bottom:-4px;width:2px;background:#fff;box-shadow:0 0 12px #fff;left:0"></i>
      </div></div>
    <div class="fc fb" style="left:86px;top:560px;width:380px;height:380px;background:none;border:none;box-shadow:none;padding:0">
      ${[0, 1, 2].map(k => `<div class="reel r${k}" style="position:absolute;left:110px;top:10px;width:180px;height:320px;border-radius:22px;overflow:hidden;border:1px solid rgba(255,255,255,.18);box-shadow:0 24px 60px rgba(0,0,0,.6);background:${['linear-gradient(160deg,#3d6dff,#12163a 70%)', 'linear-gradient(160deg,#b07bff,#1a1236 70%)', 'linear-gradient(160deg,#ff7eb6,#2a1030 70%)'][k]}">
        <div style="position:absolute;left:50%;top:44%;width:58px;height:58px;margin:-29px;border-radius:50%;background:rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center"><svg width="22" height="22" viewBox="0 0 24 24"><path d="M7 4v16l13-8z" fill="#fff"/></svg></div>
        <div style="position:absolute;left:14px;bottom:16px;font-size:14px;font-weight:700">${['Reels', 'Shorts', 'TikTok'][k]}</div>
        <div style="position:absolute;left:14px;right:14px;bottom:44px;height:3px;border-radius:2px;background:rgba(255,255,255,.25)"><i class="rp" style="display:block;height:100%;width:0;background:#fff;border-radius:2px"></i></div>
      </div>`).join('')}
    </div>`;
}
var FLOATS = [FLOATS_web, FLOATS_mkt, FLOATS_ai, FLOATS_vid];
// FLOATS is referenced above during build; hoisting via var keeps order simple
SV.forEach((s, i) => { if (!s.f.innerHTML) s.f.innerHTML = FLOATS[i](); });

// hook + captions
const hk1 = words($('hk1'), 'Looking for the *best*');
const hk2 = words($('hk2'), 'digital marketing agency');
const hk3 = words($('hk3'), '*in Padova?*');
$('capA').innerHTML = `<div class="kicker" id="capAk" style="margin-bottom:22px">Meet</div><div id="capA1" style="font-size:118px"></div><div id="capA2l" style="font-size:118px"></div>`;
const capAk = $('capAk'), capA1 = words($('capA1'), 'Upscore'), capA2l = words($('capA2l'), '*Tech.*');
$('capA2').innerHTML = `<div id="capR1" style="font-size:60px"></div><div id="capR2" style="font-size:60px"></div><div class="kicker" id="capR3" style="margin-top:26px;color:#8793c4">Padova · Italy — Worldwide</div>`;
const capR1 = words($('capR1'), 'Full-service'), capR2 = words($('capR2'), 'digital *agency*'), capR3 = $('capR3');
$('capB').innerHTML = `<div id="cb1" style="font-size:66px"></div><div id="cb2" style="font-size:66px"></div><div id="cb3" style="font-size:80px"></div>`;
const cb1 = words($('cb1'), 'Everything your'), cb2 = words($('cb2'), 'brand needs —'), cb3 = words($('cb3'), '*under one roof.*');
const oTag = words($('oTag'), 'Your all-in-one *digital partner.*');

// progress
$('prog').innerHTML = SV.map((s, i) => `<div class="it" id="pi${i}"><span class="d"></span>${s.short}</div>${i < 3 ? `<div class="bar"><i id="pb${i}"></i></div>` : ''}`).join('');

// google suggestions
const QUERY = 'best digital marketing agency in padova';
const SUGG = ['best digital marketing agency in padova', 'best digital marketing agency in italy', 'best digital marketing agency near me', 'best digital marketing courses', 'best digital camera', 'best dishes in padova'];

// grain frames
const grain = $('grain'), gctx = grain.getContext('2d'), GRAIN = [];
for (let k = 0; k < 6; k++) {
  const id = gctx.createImageData(960, 540);
  let seed = 1234 + k * 7919;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  for (let p = 0; p < id.data.length; p += 4) { const v = rnd() * 255; id.data[p] = id.data[p + 1] = id.data[p + 2] = v; id.data[p + 3] = 255; }
  GRAIN.push(id);
}

/* ---------------- rec image layers ---------------- */
const recA = $('recA'), recB = $('recB');
const loaded = new Map();
function setImg(img, n) {
  const s = srcOf(n);
  if (img.dataset.n == n) return Promise.resolve();
  img.dataset.n = n; img.src = s;
  return img.decode().catch(() => {});
}

/* ---------------- render ---------------- */
async function renderAt(t) {
  const waits = [];

  /* background */
  const hookGlow = 1 - prog(t, T.hookOut, T.phoneInEnd) * .45 + prog(t, OUT.t0 + .4, OUT.t0 + 1.6) * .4;
  const b1 = $('b1'), b2 = $('b2'), b3 = $('b3');
  b1.style.cssText = `width:1300px;height:1300px;left:${-260 + 90 * Math.sin(t * .23)}px;top:${-420 + 70 * Math.cos(t * .19)}px;background:radial-gradient(circle,rgba(46,84,255,.42),rgba(46,84,255,.12) 40%,transparent 68%)`;
  b2.style.cssText = `width:1200px;height:1200px;left:${1020 + 80 * Math.cos(t * .21)}px;top:${240 + 90 * Math.sin(t * .17)}px;background:radial-gradient(circle,rgba(139,92,255,.36),rgba(139,92,255,.1) 42%,transparent 68%)`;
  b3.style.cssText = `width:700px;height:700px;left:${760 + 160 * Math.sin(t * .13)}px;top:${620 + 60 * Math.cos(t * .29)}px;background:radial-gradient(circle,rgba(70,200,255,.16),transparent 65%)`;
  const ring = $('ring'), ring2 = $('ring2');
  const ra = t * 38 + 200;
  const rs = lerp(1.18, 1, eOutCubic(prog(t, 0, 3.2))) * (1 + .015 * Math.sin(t * .8));
  const mask = `conic-gradient(from ${ra}deg, transparent 0deg, rgba(0,0,0,.25) 40deg, #000 110deg, #000 150deg, rgba(0,0,0,.25) 230deg, transparent 300deg)`;
  ring.style.webkitMaskImage = mask; ring2.style.webkitMaskImage = mask;
  ring.style.transform = ring2.style.transform = `scale(${rs})`;
  ring.style.opacity = (.85 * hookGlow).toFixed(3); ring2.style.opacity = hookGlow.toFixed(3);
  gctx.putImageData(GRAIN[Math.floor(t * 24) % GRAIN.length], 0, 0);

  /* hook */
  staggerWords(hk1, t, T.hookIn, T.hookOut, .085, { d: 1, dy: 40, blur: 22 });
  staggerWords(hk2, t, T.hookIn + .55, T.hookOut + .12, .085, { d: 1, dy: 40, blur: 22 });
  staggerWords(hk3, t, T.hookIn + 1.0, T.hookOut + .24, .085, { d: 1.1, dy: 40, blur: 22 });

  /* phone transform */
  let k = 0;
  for (const p of P) k = Math.max(k, eInOutCubic(prog(t, p.t0, p.t0 + 1.15)) * (1 - eInOutCubic(prog(t, p.t1 - .95, p.t1))));
  const pin = eOutExpo(prog(t, T.phoneIn, T.phoneInEnd));
  const pout = eInOutCubic(prog(t, OUT.t0, OUT.t0 + 1.0));
  const wob = Math.sin(t * .9) * 5;
  const px = lerp(0, -400, k);
  const py = lerp(900, 0, pin) + wob + pout * 90;
  const ry = lerp(0, 15, k) + Math.sin(t * .5) * 1.2 * (1 - k) + lerp(-14, 0, pin) * (1 - k);
  const rx = lerp(22, 0, pin) + 1.5 * Math.sin(t * .37);
  const ps = .94 * lerp(1, .955, k) * (1 - .1 * pout);
  const phone = $('phone');
  phone.style.transform = `translate(${px.toFixed(2)}px,${py.toFixed(2)}px) rotateY(${ry.toFixed(3)}deg) rotateX(${rx.toFixed(3)}deg) scale(${ps.toFixed(4)})`;
  phone.style.opacity = (pin * (1 - pout)).toFixed(3);
  phone.style.filter = pout > .01 ? `blur(${(pout * 16).toFixed(2)}px)` : 'none';
  phone.style.boxShadow = `0 60px 120px rgba(0,0,0,.65), 0 0 0 1px rgba(255,255,255,.04), ${(-18 * k).toFixed(1)}px 30px 90px rgba(70,90,255,${(.28 + .2 * k).toFixed(3)})`;
  const gu = $('glowUnder');
  gu.style.transform = `translate(${(px * .95).toFixed(1)}px,${py.toFixed(1)}px) scale(${(.95 + .05 * Math.sin(t)).toFixed(3)})`;
  gu.style.opacity = (pin * (1 - pout) * .9).toFixed(3);

  /* screen content: google mock → recording */
  const gm = $('gm');
  const gmo = 1 - eInOutCubic(prog(t, T.toRec, T.toRec + .16));
  gm.style.opacity = gmo; gm.style.visibility = gmo <= 0 ? 'hidden' : 'visible';
  if (gmo > 0) {
    const n = clamp(Math.floor((t - T.type0) / T.dtc), 0, QUERY.length);
    const typed = QUERY.slice(0, n);
    $('qtxt').textContent = typed;
    const typing = t >= T.type0 && t < T.type0 + QUERY.length * T.dtc;
    $('caret').style.opacity = typing || Math.floor(t * 2) % 2 === 0 ? 1 : 0;
    const sg = $('sugg');
    if (n >= 4) {
      const list = SUGG.filter(x => x.startsWith(typed)).slice(0, 4);
      sg.innerHTML = list.map(x => `<div><svg width="18" height="18" viewBox="0 0 24 24"><circle cx="10" cy="10" r="6.5" fill="none" stroke="#9aa0a6" stroke-width="2.2"/><path d="m15 15 5 5" stroke="#9aa0a6" stroke-width="2.2"/></svg><span>${typed}<b>${x.slice(typed.length)}</b></span></div>`).join('');
      sg.style.opacity = list.length ? 1 : 0;
    } else { sg.innerHTML = ''; sg.style.opacity = 0; }
    const ho = 1 - prog(t, T.enter, T.enter + .18);
    $('gHome').style.opacity = ho;
    const ro = prog(t, T.enter + .1, T.enter + .3);
    $('gRes').style.opacity = ro;
    $('urltxt').textContent = t < T.enter ? 'google.com' : 'google.com/search?q=best+digital+marketing…';
    $('loadbar').style.width = (eOutCubic(prog(t, T.enter + .05, T.res + .15)) * 100) + '%';
    $('loadbar').style.opacity = 1 - prog(t, T.res + .15, T.res + .35);
    const r1 = $('r1');
    const rin = eOutCubic(prog(t, T.res, T.res + .55));
    const gl = eOutCubic(prog(t, T.glow, T.glow + .5));
    fx(r1, rin, 0, 0, 40 * (1 - rin), 1 + .025 * gl);
    r1.style.boxShadow = `0 0 0 ${(2.5 * gl).toFixed(2)}px rgba(138,180,248,${gl}), 0 0 ${(50 * gl).toFixed(1)}px rgba(120,140,255,${.55 * gl})`;
    [$('sk1'), $('sk2')].forEach((el, j) => { const q = eOutCubic(prog(t, T.res + .2 + j * .1, T.res + .7 + j * .1)); fx(el, q * (1 - .55 * gl), 0, 0, 30 * (1 - q)); });
    const tp = prog(t, T.tap, T.tap + .5);
    const tap = $('tap');
    tap.style.left = '190px'; tap.style.top = '336px';
    tap.style.opacity = tp > 0 && tp < 1 ? (.55 * (1 - tp)).toFixed(3) : 0;
    tap.style.transform = `scale(${(.3 + 1.9 * eOutCubic(tp)).toFixed(3)})`;
  }

  /* recording layers */
  const { r, seg: cs } = recAt(Math.max(t, T.toRec));
  waits.push(setImg(recA, frameOf(r)));
  // crossfade over hard cuts: recB holds the outgoing frame
  let xf = 0;
  for (const s of SEG) if (s.cut && t >= s.t0 && t < s.t0 + .35) {
    xf = 1 - eInOutCubic(prog(t, s.t0, s.t0 + .35));
    const prev = SEG[SEG.indexOf(s) - 1];
    waits.push(setImg(recB, frameOf(prev.r1)));
  }
  recB.style.opacity = xf; recB.style.visibility = xf > 0 ? 'visible' : 'hidden';
  // blur-dip across cuts so two screens never read as a muddy double exposure
  let dip = 0;
  for (const s of SEG) if (s.cut) dip = Math.max(dip, Math.sin(Math.PI * clamp((t - s.t0 + .12) / .5)));
  const fl = $('screen');
  fl.style.filter = dip > .01 ? `blur(${(dip * 7).toFixed(2)}px) brightness(${(1 + .25 * dip).toFixed(3)})` : 'none';
  // hide the incoming notification banner by restoring the (static) sticky header
  $('patch').style.display = r >= 23.1 && r <= 25.6 ? 'block' : 'none';

  /* highlight + zoom on the frozen service card */
  let hk = 0, cur = null;
  for (const p of P) if (t >= p.t0 - .01 && t <= p.t1) { cur = p; }
  const zoomer = $('zoomer'), hl = $('hl'), rect = $('hlrect');
  if (cur) {
    const s = SV[cur.i], [x0, y0, x1, y1] = s.box;
    const hin = eOutCubic(prog(t, cur.t0 + .35, cur.t0 + 1.2)), hout = eInCubic(prog(t, cur.t1 - 1.25, cur.t1 - .6));
    hk = hin * (1 - hout);
    const w = x1 - x0, h = y1 - y0;
    hl.style.left = x0 + 'px'; hl.style.top = y0 + 'px'; hl.style.width = w + 'px'; hl.style.height = h + 'px';
    hl.style.borderRadius = '18px';
    hl.style.boxShadow = `0 0 0 1400px rgba(3,4,14,${(.6 * hk).toFixed(3)}), 0 0 ${(46 * hk).toFixed(1)}px rgba(120,110,255,${(.55 * hk).toFixed(3)})`;
    const svg = $('hlsvg'); svg.setAttribute('width', w + 16); svg.setAttribute('height', h + 16);
    rect.setAttribute('x', 8); rect.setAttribute('y', 8); rect.setAttribute('width', w); rect.setAttribute('height', h);
    const per = 2 * (w + h);
    rect.setAttribute('stroke-dasharray', per);
    rect.setAttribute('stroke-dashoffset', (per * (1 - eInOutCubic(prog(t, cur.t0 + .45, cur.t0 + 1.45)))).toFixed(1));
    rect.style.opacity = (1 - hout).toFixed(3);
    hl.style.visibility = hk > 0.001 || rect.style.opacity > 0 ? 'visible' : 'hidden';
    zoomer.style.transformOrigin = `${(x0 + x1) / 2}px ${(y0 + y1) / 2}px`;
    zoomer.style.transform = `scale(${(1 + .045 * hk).toFixed(4)})`;
  } else { hl.style.visibility = 'hidden'; zoomer.style.transform = 'none'; }

  /* service panels + floats */
  SV.forEach((s, i) => {
    const p = P[i];
    const on = t > p.t0 - .1 && t < p.t1 + .1;
    s.g.style.display = on ? 'block' : 'none';
    s.f.style.display = on ? 'block' : 'none';
    if (!on) return;
    const a = p.t0 + .55, e = p.t1 - 1.35;
    reveal(s.num, t, a, e, { d: .8, dy: 20, blur: 10, dx: 30 });
    staggerWords(s.w1, t, a + .15, e, .08, { d: .95, dy: 46, blur: 22 });
    staggerWords(s.w2, t, a + .15 + s.w1.length * .08 + .05, e + .05, .08, { d: 1, dy: 46, blur: 22 });
    reveal(s.defEl, t, a + .95, e + .12, { d: .9, dy: 22, blur: 12 });
    s.chips.forEach((c, j) => {
      const st = a + 1.5 + j * .085;
      const q = eOutBack(prog(t, st, st + .6)), qo = eInCubic(prog(t, e + .15 + j * .02, e + .6 + j * .02));
      const o = clamp(prog(t, st, st + .35)) * (1 - qo);
      fx(c, o, 8 * (1 - clamp(q)) + 8 * qo, 0, 22 * (1 - q) - 14 * qo, lerp(.92, 1, clamp(q)));
      c.querySelector('.sheen').style.left = (lerp(-140, 480, prog(Math.max(0, t - st) % 5.2, .35, 1.05))) + 'px';
    });
    // floating cards
    const fa = s.f.querySelector('.fa'), fb = s.f.querySelector('.fb');
    const fl = Math.sin(t * 1.1 + i) * 6, fl2 = Math.cos(t * .9 + i) * 7;
    reveal(fa, t, p.t0 + .9, e + .1, { d: 1, dx: -70, dy: 20 + fl, blur: 16, s0: .94 });
    fa.style.transform += ` translateY(${fl.toFixed(2)}px)`;
    reveal(fb, t, p.t0 + 1.25, e + .18, { d: 1, dx: -70, dy: 30, blur: 16, s0: .94 });
    fb.style.transform += ` translateY(${fl2.toFixed(2)}px)`;
    FANIM[i](s.f, t - (p.t0 + .9), t);
  });

  /* progress bar */
  const po = prog(t, P[0].t0 - .6, P[0].t0 + .2) * (1 - prog(t, P[3].t1 + .8, P[3].t1 + 1.4));
  fx($('prog'), po, 8 * (1 - po), 0, -14 * (1 - po), 1, '');
  $('prog').style.transform = `translateX(-50%) translateY(${(-14 * (1 - po)).toFixed(2)}px)`;
  SV.forEach((s, i) => {
    const it = $('pi' + i), p = P[i];
    const act = t >= p.t0 - .2 && t < p.t1;
    const done = t >= p.t1;
    it.style.color = act ? '#fff' : done ? '#aab2dc' : '#5f6894';
    const d = it.querySelector('.d');
    d.style.background = act ? 'linear-gradient(135deg,#5b8cff,#b07bff)' : done ? '#6f7bd6' : '#2c3150';
    d.style.boxShadow = act ? '0 0 14px rgba(140,120,255,.9)' : 'none';
    if (i < 3) $('pb' + i).style.width = (prog(t, p.t1 - .9, P[i + 1].t0 + .2) * 100) + '%';
  });

  /* side captions */
  const A1 = T.A0 + .75, Ae = T.B0 - .6;
  reveal(capAk, t, A1, Ae, { d: .8, dy: 16, blur: 10 });
  staggerWords(capA1, t, A1 + .15, Ae, .1, { d: 1, dy: 50, blur: 24 });
  staggerWords(capA2l, t, A1 + .35, Ae + .05, .1, { d: 1, dy: 50, blur: 24 });
  staggerWords(capR1, t, A1 + .7, Ae, .08, { d: .95, dy: 36, blur: 18 });
  staggerWords(capR2, t, A1 + .85, Ae + .05, .08, { d: .95, dy: 36, blur: 18 });
  reveal(capR3, t, A1 + 1.3, Ae + .1, { d: .8, dy: 16, blur: 10 });
  const B1 = T.B0 + 2.2, Be = P[0].t0 - .5;
  staggerWords(cb1, t, B1, Be, .08, { d: 1, dy: 40, blur: 20 });
  staggerWords(cb2, t, B1 + .25, Be + .04, .08, { d: 1, dy: 40, blur: 20 });
  staggerWords(cb3, t, B1 + .55, Be + .08, .09, { d: 1.1, dy: 44, blur: 22 });

  /* outro */
  const o0 = OUT.t0 + .6;
  const lg = eOutCubic(prog(t, o0, o0 + 1.3));
  fx($('oLogo'), lg * (1 - prog(t, OUT.end - .7, OUT.end - .1)), 22 * (1 - lg), 0, 30 * (1 - lg), lerp(1.08, 1, lg));
  staggerWords(oTag, t, o0 + .8, null, .085, { d: 1, dy: 36, blur: 18 });
  reveal($('oCta'), t, o0 + 1.6, null, { d: 1, dy: 34, blur: 14 });
  reveal($('oLoc'), t, o0 + 2.1, null, { d: .9, dy: 16, blur: 10 });
  $('oSheen').style.left = lerp(-160, 520, prog(t, o0 + 2.6, o0 + 3.5)) + 'px';
  const fade = prog(t, OUT.end - .7, OUT.end - .05);
  $('outro').style.opacity = 1 - fade;
  $('stage').style.filter = fade > 0 ? `brightness(${(1 - fade).toFixed(3)})` : 'none';

  await Promise.all(waits);
}

/* per-service float animations: u = local time since cards start */
const FANIM = [
  (f, u) => {
    const q = eOutCubic(prog(u, .4, 2.0));
    f.querySelector('.arc').setAttribute('stroke-dashoffset', (289 * (1 - .98 * q)).toFixed(1));
    f.querySelector('.num').textContent = Math.round(98 * q);
    f.querySelectorAll('.ln').forEach((l, j) => { const z = eOutCubic(prog(u, .7 + j * .18, 1.2 + j * .18)); l.style.opacity = z; l.style.transform = `translateX(${(-12 * (1 - z)).toFixed(1)}px)`; });
  },
  (f, u) => {
    const q = eInOutCubic(prog(u, .4, 2.0));
    f.querySelector('.ln').setAttribute('stroke-dashoffset', (420 * (1 - q)).toFixed(1));
    f.querySelector('.area').setAttribute('opacity', prog(u, 1.2, 2.2).toFixed(3));
    const pt = f.querySelector('.pt'); const pp = prog(u, 1.9, 2.2);
    pt.setAttribute('opacity', pp); pt.setAttribute('r', (6 + 2.5 * Math.sin(u * 4) * pp).toFixed(2));
    [100, 72, 44, 26].forEach((w, j) => { f.querySelector('.fb' + j).style.width = (w * eOutCubic(prog(u, .7 + j * .2, 1.7 + j * .2))) + '%'; });
  },
  (f, u, t) => {
    ['.n0', '.n1', '.n2', '.n3'].forEach((c, j) => { const z = eOutBack(prog(u, .3 + j * .25, .9 + j * .25)); const el = f.querySelector(c); el.style.opacity = clamp(z); el.style.transform = `scale(${lerp(.8, 1, clamp(z)).toFixed(3)})`; });
    const path = f.querySelector('#wfp') || f.querySelector('path');
    // pulses travel down the three branches
    const pts = [[[60, 30], [60, 95]], [[60, 125], [170, 180]], [[60, 125], [60, 215]]];
    ['.p1', '.p2', '.p3'].forEach((c, j) => {
      const ph = ((u * .8 + j * .33) % 1), [[ax, ay], [bx, by]] = pts[j];
      const el = f.querySelector(c); el.setAttribute('cx', lerp(ax, bx, ph)); el.setAttribute('cy', lerp(ay, by, ph));
      el.setAttribute('opacity', (u > 1.2 ? Math.sin(ph * Math.PI) : 0).toFixed(3));
    });
    const m0 = f.querySelector('.m0'), m1 = f.querySelector('.m1'), m2 = f.querySelector('.m2');
    const a0 = eOutCubic(prog(u, .8, 1.3)); m0.style.opacity = a0; m0.style.transform = `translateY(${(12 * (1 - a0)).toFixed(1)}px)`;
    const typingOn = u > 1.5 && u < 2.9; m1.style.display = typingOn ? 'flex' : 'none';
    m1.querySelectorAll('.td').forEach((d, j) => d.style.opacity = (.35 + .65 * Math.max(0, Math.sin(u * 7 - j * .9))).toFixed(2));
    const a2 = eOutCubic(prog(u, 2.9, 3.4)); m2.style.display = u >= 2.9 ? 'block' : 'none'; m2.style.opacity = a2; m2.style.transform = `translateY(${(12 * (1 - a2)).toFixed(1)}px)`;
  },
  (f, u) => {
    const ph = f.querySelector('.ph'); const x = ((Math.max(0, u - .6) * .14) % 1);
    ph.style.left = (x * 100) + '%';
    const secs = Math.max(0, u - .6) * 4.2; const ss = Math.floor(secs) % 60, fr = Math.floor((secs % 1) * 30);
    f.querySelector('.tcode').textContent = `00:${String(ss).padStart(2, '0')}:${String(fr).padStart(2, '0')}`;
    const wave = f.querySelector('.wave');
    if (!wave.dataset.built) { wave.dataset.built = 1; wave.innerHTML = Array.from({ length: 60 }, (_, j) => `<i style="position:absolute;bottom:50%;left:${j * 1.66}%;width:.9%;border-radius:2px;background:#5dff9e;height:${(20 + 70 * Math.abs(Math.sin(j * 1.7) * Math.cos(j * .43))).toFixed(0)}%;transform:translateY(50%)"></i>`).join(''); }
    f.querySelectorAll('.clip').forEach((c, j) => { const z = eOutCubic(prog(u, .2 + j * .06, .7 + j * .06)); c.style.opacity = z; c.style.transform = `scaleX(${lerp(.6, 1, z).toFixed(3)})`; c.style.transformOrigin = 'left'; });
    [[-120, -9], [0, 0], [120, 9]].forEach(([dx, rot], j) => {
      const r = f.querySelector('.r' + j); const z = eOutBack(prog(u, .5 + j * .15, 1.3 + j * .15));
      r.style.transform = `translateX(${(dx * clamp(z)).toFixed(1)}px) rotate(${(rot * z).toFixed(2)}deg) translateY(${j === 1 ? -14 : 8}px)`;
      r.style.zIndex = j === 1 ? 3 : 1; r.style.opacity = clamp(prog(u, .4 + j * .15, .8 + j * .15));
      r.querySelector('.rp').style.width = (((u * .3 + j * .27) % 1) * 100) + '%';
    });
  },
];

window.DURATION = DURATION;
window.TIMELINE = { T, SEG, P, OUT };
window.renderAt = renderAt;
window.ready = document.fonts.ready.then(() => Promise.all([...document.images].map(i => i.complete ? 0 : i.decode().catch(() => 0))));
})();
