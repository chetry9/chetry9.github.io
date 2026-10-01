import numpy as np, json, sys, wave, soundfile as sf
from scipy.signal import butter, sosfilt, lfilter
name,vo_prefix=sys.argv[1],sys.argv[2]
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
TB=ct['braam']; TE=ct['endhit']; TC=11.0; TH=12.5
beat=.5
# ---------- MUSIC ----------
# A: drone + ticks + heartbeat
d=5.2; t=T(d); drone=(np.sin(2*np.pi*55*t)+.5*np.sin(2*np.pi*82.4*t)+.3*saw(110,len(t))*0)*np.minimum(1,t/1.5)*.18
add(M,drone+lp(noise(d),400)*.04*np.minimum(1,t/2),0)
for k in range(1,11):
    tm=k*.5; add(M,tick() if k%2 else tock(),tm,.35,(-.3,.3)[k%2])
for tm in (2.0,3.0,3.8,4.4,4.85): add(M,heart(),tm,.7)
# B: pulse ostinato 16ths building + shepard + riser
tB=5.2; L=TC-tB; n16=int(L/(beat/4))
for i in range(n16):
    tm=tB+i*beat/4; u=i/n16; m=[45,45,57,45,48,45,57,52][i%8]
    s=lp(saw(f(m),int(.11*SR)),600+3000*u)*np.exp(-T(.11)*18)
    add(M,s,tm,.12+.25*u,(-.3,.3)[i%2])
    if i%4==0: add(M,lp(pdive(120,45,.3)*np.exp(-T(.3)*10),300),tm,.25+.45*u)
add(M,shepard(L),tB,1.0); add(FX,riser(L),tB,.45)
# E–F: epic section 13.3 -> TE
prog=[[57,60,64],[53,57,60],[48,52,55],[55,59,62]]; bassn=[33,29,36,31]
tm=TB; i=0
while tm<TE-.01:
    b=i%4; bar=int((tm-TB)//2)%4
    add(M,lp(pdive(150,45,.35)*np.exp(-T(.35)*8),400),tm,.75)              # kick every beat
    if b in (1,3): add(M,verb(bp(noise(.3),400,6000)*np.exp(-T(.3)*14),1.0,.3),tm,.35)
    for j in range(4): add(M,hp(noise(.04),7000)*np.exp(-T(.04)*90),tm+j*beat/4,.06 if j%2 else .1,(-.4,.4)[j%2])
    if b==3: add(M,taiko(.8),tm+beat*.5,.3)
    bn=bassn[bar]; add(M,lp(saw(f(bn+12),int(beat*SR*.9)),500)*np.exp(-T(beat*.9)*2),tm,.3)
    if b==0: add(M,pad(prog[bar],2.0,1600),tm,1.0)
    tm+=beat; i+=1
# G: end pad tail
add(M,pad([57,64,69,72],3.6,900),TE,1.4)
# ---------- SFX ----------
ti=0; REV=(12.75,)
for tm,ty in J['cues']:
    if ty=='boom': add(FX,boom(),tm,.9)
    elif ty=='drone': pass
    elif ty=='hitA0': add(FX,thud(1.0),tm,.6)
    elif ty=='hitA1': add(FX,thud(1.25),tm,.55,.15)
    elif ty=='glitch': add(FX,glitch(),tm,.45,rng.uniform(-.5,.5))
    elif ty.startswith('tick'): k=int(ty[4:]); add(FX,PERC[k](ti*.4),tm,.35,rng.uniform(-.6,.6)); ti+=1
    elif ty.startswith('slam'): p=int(ty[4:]); add(FX,slam((1.0,1.12,.9)[p]),tm,.85,(-.15,.15,0)[p])
    elif ty=='revswell': REV=(tm,)
    elif ty=='braam': add(FX,braam(),tm,.95); add(FX,boom(),tm,.6)
    elif ty=='whoosh': add(FX,swoosh(.5,False),tm-.15,.5)
    elif ty.startswith('card'): k=int(ty[4:]); add(FX,swoosh(.35,k%2==0),tm-.2,.55,(-.6,.6)[k%2]); add(FX,taiko((1.0,1.15,.9,1.3)[k]),tm,.55)
    elif ty=='endhit': add(FX,braam(2.6),tm,.7); add(FX,slam(.85),tm,.6)
    elif ty.startswith('glass'): k=int(ty[5:]); add(FX,glass([84,88,91,96][k]),tm,.25,(-.6,.6,-.3,.3)[k])
    elif ty=='sting': add(FX,bell(),tm,.5); add(FX,thud(.7),tm,.4)
# hush: kill everything except the swell between TH and TB
hush=np.ones(N); a=int(TH*SR); b=int(TB*SR); r=int(.04*SR)
hush[a:b]=0.0; hush[a-r:a]=np.linspace(1,0,r)
M*=hush[:,None]
FX*=hush[:,None]
add(FX,revswell(.55),REV[0],.6)
# ---------- VO ----------
for tm,ty in J['cues']:
    if ty.startswith('vo:'):
        k=int(ty[3:]); v,sr=sf.read(f'{vo_prefix}_{k:02d}.wav'); v=np.interp(np.arange(len(v)*2)/2,np.arange(len(v)),v)
        add(VO,v,tm)
VO=hp(VO,90); VO=VO+.25*bp(VO,2500,6000)
env=lfilter([1-np.exp(-1/(.01*SR))],[1,-np.exp(-1/(.01*SR))],np.abs(VO)); VO*=np.minimum(1,.35/np.maximum(env,1e-4))**.5; VO*=.9/np.max(np.abs(VO))
vg=np.ones(N); vg[int(12.38*SR):b]=.45; VO*=vg
VO=VO+.18*verb(VO,1.2,1.0)[:N]   # a touch of cinematic space
denv=lfilter([1-np.exp(-1/(.1*SR))],[1,-np.exp(-1/(.1*SR))],(np.abs(VO)>.02).astype(float))
mix=M*(1-.6*np.clip(denv*1.5,0,1))[:,None]*.9+FX*(1-.35*np.clip(denv,0,1))[:,None]*.85+np.stack([VO,VO],1)*1.45
fo=int(.8*SR); mix[-fo:]*=np.linspace(1,0,fo)[:,None]
mix=np.tanh(mix*1.25)/np.tanh(1.25); mix*=.92/np.max(np.abs(mix))
with wave.open(name+'.wav','wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype('<i2').tobytes())
print('ok',DUR)
