import numpy as np, json, sys, wave
name=sys.argv[1]; J=json.load(open(name+'.cues.json')); DUR=J['dur']+0.5; SR=48000
N=int(DUR*SR); L=np.zeros(N); R=np.zeros(N); rng=np.random.default_rng(7)
t_all=np.arange(N)/SR
def add(sig,t,gain=1.0,pan=0.0):
    i=int(t*SR); n=min(len(sig),N-i)
    if n<=0: return
    L[i:i+n]+=sig[:n]*gain*(1-max(pan,0)); R[i:i+n]+=sig[:n]*gain*(1+min(pan,0))
def env(n,a,d):
    e=np.ones(n); ai=int(a*SR); e[:ai]=np.linspace(0,1,ai) if ai else 1
    return e*np.exp(-np.arange(n)/SR/d)
def lp(x,a):  # one-pole lowpass, a in (0,1)
    y=np.empty_like(x); s=0.
    for i in range(len(x)): s+=a*(x[i]-s); y[i]=s
    return y
def lpv(x,alist):
    y=np.empty_like(x); s=0.
    for i in range(len(x)): s+=alist[i]*(x[i]-s); y[i]=s
    return y
# --- music: 118 bpm, A minor progression Am F C G
BPM=118; beat=60/BPM; bar=beat*4
chords=[[57,60,64],[53,57,60],[48,52,55],[55,59,62]]
bass=[45,41,48,43]
f=lambda m:440*2**((m-69)/12)
music_start=0.0; full_start=13.3  # beat drops at logo reveal
def saw(freq,n):
    ph=(np.arange(n)*freq/SR)%1; return 2*ph-1
# pad throughout
padlen=int(bar*SR)
t=0; k=0
while t<DUR:
    n=min(padlen,N-int(t*SR))
    if n<=0: break
    s=np.zeros(n)
    for m in chords[k%4]:
        for det in (-0.08,0.08): s+=saw(f(m+12)*(1+det/100*3),n)
    s=lp(s,0.035)*0.05
    e=np.minimum(1,np.minimum(np.arange(n)/(0.25*SR),(n-np.arange(n))/(0.25*SR)))
    add(s*e,t,1.0); t+=bar; k+=1
# drums
kick_n=int(.35*SR); tk=np.arange(kick_n)/SR
kick=np.sin(2*np.pi*(45*tk+ (110/18)*(1-np.exp(-tk*18))))*np.exp(-tk*9)
hat=rng.standard_normal(int(.05*SR)); hat=np.diff(np.concatenate([[0],hat]))*np.exp(-np.arange(len(hat))/SR/0.012)
clap=rng.standard_normal(int(.2*SR)); clap=np.diff(np.concatenate([[0],clap]))*np.exp(-np.arange(len(clap))/SR/0.06)
t=0; i=0
while t<DUR-0.3:
    b=i%4; half=t>=5.85  # hats + soft kick from google scene
    if t>=full_start or (half and b==0): add(kick,t,0.55 if t>=full_start else 0.3)
    if t>=full_start and b in (1,3): add(clap,t,0.12,0.1)
    if half: add(hat,t+beat/2,0.07,-0.3)
    if t>=full_start: add(hat,t,0.04,0.3)
    # bass
    if t>=full_start:
        bn=int(beat*SR*0.9); tb=np.arange(bn)/SR
        m=bass[int(t//bar)%4]; bs=np.sin(2*np.pi*f(m-12)*tb)+0.3*np.sin(2*np.pi*f(m)*tb)
        add(bs*np.exp(-tb*3)*np.minimum(1,tb*200),t,0.22)
    t+=beat; i+=1
# --- sfx
def whoosh(dur=.6):
    n=int(dur*SR); x=rng.standard_normal(n); tt=np.arange(n)/n
    a=0.02+0.35*np.sin(np.pi*tt)**2
    y=lpv(x,a)-lpv(x,a*0.3)
    return y*np.sin(np.pi*tt)**1.5*0.9
def hit():
    n=int(.5*SR); tt=np.arange(n)/SR
    return (np.sin(2*np.pi*(55*tt+60*(1-np.exp(-tt*25))/25))*np.exp(-tt*6)*0.8 + lp(rng.standard_normal(n),0.2)*np.exp(-tt*20)*0.5)
def impact():
    n=int(2.2*SR); tt=np.arange(n)/SR
    boom=np.sin(2*np.pi*(38*tt+80*(1-np.exp(-tt*12))/12))*np.exp(-tt*1.6)
    return boom*0.9+lp(rng.standard_normal(n),0.08)*np.exp(-tt*3)*0.6
def riser(d=.45):
    n=int(d*SR); tt=np.arange(n)/n; x=rng.standard_normal(n)
    return lpv(x,0.01+0.5*tt**2)*tt**2*1.2
def click():
    n=int(.03*SR); tt=np.arange(n)/SR
    return (np.sin(2*np.pi*2400*tt)*0.5+rng.standard_normal(n)*0.4)*np.exp(-tt*300)
def key():
    n=int(.04*SR); tt=np.arange(n)/SR
    return (rng.standard_normal(n)*0.5+np.sin(2*np.pi*1600*tt)*0.2)*np.exp(-tt*180)
def pop(fr=880):
    n=int(.12*SR); tt=np.arange(n)/SR
    return np.sin(2*np.pi*fr*tt*(1+tt*4))*np.exp(-tt*35)
def swell():
    n=int(2.5*SR); tt=np.arange(n)/SR
    s=sum(np.sin(2*np.pi*f(m)*tt) for m in (69,72,76,81))
    return s*np.minimum(1,tt/1.2)*np.exp(-np.maximum(0,tt-1.2)*2)*0.08
tick_i=0
for tm,ty in J['cues']:
    if ty=='whoosh': add(whoosh(),tm-0.2,0.5, rng.uniform(-.4,.4))
    elif ty=='swoosh': add(whoosh(.8),tm-0.3,0.45)
    elif ty=='hit': add(hit(),tm,0.55)
    elif ty=='impact': add(impact(),tm,0.8); add(riser(),tm-0.45,0.35)
    elif ty=='riser': add(riser(.4),tm,0.3)
    elif ty=='click': add(click(),tm,0.7)
    elif ty=='key': add(key(),tm,0.35, rng.uniform(-.2,.2))
    elif ty=='pop': add(pop(700),tm,0.18)
    elif ty=='tick': add(pop(1100+ (tick_i%5)*110),tm,0.12); tick_i+=1
    elif ty=='count': pass
    elif ty=='swell': add(swell(),tm,1.0)
# master: fades + soft limit
fade=np.ones(N); fi=int(0.3*SR); fo=int(1.5*SR); fade[:fi]=np.linspace(0,1,fi); fade[-fo:]=np.linspace(1,0,fo)
out=np.stack([L,R],1)*fade[:,None]
out=np.tanh(out*1.4)/np.tanh(1.4); out*=0.89/np.max(np.abs(out))
with wave.open(name+'.wav','wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype('<i2').tobytes())
print('ok',DUR)
