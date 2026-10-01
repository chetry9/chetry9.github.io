import numpy as np, json, sys, wave, soundfile as sf
from scipy.signal import butter, sosfilt, lfilter
name,vo_prefix=sys.argv[1],sys.argv[2]
J=json.load(open(name+'.cues.json')); DUR=J['dur']+0.6; SR=48000; N=int(DUR*SR)
rng=np.random.default_rng(11)
M=np.zeros((N,2)); FX=np.zeros((N,2)); VO=np.zeros(N)
def add(buf,sig,t,g=1.,pan=0.):
    i=int(max(t,0)*SR); n=min(len(sig),N-i)
    if n<=0: return
    s=sig[:n]*g
    if buf.ndim==1: buf[i:i+n]+=s; return
    buf[i:i+n,0]+=s*np.sqrt((1-pan)/2)*1.414; buf[i:i+n,1]+=s*np.sqrt((1+pan)/2)*1.414
def bp(x,lo,hi): return sosfilt(butter(2,[lo,hi],'bandpass',fs=SR,output='sos'),x)
def lp(x,fc,o=2): return sosfilt(butter(o,fc,'low',fs=SR,output='sos'),x)
def hp(x,fc,o=2): return sosfilt(butter(o,fc,'high',fs=SR,output='sos'),x)
def sweep_lp(x,f0,f1):  # time-varying one-pole lowpass (vectorised in chunks)
    n=len(x); out=np.empty(n); s=0.; C=256
    fs=np.geomspace(f0,f1,n//C+1)
    for j in range(0,n,C):
        a=1-np.exp(-2*np.pi*fs[j//C]/SR); seg=x[j:j+C]
        y,zf=lfilter([a],[1,-(1-a)],seg,zi=[s*(1-a)]) ; out[j:j+C]=y; s=y[-1]
    return out
T=lambda d:np.arange(int(d*SR))/SR
noise=lambda d:rng.standard_normal(int(d*SR))
f=lambda m:440*2**((m-69)/12)
# ---------------- transition library (all different) ----------------
def w_air(d=.7):      # classic airy whoosh rising then falling
    t=T(d); x=noise(d); u=t/d
    y=sweep_lp(x,300,6000); y=y*np.sin(np.pi*u)**2; return hp(y,200)*1.2
def w_reverse(d=.9):  # reverse cymbal swell that cuts
    t=T(d); u=t/d; y=hp(noise(d),3000)*u**3
    return y*1.3
def w_subdrop(d=1.0): # pitch dive boom
    t=T(d); ph=2*np.pi*np.cumsum(np.geomspace(160,32,len(t)))/SR
    return np.sin(ph)*np.exp(-t*3)*1.1+lp(noise(d),400)*np.exp(-t*10)*.5
def w_shimmer(d=1.1): # sparkly arpeggio sweep
    y=np.zeros(int(d*SR))
    for i,m in enumerate([81,84,88,91,93,96]):
        tt=T(.35); s=np.sin(2*np.pi*f(m)*tt)*np.exp(-tt*9)*.25; st=int(i*.07*SR); y[st:st+len(s)]+=s[:len(y)-st]
    return y+hp(noise(d),5000)*np.sin(np.pi*T(d)/d)**3*.35
def w_zip(d=.45):     # fast zip / swipe down
    t=T(d); u=t/d; ph=2*np.pi*np.cumsum(np.geomspace(2200,180,len(t)))/SR
    return lp(np.sign(np.sin(ph))*.3,5000)*np.sin(np.pi*u)*.9
def w_glitch(d=.5):   # stuttered noise bursts
    y=np.zeros(int(d*SR))
    for i in range(6):
        st=int(i*d/6*SR); ln=int(d/6*SR*.55); y[st:st+ln]=bp(noise(ln/SR),800+i*500,3000+i*900)*(.9-i*.1)
    return y
def w_woom(d=1.0):    # deep doppler pass-by
    t=T(d); u=t/d; fr=np.interp(u,[0,.5,1],[90,140,60])
    return (np.sin(2*np.pi*np.cumsum(fr)/SR)*.7+sweep_lp(noise(d),200,1800)*.8)*np.sin(np.pi*u)**2
def w_swipe(d=.35):   # paper swipe
    t=T(d); return bp(noise(d),1500,7000)*np.sin(np.pi*t/d)**.6*np.exp(-t*4)*1.3
TRANS=[(w_air,.55),(w_zip,.45),(w_reverse,.45),(w_woom,.55),(w_glitch,.35),(w_swipe,.5),(w_shimmer,.6),(w_subdrop,.55)]
# ---------------- hits / ui ----------------
def hit_tom(): t=T(.6); return np.sin(2*np.pi*np.cumsum(np.geomspace(180,70,len(t)))/SR)*np.exp(-t*7)+lp(noise(.6),2000)*np.exp(-t*30)*.4
def hit_snap(): t=T(.4); return bp(noise(.4),1200,6000)*np.exp(-t*25)*1.4+np.sin(2*np.pi*220*t)*np.exp(-t*20)*.4
def hit_boom(): t=T(1.4); return np.sin(2*np.pi*np.cumsum(np.geomspace(120,38,len(t)))/SR)*np.exp(-t*2.5)*1.1+lp(noise(1.4),600)*np.exp(-t*6)*.5
def impact():
    t=T(2.6); b=np.sin(2*np.pi*np.cumsum(np.geomspace(110,34,len(t)))/SR)*np.exp(-t*1.4)
    tail=lp(noise(2.6),1500)*np.exp(-t*2.2)*.5; bell=sum(np.sin(2*np.pi*f(m)*t)*np.exp(-t*1.8) for m in (69,76,81))*.08
    return b+tail+bell
def riser(d): t=T(d); u=t/d; return sweep_lp(noise(d),200,9000)*u**2*.9+np.sin(2*np.pi*np.cumsum(np.geomspace(200,900,len(t)))/SR)*u**3*.15
def click(): t=T(.035); return (np.sin(2*np.pi*3000*t)*.5+noise(.035)*.4)*np.exp(-t*280)
def key(i): t=T(.045); return bp(noise(.045),1500+ (i%4)*400,6000)*np.exp(-t*160)*1.3
def pluck(m,d=.3,br=1.0):
    t=T(d); return (np.sin(2*np.pi*f(m)*t)+.35*br*np.sin(4*np.pi*f(m)*t)+.12*np.sin(6*np.pi*f(m)*t))*np.exp(-t*14)
def pop(fr): t=T(.14); return np.sin(2*np.pi*np.cumsum(np.linspace(fr*.7,fr*1.2,len(t)))/SR)*np.exp(-t*30)
def ring_rise(): t=T(1.2); u=t/1.2; return np.sin(2*np.pi*np.cumsum(np.geomspace(300,1200,len(t)))/SR)*u*np.exp(-np.maximum(0,u-.85)*20)*.15
def ding(): t=T(1.5); return sum(a*np.sin(2*np.pi*f(m)*t)*np.exp(-t*k) for m,a,k in ((88,.5,3),(95,.25,4),(100,.12,6)))
def coin(): 
    y=np.zeros(int(.6*SR))
    for i,m in enumerate([88,95]): s=np.sign(np.sin(2*np.pi*f(m)*T(.3)))*np.exp(-T(.3)*9)*.25; st=int(i*.08*SR); y[st:st+len(s)]+=s
    return lp(y,6000)
def swell(): t=T(2.6); return sum(np.sin(2*np.pi*f(m)*t) for m in (57,64,69,72,76))*np.minimum(1,t/1.1)*np.exp(-np.maximum(0,t-1.2)*1.8)*.06

def glass(m):   # glassy tink: inharmonic partials + soft air
    t=T(1.2); y=sum(a*np.sin(2*np.pi*f(m)*r*t)*np.exp(-t*k) for r,a,k in ((1,.5,5),(2.76,.25,9),(5.4,.12,14),(8.9,.06,20)))
    return y*.6+hp(noise(1.2),4000)*np.exp(-t*25)*.25
def suck(d=.6): t=T(d); u=t/d; return sweep_lp(noise(d),500,7000)*u**2.5*.9+np.sin(2*np.pi*np.cumsum(np.geomspace(200,700,len(t)))/SR)*u**2*.2
def success():
    y=np.zeros(int(1.4*SR))
    for i,m in enumerate([76,83,88]):
        tt=T(1.0); s=(np.sin(2*np.pi*f(m)*tt)+.3*np.sin(4*np.pi*f(m)*tt))*np.exp(-tt*4)*.35; st=int(i*.09*SR); y[st:st+len(s)]+=s
    return y
# ---------------- music with sections ----------------
cues=J['cues']; ct={c[1]:c[0] for c in cues}
BPM=118; beat=60/BPM; bar=beat*4
INTRO='impact' in ct
DROP=ct.get('impact',0.0); OUT=ct.get('outro',1e9); G0=5.85 if INTRO else -1
SECS=sorted(c[0] for c in cues if c[1].startswith('sec'))
S0=SECS[0] if SECS else 1e9
PROGS=[([[57,60,64],[53,57,60],[48,52,55],[55,59,62]],[45,41,48,43]),   # Am F C G
       ([[50,53,57],[53,57,60],[48,52,55],[52,55,59]],[38,41,36,40]),   # Dm F C Em
       ([[53,57,60],[55,59,62],[52,55,59],[57,60,64]],[41,43,40,45]),   # F G Em Am
       ([[48,52,55],[55,59,62],[57,60,64],[53,57,60]],[36,43,45,41])]   # C G Am F
def sec_index(t):
    i=-1
    for j,st in enumerate(SECS):
        if t>=st-0.01: i=j
    return i
def prog(t):
    i=sec_index(t); P,B=PROGS[(i+ (1 if not INTRO else 0))%4] if i>=0 else PROGS[0]
    if t>=OUT: P,B=PROGS[0]
    return P[int(t//bar)%4],B
def in_break(t): return any(st-bar<=t<st+bar*.5 for st in SECS)
def saw(fr,n): return 2*((np.arange(n)*fr/SR)%1)-1
kick=(lambda t:np.sin(2*np.pi*np.cumsum(np.geomspace(140,45,len(t)))/SR)*np.exp(-t*8))(T(.4))
hat=hp(noise(.06),7000)*np.exp(-T(.06)*70); ohat=hp(noise(.25),6000)*np.exp(-T(.25)*14)
clap=bp(noise(.25),900,5000)*np.exp(-T(.25)*18)
shaker=bp(noise(.08),5000,12000)*np.sin(np.pi*T(.08)/.08)
# pad per bar
t=0.
while t<DUR:
    ch,_=prog(t); n=min(int(bar*SR),N-int(t*SR))
    if n<=0: break
    s=np.zeros(n)
    for m in ch:
        for det in (-.12,.12): s+=saw(f(m+12)*2**(det/12/8),n)
    fc=900 if t<DROP else 2200
    if any(st<=t<st+bar for st in SECS): fc=500
    s=lp(s,fc)*.045; e=np.minimum(1,np.minimum(np.arange(n)/(.3*SR),(n-np.arange(n))/(.3*SR)))
    add(M,s*e,t,1.,0); t+=bar
# rhythm
t=0.; i=0
while t<DUR-.4:
    b=i%4; bb=i%16; ch,bs=prog(t); m=bs[int(t//bar)%4]
    brk=in_break(t)
    if INTRO and t<3.3:   # intro heartbeat
        if b in (0,1) : add(M,lp(kick,300),t+(0 if b==0 else .18),.35)
    elif t<G0:  # tension: pulse on 8ths
        add(M,pluck(ch[0]+12,.2,.3),t,.12,-.2); add(M,pluck(ch[1]+12,.2,.3),t+beat/2,.1,.2)
    elif t<DROP: # curious search groove: arps + shaker
        for j,nn in enumerate([ch[0],ch[1],ch[2],ch[1]+12]):
            add(M,pluck(nn+12,.25),t+j*beat/4,.08,(-.4,.4)[j%2])
        add(M,shaker,t+beat/2,.1,.3)
        if b==0: add(M,kick,t,.3)
    elif t>=OUT:
        if b==0 and t<OUT+beat*2: add(M,kick,t,.4)
    elif brk:
        add(M,hat,t,.05); add(M,hat,t+beat/2,.05)
    else:
        vpn=sec_index(t)%2==1
        add(M,kick,t,.62)
        if vpn and b==2: add(M,kick,t+beat*.75,.35)
        if b in (1,3): add(M,clap,t,.2,.1)
        if vpn:
            for j in range(4): add(M,hat,t+j*beat/4,.05 if j%2 else .08,-.3)
        else:
            add(M,hat,t+beat/2,.08,.3); 
            if bb==15: add(M,ohat,t+beat/2,.09)
        # bass
        n=int(beat*SR*.92); tb=T(n/SR); bsig=(np.sin(2*np.pi*f(m-12)*tb)+.3*np.sin(2*np.pi*f(m)*tb))*np.exp(-tb*2.5)*np.minimum(1,tb*300)
        add(M,bsig,t,.24)
        # lead arp in sections for movement
        if t>=S0:
            nn=[ch[0],ch[2],ch[1]+12,ch[2]][b]+24 if not vpn else [ch[2],ch[0]+12,ch[1]+12,ch[0]+12][b]+12
            add(M,pluck(nn,.22,.6),t+beat/2,.06,(-.5,.5)[b%2])
    t+=beat; i+=1
# ---------------- place sfx ----------------
ti=0; last=None; order=[0,1,2,3,4,5,6,7,0,3,1,6,2,5,4,7]
keyi=0; tick=0; popi=0; secn=0; hitn=0; POPS=[660,740,830,880,990,1100]
for tm,ty in cues:
    if ty in('whoosh','swoosh'):
        fn,g=TRANS[order[ti%len(order)]]; ti+=1; s=fn()
        off=.45 if fn in (w_reverse,) else .25
        add(FX,s,tm-off,g*(1.2 if ty=='swoosh' else 1),rng.uniform(-.5,.5))
    elif ty=='hit0': add(FX,hit_tom(),tm,.55)
    elif ty=='hit1': add(FX,hit_snap(),tm,.5,-.2)
    elif ty=='hit2': add(FX,hit_boom(),tm,.6)
    elif ty=='impact': add(FX,impact(),tm,.75); add(FX,riser(1.2),tm-1.2,.3)
    elif ty=='riser': add(FX,w_reverse(.4),tm,.3)
    elif ty=='titleriser': add(FX,riser(.75),tm,.28)
    elif ty.startswith('sec'): add(FX,(hit_boom,hit_tom,hit_snap)[secn%3](),tm,.4); secn+=1
    elif ty=='hit': add(FX,(hit_snap,hit_tom,hit_boom)[hitn%3](),tm,.35,(-.2,.2,0)[hitn%3]); hitn+=1
    elif ty.startswith('step'): si_=int(ty[4:]); [add(FX,pluck(m+12,.6,.8),tm+j*.05,.12,(-.3,0,.3)[j]) for j,m in enumerate([[60,64,67],[62,65,69],[64,67,72]][si_])]
    elif ty=='click': add(FX,click(),tm,.8)
    elif ty=='key': add(FX,key(keyi),tm,.4,rng.uniform(-.25,.25)); keyi+=1
    elif ty=='pop': add(FX,pop(POPS[popi%6]),tm,.2,rng.uniform(-.4,.4)); popi+=1
    elif ty=='tick': scale=[72,74,76,79,81,84,86,88]; add(FX,pluck(scale[tick%8]+12,.25),tm,.1,rng.uniform(-.3,.3)); tick+=1
    elif ty=='count':
        for j in range(14): add(FX,click(),tm+1.3*(j/14)**1.6,.25)
    elif ty=='ring': add(FX,ring_rise(),tm,1.)
    elif ty=='price': add(FX,coin(),tm,.5)
    elif ty=='deal': add(FX,ding(),tm,.12)
    elif ty=='swell': add(FX,swell(),tm,1.)
    elif ty=='outro': add(FX,impact(),tm,.45)
    elif ty.startswith('glass'): gi=int(ty[5:]); add(FX,glass([84,88,91,96][gi]),tm,.35,(-.7,.7,-.4,.4)[gi]); add(FX,w_swipe(.3),tm-.1,.25,(-.7,.7,-.4,.4)[gi])
    elif ty=='glow': add(FX,w_shimmer(.9),tm,.3)
    elif ty=='merge': add(FX,suck(),tm,.5)
    elif ty=='rise': add(FX,w_shimmer(),tm-.1,.5); add(FX,w_air(.6),tm-.2,.35)
    elif ty=='fclick': add(FX,click(),tm,.9); add(FX,success(),tm+.05,.6)
# ---------------- voice-over ----------------
vo_i=0
for tm,ty in cues:
    if ty.startswith('vo:'):
        k=int(ty[3:]); a,sr=sf.read(f'{vo_prefix}_{k:02d}.wav'); assert sr==24000
        a=np.interp(np.arange(int(len(a)*2))/2,np.arange(len(a)),a)  # 24k -> 48k
        add(VO,a,tm,1.)
# VO polish: gentle high-pass, presence, compression-ish
VO=hp(VO,90); VO=VO+0.25*bp(VO,2500,6000)
env=np.abs(VO); env=lfilter([1-np.exp(-1/(0.01*SR))],[1,-np.exp(-1/(0.01*SR))],env)
gain=np.minimum(1,0.35/np.maximum(env,1e-4))**0.5; VO*=gain; VO*=0.9/np.max(np.abs(VO))
# ducking: music & fx under voice
denv=lfilter([1-np.exp(-1/(0.12*SR))],[1,-np.exp(-1/(0.12*SR))],(np.abs(VO)>0.02).astype(float))
duck=1-0.68*np.clip(denv*1.5,0,1)
mix=M*duck[:,None]*0.9+FX*(1-0.5*np.clip(denv,0,1))[:,None]*0.8+np.stack([VO,VO],1)*1.5
m_=denv>0.6; bg=(M*duck[:,None]*0.9+FX*(1-0.5*np.clip(denv,0,1))[:,None]*0.8).mean(1)
r=lambda x:20*np.log10(np.sqrt((x**2).mean()))
print('VO',r(VO[m_]*1.5),'bg under VO',r(bg[m_]),'bg elsewhere',r(bg[~m_]))
fade=np.ones(N); fi=int((.2 if INTRO else .1)*SR); fo=int((1.8 if 'merge' in ct else 0.25)*SR); fade[:fi]=np.linspace(0,1,fi); fade[-fo:]=np.linspace(1,0,fo)
mix*=fade[:,None]; mix=np.tanh(mix*1.3)/np.tanh(1.3); mix*=0.9/np.max(np.abs(mix))
with wave.open(name+'.wav','wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype('<i2').tobytes())
print('ok',round(DUR,2),'transitions used:',ti)
