/* Upscore Tech teaser (~25s). Deterministic: window.renderAt(t).
 * Shots are live renders of the main promo scene (index.html in an iframe), so punch-ins stay sharp.
 * Editing rules (from the hook tutorial): clean first frame with one focal point, <=3 lines of text,
 * pointer/circle arrives ~0.3s after the cut, tight beat-cut pacing, end on an open loop. */
(() => {
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, k) => a + (b - a) * k;
const prog = (t, a, b) => clamp((t - a) / (b - a));
const eOutCubic = k => 1 - Math.pow(1 - k, 3);
const eInCubic = k => k * k * k;
const eOutExpo = k => k >= 1 ? 1 : 1 - Math.pow(2, -10 * k);
const eInOutCubic = k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
const eOutBack = k => { const c1 = 1.7, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); };
const $ = id => document.getElementById(id);
function fx(el, o, blur = 0, tx = 0, ty = 0, sc = 1) {
  el.style.opacity = o; el.style.visibility = o <= .001 ? 'hidden' : 'visible';
  el.style.filter = blur > .05 ? `blur(${blur.toFixed(2)}px)` : 'none';
  el.style.transform = `translate(${tx.toFixed(2)}px,${ty.toFixed(2)}px) scale(${sc.toFixed(4)})`;
}
function words(el, text) {
  el.innerHTML = ''; const out = [];
  text.split('|').forEach((line, li) => {
    const row = document.createElement('div'); el.appendChild(row);
    line.split(/(\*[^*]+\*)/).forEach(part => {
      if (!part) return;
      const acc = part.startsWith('*');
      part.replace(/\*/g, '').split(/(\s+)/).forEach(tok => {
        if (!tok) return;
        if (/^\s+$/.test(tok)) { row.appendChild(document.createTextNode(' ')); return; }
        const s = document.createElement('span'); s.className = 'w' + (acc ? ' serif gtxt' : ''); s.textContent = tok;
        row.appendChild(s); out.push(s);
      });
    });
  });
  return out;
}
// slam-in words: fast scale-down + blur clear
function slam(ws, t, s, e, st = .06, o = {}) {
  ws.forEach((w, i) => {
    const a = s + i * st;
    const p = eOutExpo(prog(t, a, a + (o.d ?? .42)));
    const q = e == null ? 0 : eInCubic(prog(t, e, e + (o.od ?? .12)));
    fx(w, clamp(p * 1.4) * (1 - q), 18 * (1 - p) + 14 * q, 0, (o.dy ?? 24) * (1 - p), lerp(o.s0 ?? 1.35, 1, p) * (1 + .12 * q));
  });
}

/* ---------- edit decision list ---------- */
const BEAT = .5, DROP = 2.5, SHOT = 3 * BEAT;
const G0 = DROP + 8 * SHOT;          // 14.5  google moment
const L0 = 18.0;                      // logo slam
const C0 = 21.3;                      // CTA
const END = 26.5;
let TL = null;                         // main promo timeline (loaded)
const SHOTS = [
  { p: 0, off: 1.35, sp: .9, z: 1.55, f: [560, 470], text: 'Websites' },
  { p: 0, off: 1.2, sp: 1.15, z: 2.5, f: [229, 255], text: 'that load|*fast.*', circle: [-88, 5, 66, 66] },
  { p: 1, off: 1.25, sp: 1.1, z: 2.15, f: [240, 262], text: 'Marketing' },
  { p: 1, off: 1.45, sp: 1.15, z: 2.35, f: [266, 700], text: 'that|*converts.*' },
  { p: 2, off: 1.05, sp: 1.0, z: 1.85, f: [244, 330], text: 'AI agents' },
  { p: 2, off: 3.0, sp: 1.2, z: 2.3, f: [271, 705], text: 'that never|*sleep.*', circle: [50, 18, 150, 44], cd: .78 },
  { p: 3, off: 1.3, sp: 1.0, z: 2.1, f: [244, 262], text: 'Videos' },
  { p: 3, off: 1.2, sp: 1.0, z: 1.75, f: [276, 745], text: 'that stop|the *scroll.*', circle: [-6, -28, 64, 100] },
];
SHOTS.forEach((s, i) => { s.t0 = DROP + i * SHOT; s.t1 = s.t0 + SHOT; s.side = i % 2 ? 'R' : 'L'; });

/* ---------- DOM ---------- */
const wordEl = $('word');
SHOTS.forEach(s => { const d = document.createElement('div'); d.className = 'big'; d.style.fontSize = '118px'; document.getElementById('stage').insertBefore(d, $('hook')); s.el = d; s.ws = words(d, s.text); });
wordEl.remove();
const h1 = words($('h1'), 'What if *one team*'), h2 = words($('h2'), 'could do all of this?');
const gws = words($('gtext'), 'One|*search.*');
const tag = words($('tag'), 'Build smarter. *Grow faster.*');
const c1 = words($('c1'), '4 services. *One team.*');
const srcFull = $('srcFull'), srcWin = $('srcWin');
const logoR = document.querySelector('#logo img.r'), logoC = document.querySelector('#logo img.c');
logoR.style.filter = 'brightness(.6) sepia(1) saturate(12) hue-rotate(-40deg)';
logoC.style.filter = 'brightness(.6) sepia(1) saturate(12) hue-rotate(150deg)';

// grain
const gctx = $('grain').getContext('2d'), GR = [];
for (let k = 0; k < 6; k++) { const id = gctx.createImageData(960, 540); let seed = 99 + k * 7919; const r = () => ((seed = (seed * 16807) % 2147483647) / 2147483647); for (let p = 0; p < id.data.length; p += 4) { const v = r() * 255; id.data[p] = id.data[p + 1] = id.data[p + 2] = v; id.data[p + 3] = 255; } GR.push(id); }

// hand-drawn circle path around (cx,cy) with radii rx,ry, overshooting like a pen stroke
function scribble(cx, cy, rx, ry, seed) {
  let s = seed; const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647 - .5);
  const pts = [];
  for (let a = -.35; a <= Math.PI * 2 + .55; a += .12) {
    const k = 1 + .045 * Math.sin(a * 3 + seed) + .02 * rnd();
    pts.push([cx + Math.cos(a) * rx * k * (1 + a * .012), cy + Math.sin(a) * ry * k * (1 + a * .01)]);
  }
  return 'M' + pts.map(p => p.map(v => v.toFixed(1)).join(' ')).join(' L');
}

async function loadFrames() {
  const src = 'index.html?rec=rec';
  await Promise.all([srcFull, srcWin].map(f => new Promise(r => { f.onload = r; f.src = src; })));
  await Promise.all([srcFull, srcWin].map(f => f.contentWindow.ready));
  TL = await (await fetch('out/timeline.json')).json();
}

/* ---------- render ---------- */
async function renderAt(t) {
  const waits = [];
  // background
  const b1 = $('b1'), b2 = $('b2');
  b1.style.cssText = `width:1300px;height:1300px;left:${-300 + 120 * Math.sin(t * .6)}px;top:${-400 + 80 * Math.cos(t * .5)}px;background:radial-gradient(circle,rgba(46,84,255,.4),rgba(46,84,255,.1) 40%,transparent 68%)`;
  b2.style.cssText = `width:1200px;height:1200px;left:${1000 + 90 * Math.cos(t * .55)}px;top:${260 + 90 * Math.sin(t * .45)}px;background:radial-gradient(circle,rgba(139,92,255,.34),rgba(139,92,255,.08) 42%,transparent 68%)`;
  const ringOn = t < DROP ? .25 : t >= L0 ? 1 : .35;
  const ring = $('ring');
  ring.style.opacity = ringOn * (t >= L0 ? lerp(1.6, 1, eOutCubic(prog(t, L0, L0 + .8))) : 1);
  ring.style.transform = `scale(${(t >= L0 ? lerp(.8, 1, eOutExpo(prog(t, L0, L0 + .9))) : 1).toFixed(4)}) rotate(${(t * 20).toFixed(2)}deg)`;
  ring.style.webkitMaskImage = `conic-gradient(from ${t * 60}deg, transparent 0deg, #000 90deg, #000 150deg, transparent 260deg)`;
  $('bg').style.opacity = t < DROP ? .5 : 1;
  gctx.putImageData(GR[Math.floor(t * 24) % GR.length], 0, 0);

  // letterbox (montage + google)
  const lb = eOutCubic(prog(t, DROP, DROP + .35)) * (1 - eInOutCubic(prog(t, L0 - .1, L0 + .3)));
  $('barT').style.height = $('barB').style.height = (74 * lb).toFixed(1) + 'px';

  // hook — clean frame, one focal point, two lines
  const hookOut = eInCubic(prog(t, DROP - .22, DROP));
  h1.forEach((w, i) => { const p = eOutCubic(prog(t, .1 + i * .11, .75 + i * .11)); fx(w, p * (1 - hookOut), 16 * (1 - p) + 30 * hookOut, 0, 30 * (1 - p), 1 + .5 * hookOut); });
  h2.forEach((w, i) => { const p = eOutCubic(prog(t, .6 + i * .1, 1.25 + i * .1)); fx(w, p * (1 - hookOut), 16 * (1 - p) + 30 * hookOut, 0, 30 * (1 - p), 1 + .5 * hookOut); });

  // montage window
  const win = $('win');
  const cur = SHOTS.find(s => t >= s.t0 && t < s.t1);
  SHOTS.forEach(s => { if (s !== cur) s.ws.forEach(w => fx(w, 0)); });
  const circ = $('circ');
  circ.style.opacity = 0;
  if (cur && TL) {
    const u = t - cur.t0, i = SHOTS.indexOf(cur);
    const W = 1060, H = 700, wx = cur.side === 'L' ? 110 : 750, wy = 190;
    // whip: out-motion in the last 0.1s, in-motion in the first 0.12s
    const dir = cur.side === 'L' ? -1 : 1;
    const whipIn = 1 - eOutCubic(prog(u, 0, .14)), whipOut = eInCubic(prog(u, SHOT - .1, SHOT));
    const mx = (i === 0 ? 0 : whipIn * -dir * 260) + whipOut * dir * 260;
    const blurX = (i === 0 ? 0 : whipIn * 38) + whipOut * 38;
    const pop = i === 0 ? eOutBack(prog(u, 0, .45)) : 1;
    win.style.visibility = 'visible'; win.style.opacity = 1;
    win.style.left = wx + 'px'; win.style.top = wy + 'px';
    win.style.transform = `translateX(${mx.toFixed(1)}px) scale(${lerp(.86, 1, pop).toFixed(4)}) rotate(${(dir * .6 * (1 - u / SHOT)).toFixed(3)}deg)`;
    $('mbxb').setAttribute('stdDeviation', `${blurX.toFixed(1)} 0`);
    win.style.filter = blurX > .5 ? 'url(#mbx)' : 'none';
    // camera inside the window: centre the focus element, slow push-in
    const z = cur.z * (1 + .07 * u / SHOT);
    const [fx0, fy0] = cur.f;
    srcWin.style.transform = `translate(${(W / 2 - fx0 * z).toFixed(2)}px,${(H / 2 - fy0 * z).toFixed(2)}px) scale(${z.toFixed(4)})`;
    const P = TL.P[cur.p];
    waits.push(srcWin.contentWindow.renderAt(P.t0 + cur.off + u * cur.sp));
    // words on the clean side
    cur.el.style.left = (cur.side === 'L' ? 1250 : 150) + 'px'; cur.el.style.top = (cur.ws.length > 2 || cur.text.includes('|') ? 380 : 470) + 'px';
    slam(cur.ws, t, cur.t0 + .06, cur.t1 - .12, .07);
    // hand-drawn circle arrives ~0.3s after the cut
    if (cur.circle) {
      const [dx, dy, rx, ry] = cur.circle;
      const cx = wx + W / 2 + dx * z, cy = wy + H / 2 + dy * z;
      circ.setAttribute('d', scribble(cx, cy, rx * z, ry * z, 7 + i));
      const cd = cur.cd ?? .32;
      const L = circ.getTotalLength();
      circ.setAttribute('stroke-dasharray', L);
      circ.setAttribute('stroke-dashoffset', (L * (1 - eInOutCubic(prog(u, cd, cd + .42)))).toFixed(1));
      circ.style.opacity = u > cd ? 1 - whipOut : 0;
      circ.style.transform = `translateX(${mx.toFixed(1)}px)`;
      circ.setAttribute('stroke', i === 5 ? '#fff' : '#7fb0ff');
    }
  } else { win.style.visibility = 'hidden'; }

  // google moment — speed ramp: fast typing, slow-mo on the #1 glow and tap
  const full = $('full');
  const inG = t >= G0 - .02 && t < L0;
  full.style.visibility = inG ? 'visible' : 'hidden';
  if (inG && TL) {
    const T = TL.T;
    let src;
    if (t < G0 + 2.0) src = lerp(T.phoneInEnd - .1, T.glow - .1, prog(t, G0, G0 + 2.0));
    else if (t < G0 + 3.2) src = lerp(T.glow - .1, T.tap + .1, prog(t, G0 + 2.0, G0 + 3.2));
    else src = lerp(T.tap + .1, T.toRec + .25, prog(t, G0 + 3.2, L0));
    waits.push(srcFull.contentWindow.renderAt(src));
    const push = 1 + .1 * eInOutCubic(prog(t, G0, L0));
    const gin = 1 - eOutCubic(prog(t, G0, G0 + .16));
    srcFull.style.transform = `translate(${(960 - 960 * push + 170 * (1 - eOutCubic(prog(t, G0, G0 + .5)))).toFixed(1)}px,${(540 - 540 * push).toFixed(1)}px) scale(${push.toFixed(4)})`;
    $('mbxb').setAttribute('stdDeviation', `${(gin * 38).toFixed(1)} 0`);
    full.style.filter = gin > .02 ? 'url(#mbx)' : 'none';
  }
  slam(gws, t, G0 + .3, L0 - .45, .12, { d: .5 });
  $('gtext').style.visibility = inG ? 'visible' : 'hidden';

  // logo slam
  const lg = eOutExpo(prog(t, L0, L0 + .32)), lgo = eInCubic(prog(t, C0 - .25, C0));
  const shake = Math.exp(-(t - L0) * 7) * (t >= L0 ? 1 : 0);
  const sx = shake * 18 * Math.sin(t * 91), sy = shake * 12 * Math.cos(t * 77);
  fx($('logo'), (t >= L0 ? clamp(lg * 1.5) : 0) * (1 - lgo), 22 * (1 - lg) + 20 * lgo, sx, sy, lerp(1.4, 1, lg) * (1 + .15 * lgo));
  const rgb = 16 * Math.exp(-(t - L0) * 5) * (t >= L0 ? 1 : 0) + 10 * lgo;
  logoR.style.transform = `translateX(${-rgb}px)`; logoC.style.transform = `translateX(${rgb}px)`;
  logoR.style.opacity = logoC.style.opacity = clamp(rgb / 10) * .85;
  $('logoWrap').style.visibility = t >= L0 - .01 && t < C0 ? 'visible' : 'hidden';
  slam(tag, t, L0 + .75, C0 - .3, .08, { s0: 1.2 });

  // CTA — open loop
  $('cta').style.visibility = t >= C0 - .01 ? 'visible' : 'hidden';
  slam(c1, t, C0 + .05, null, .09, { s0: 1.25 });
  const bp = eOutBack(prog(t, C0 + .8, C0 + 1.3));
  fx($('cbtn'), clamp(prog(t, C0 + .8, C0 + 1.0)), 10 * (1 - clamp(bp)), 0, 30 * (1 - bp), lerp(.7, 1, bp) * (1 + .025 * Math.max(0, Math.sin((t - C0) * 5.5)) * (t > C0 + 1.4 ? 1 : 0)));
  $('sheen').style.left = lerp(-200, 620, prog((t - C0 - 1.5) % 1.8, 0, .7)) + 'px';
  fx($('curl'), eOutCubic(prog(t, C0 + 1.3, C0 + 1.8)), 0, 0, 14 * (1 - eOutCubic(prog(t, C0 + 1.3, C0 + 1.8))));

  // flashes on the big hits
  let fl = 0;
  for (const h of [DROP, L0]) fl = Math.max(fl, (t >= h ? 1 : 0) * Math.exp(-(t - h) * 9) * .85);
  for (const s of SHOTS.slice(1)) fl = Math.max(fl, (t >= s.t0 ? 1 : 0) * Math.exp(-(t - s.t0) * 22) * .22);
  fl = Math.max(fl, (t >= G0 ? 1 : 0) * Math.exp(-(t - G0) * 14) * .35);
  $('flash').style.opacity = fl.toFixed(3);
  const fade = prog(t, END - .35, END);
  $('stage').style.filter = fade > 0 ? `brightness(${(1 - fade).toFixed(3)})` : 'none';
  await Promise.all(waits);
}

window.DURATION = END;
window.TEASER = { BEAT, DROP, SHOT, G0, L0, C0, END, SHOTS: SHOTS.map(s => ({ t0: s.t0, t1: s.t1, circle: !!s.circle })) };
window.renderAt = renderAt;
window.ready = document.fonts.ready.then(loadFrames);
})();
