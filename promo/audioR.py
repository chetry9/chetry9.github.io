import numpy as np, json, sys, wave, soundfile as sf
from scipy.signal import resample_poly
from scipy.signal import butter, sosfilt, lfilter
name,vo_prefix=sys.argv[1],sys.argv[2]
VOG=float(sys.argv[3]) if len(sys.argv)>3 else 1.0
J=json.load(open(name+'.cues.json')); DUR=J['dur']+0.4; SR=48000; N=int(DUR*SR)
rng=np.random.default_rng(3)
M=np.zeros((N,2)); FX=np.zeros((N,2)); VO=np.zeros(N)
def add(buf,sig,t,g=1.,pan=0.):
    i=int(t*SR); 
    if i<0: sig=sig[-i:]; i=0
    n=min(len(sig),N-i)
    if n<=0: return
    s=sig[:n]*g
    if buf.ndim==1: buf[i:i+n]+=s; return
    buf[i:i+n,0]+=s*np.sqrt((1-pan)/2)*1.414; buf[i:i+n,1]+=s*np.sqrt((1+pan)/2)*1.414
T=lambda d:np.arange(int(d*SR))/SR
noise=lambda d:rng.standard_normal(int(d*SR))
f=lambda m:440*2**((m-69)/12)
def bp(x,lo,hi): return sosfilt(butter(2,[lo,hi],'bandpass',fs=SR,output='sos'),x)
def lp(x,fc,o=2): return sosfilt(butter(o,fc,'low',fs=SR,output='sos'),x)
def hp(x,fc,o=2): return sosfilt(butter(o,fc,'high',fs=SR,output='sos'),x)
def sweep_lp(x,f0,f1):
    n=len(x); out=np.empty(n); s=0.; C=256; fs=np.geomspace(f0,f1,n//C+1)
    for j in range(0,n,C):
        a=1-np.exp(-2*np.pi*fs[j//C]/SR); y,_=lfilter([a],[1,-(1-a)],x[j:j+C],zi=[s*(1-a)]); out[j:j+C]=y; s=y[-1]
    return out
def pdive(f0,f1,d,k=1): t=T(d); return np.sin(2*np.pi*np.cumsum(np.geomspace(f0,f1,len(t)))/SR)
def verb(x,d=1.6,mix=.35):  # cheap noise-convolution reverb
    ir=noise(d)*np.exp(-T(d)*4.5); ir=lp(ir,6000); y=np.convolve(x,ir)[:len(x)+int(d*SR)]*.03
    out=np.zeros(len(y)); out[:len(x)]+=x; return out*(1-mix)+y*mix
saw=lambda fr,n:2*((np.arange(n)*fr/SR)%1)-1
# ---------- library ----------
def boom(): t=T(3); return verb(pdive(90,28,3)*np.exp(-t*1.3)*1.0+lp(noise(3),300)*np.exp(-t*3)*.4,2.5,.4)
def thud(p): t=T(1.4); return verb(pdive(140*p,45*p,1.4)*np.exp(-t*4)+bp(noise(1.4),1800*p,5000)*np.exp(-t*18)*.35+np.sin(2*np.pi*660*p*t)*np.exp(-t*6)*.08,1.4,.35)
def tick(): t=T(.03); return bp(noise(.03),2500,8000)*np.exp(-t*250)
def tock(): t=T(.05); return (np.sin(2*np.pi*900*t)+bp(noise(.05),800,3000))*np.exp(-t*120)*.6
def heart(): t=T(.5); b=pdive(70,40,.5)*np.exp(-t*14); y=np.zeros(int(.7*SR)); y[:len(b)]+=b; y[int(.16*SR):int(.16*SR)+len(b)]+=b*.7; return lp(y,200)
def glitch():
    y=np.zeros(int(.25*SR))
    for i in range(5): st=int(i*.05*SR); ln=int(.025*SR); y[st:st+ln]=np.round(bp(noise(ln/SR),400+i*900,7000)*3)/3*.8
    return y
PERC=[lambda p:(bp(noise(.08),3000,9000)*np.exp(-T(.08)*60)*1.2),                         # rim/click
      lambda p:(np.sin(2*np.pi*f(84+p)*T(.12))*np.exp(-T(.12)*40)),                        # clave pitched
      lambda p:(pdive(220+p*8,90,.25)*np.exp(-T(.25)*16)),                                 # tom
      lambda p:(bp(noise(.1),900,4000)*np.exp(-T(.1)*30)+np.sin(2*np.pi*f(72+p)*T(.1))*np.exp(-T(.1)*30)*.5)]
def shepard(d):   # endlessly rising illusion
    t=T(d); y=np.zeros(len(t)); u=t/d
    for k in range(6):
        oc=(k+u*1.6)%6; fr=55*2**oc; amp=np.sin(np.pi*oc/6)**2
        y+=np.sin(2*np.pi*np.cumsum(fr)/SR)*amp
    return y*.08*(0.3+u**1.5)
def riser(d): t=T(d); u=t/d; return sweep_lp(noise(d),150,12000)*u**2.4*.9
def slam(p):
    t=T(2.0); sub=pdive(110*p,32,2.0)*np.exp(-t*2.2)
    sn=bp(noise(2.0),300,6000)*np.exp(-t*9)*.7; clang=sum(np.sin(2*np.pi*fr*p*t)*np.exp(-t*5) for fr in (523,787,1203))*.07
    return verb(sub+sn+clang,1.8,.4)
def revswell(d=.55): t=T(d); u=t/d; return hp(noise(d),2500)*u**4*1.4+np.sin(2*np.pi*np.cumsum(np.geomspace(300,1400,len(t)))/SR)*u**4*.15
def braam(d=3.2):
    t=T(d); y=np.zeros(len(t)); u=t/d
    for m in (33,45,52,57):  # A1 A2 E3 A3
        for det in (-.15,0,.15): y+=saw(f(m)*2**(det/12),len(t))
    y=sweep_lp(y,180,1400)*.18; y=np.tanh(y*3)*.5
    env=np.minimum(1,t/.06)*np.exp(-np.maximum(0,t-.4)*1.1)
    return verb(y*env+pdive(80,30,d)*np.exp(-t*1.5)*.9,2.2,.3)
def swoosh(d=.45,up=True): t=T(d); u=t/d; return sweep_lp(noise(d),400 if up else 6000,7000 if up else 300)*np.sin(np.pi*u)**1.5*1.1
def taiko(p): t=T(.9); return verb(pdive(120*p,55*p,.9)*np.exp(-t*7)+lp(noise(.9),900)*np.exp(-t*25)*.5,1.0,.3)
def glass(m): t=T(1.2); return sum(a*np.sin(2*np.pi*f(m)*r*t)*np.exp(-t*k) for r,a,k in ((1,.5,5),(2.76,.25,9),(5.4,.12,14)))*.6
def bell(): t=T(3); return verb(sum(a*np.sin(2*np.pi*f(m)*t)*np.exp(-t*k) for m,a,k in ((81,.4,1.5),(88,.25,2),(93,.15,2.5),(69,.3,1.2))),2.5,.45)
def pad(chord,d,fc=1200):
    n=int(d*SR); y=np.zeros(n)
    for m in chord:
        for det in (-.1,.1): y+=saw(f(m)*2**(det/12),n)
    e=np.minimum(1,np.minimum(np.arange(n)/(.4*SR),(n-np.arange(n))/(.3*SR)))
    return lp(y,fc)*.035*e

ct={}
for tm,ty in J['cues']: ct.setdefault(ty,tm)
beat=60/122
def pluck(m,d=.3,br=1.0): t=T(d); return (np.sin(2*np.pi*f(m)*t)+.35*br*np.sin(4*np.pi*f(m)*t))*np.exp(-t*12)
def kick(): t=T(.4); return lp(pdive(150,45,.4)*np.exp(-t*8),400)
def hat(o=False): d=.25 if o else .05; return hp(noise(d),7000)*np.exp(-T(d)*(14 if o else 80))
def clap(): return verb(bp(noise(.25),900,5000)*np.exp(-T(.25)*18),.8,.25)
def zipdown(): t=T(.4); return lp(np.sign(np.sin(2*np.pi*np.cumsum(np.geomspace(1800,150,len(t)))/SR))*.3,4000)*np.sin(np.pi*t/.4)
def bubble(p): t=T(.16); return np.sin(2*np.pi*np.cumsum(np.geomspace(300*p,900*p,len(t)))/SR)*np.exp(-t*24)
def key(): return bp(noise(.04),1800,6000)*np.exp(-T(.04)*160)*1.2
WH=[lambda:swoosh(.45,True),lambda:swoosh(.4,False),lambda:revswell(.45),lambda:zipdown(),lambda:swoosh(.6,True)*.8+bp(noise(.6),5000,11000)*np.sin(np.pi*T(.6)/.6)**3*.3]
PROG=[[57,60,64],[53,57,60],[55,59,62],[52,55,59]]; BASS=[45,41,43,40]
S2=2.85; S3=ct['swoosh']-.15; DROP=ct['impact']; OUT=ct['outro']
FULL0=2.85
t=0.; i=0
while t<DUR-.3:
    b=i%4; bar=int(t//(beat*4))%4; ch=PROG[bar]
    if b==0: add(M,pad(ch,beat*4,900 if t<FULL0 else 1700),t,1.0)
    if t<S2:
        for j,m in enumerate([ch[0],ch[2],ch[1]+12,ch[2]]): add(M,pluck(m+12,.25,.5),t+j*beat/4,.06,(-.4,.4)[j%2])
    elif t<S3 or (DROP<=t<OUT):
        full=(t>=DROP) or (FULL0<=t<S3)
        add(M,kick(),t,.7 if full else .5)
        if full and b in (1,3): add(M,clap(),t,.28,.1)
        for j in range(4 if full else 2): add(M,hat(),t+j*beat/(4 if full else 2),.06 if j%2 else .09,(-.4,.4)[j%2])
        if full and b==3 and bar%2: add(M,hat(True),t+beat/2,.08)
        add(M,lp(saw(f(BASS[bar]+12),int(beat*SR*.9)),600)*np.exp(-T(beat*.9)*2.2),t,.28)
        if full: add(M,pluck([ch[0],ch[2],ch[1]+12,ch[2]][b]+24,.2,.6),t+beat/2,.05,(-.5,.5)[b%2])
    elif t>=OUT:
        if b==0 and t<OUT+beat*4: add(M,kick(),t,.45)
    t+=beat; i+=1
add(FX,riser(DROP-S3),S3,.4); add(M,shepard(DROP-S3),S3,.6)
add(M,pad([57,64,69,72],4.0,900),OUT+1.5,1.2)
wi=0
for tm,ty in J['cues']:
    if ty=='boom': add(FX,boom(),tm,.7)
    elif ty=='pop': add(FX,bubble(1.0),tm,.25)
    elif ty in ('hit','hit2'): add(FX,thud(1.0 if ty=='hit' else 1.2),tm,.55)
    elif ty in ('whoosh','swoosh','swoosh2'): fn=WH[wi%len(WH)]; wi+=1; add(FX,fn(),tm-.2,.5,rng.uniform(-.5,.5))
    elif ty=='count':
        for j in range(16): add(FX,tick(),tm+1.2*(j/16)**1.5,.35)
    elif ty.startswith('dot'): k=int(ty[3:]); add(FX,glass([84,88,91][k]),tm,.35,(-.4,0,.4)[k])
    elif ty in ('impact','impact2'): add(FX,slam(1.0 if ty=='impact' else 1.15),tm,.6); 
    elif ty.startswith('hitA'): k=int(ty[4:]); add(FX,thud((1.0,1.1,.92,1.2)[k]),tm,.45); add(FX,WH[k%len(WH)](),tm-.2,.35,(-.4,.4)[k%2])
    elif ty.startswith('hitB'): k=int(ty[4:]); add(FX,pluck([72,74,76,79][k],.5,.8),tm,.14); add(FX,swoosh(.35,k%2==0),tm-.15,.35,(.4,-.4)[k%2])
    elif ty.startswith('row'): k=int(ty[3:]); add(FX,thud((1.2,1.3,1.4,1.5)[k]),tm,.25); add(FX,swoosh(.3,True),tm-.12,.3,(-.4,.4)[k%2])
    elif ty=='slamlock': add(FX,thud(.85),tm,.5); add(FX,sum(np.sin(2*np.pi*fr*T(.6))*np.exp(-T(.6)*9) for fr in (880,1320,2210))*.05,tm,1.)
    elif ty=='click': add(FX,bp(noise(.05),2000,8000)*np.exp(-T(.05)*120)*1.4,tm,.6); add(FX,pdive(300,120,.12)*np.exp(-T(.12)*30),tm,.4)
    elif ty=='scan': t_=T(1.5); add(FX,np.sin(2*np.pi*np.cumsum(np.geomspace(500,1600,len(t_)))/SR)*np.sin(np.pi*t_/1.5)*.08+bp(noise(1.5),3000,9000)*np.sin(np.pi*t_/1.5)*.12,tm,1.)
    elif ty=='flip': add(FX,bp(noise(.12),1500,7000)*np.exp(-T(.12)*40)*1.2,tm,.5); add(FX,thud(1.3),tm+.1,.35)
    elif ty.startswith('card'): k=int(ty[4:]); add(FX,WH[(k+1)%len(WH)](),tm-.2,.45,(-.5,.5,0)[k]); add(FX,thud((1.0,1.15,1.3)[k]),tm,.3)
    elif ty=='yes': add(FX,pluck(84,.3,.6),tm,.16); add(FX,bubble(1.6),tm,.08,rng.uniform(-.4,.4))
    elif ty=='nope': add(FX,lp(saw(f(40),int(.14*SR)),900)*np.exp(-T(.14)*20),tm,.22,rng.uniform(-.4,.4))
    elif ty=='close': add(FX,zipdown(),tm,.4)
    elif ty.startswith('tick'): k=int(ty[4:]); add(FX,pluck([76,79,84][k],.5,.8),tm,.18); add(FX,bubble(1.4),tm,.12)
    elif ty.startswith('app'): k=int(ty[3:]); add(FX,bubble((1.0,1.2,1.35,1.6)[k]),tm,.16,rng.uniform(-.6,.6))
    elif ty=='key': add(FX,key(),tm,.3,rng.uniform(-.3,.3))
    elif ty=='ring': add(FX,np.sin(2*np.pi*np.cumsum(np.geomspace(300,1200,int(1.0*SR)))/SR)*np.linspace(0,1,int(1.0*SR))*.12,tm,1.)
    elif ty.startswith('glass'): k=int(ty[5:]); add(FX,glass([84,88,91,96][k]),tm,.25,(-.6,.6,-.3,.3)[k])
    elif ty=='outro': add(FX,bell(),tm+3.6,.35)
b=int(DUR*SR)
# ---------- VO ----------
for tm,ty in J['cues']:
    if ty.startswith('vo:'):
        k=int(ty[3:]); v,sr=sf.read(f'{vo_prefix}_{k:02d}.wav'); v=resample_poly(v,2,1)
        add(VO,v,tm)
VO*=.9/np.max(np.abs(VO))
denv=lfilter([1-np.exp(-1/(.08*SR))],[1,-np.exp(-1/(.08*SR))],(np.abs(VO)>.02).astype(float)); dk=np.clip(denv*1.6,0,1)
# carve a pocket for the voice: pull 700Hz-4kHz out of music & fx while the narrator speaks
def carve(X,depth):
    mid=np.stack([bp(X[:,0],700,4000),bp(X[:,1],700,4000)],1); return X-mid*(depth*dk)[:,None]
dk=dk*(1 if VOG>0 else 0)
Mc=carve(M,.8)*(1-.62*dk)[:,None]; FXc=carve(FX,.7)*(1-.45*dk)[:,None]
mix=Mc*.9+FXc*.85+np.stack([VO,VO],1)*1.85*VOG
r=lambda x:20*np.log10(np.sqrt((x**2).mean())+1e-9); m=dk>.6
print('VO',round(r(VO[m]*1.85*VOG),1),'music+fx under VO',round(r((Mc*.9+FXc*.85).mean(1)[m]),1),'music+fx elsewhere',round(r((Mc*.9+FXc*.85).mean(1)[~m]),1))
fo=int(.8*SR); mix[-fo:]*=np.linspace(1,0,fo)[:,None]
mix=np.tanh(mix*1.25)/np.tanh(1.25); mix*=.92/np.max(np.abs(mix))
with wave.open(name+'.wav','wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype('<i2').tobytes())
print('ok',DUR)
