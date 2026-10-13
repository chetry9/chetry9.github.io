import numpy as np, wave
SR=44100; D=57.6; N=int(SR*D); OFF=0.3; c=lambda x:x+OFF
rng=np.random.default_rng(1)
def tt(d): return np.arange(int(SR*d))/SR
def lp(x,a):  # one-pole lowpass, a in (0,1)
    y=np.empty_like(x); s=0.0
    for i in range(len(x)): s+=a*(x[i]-s); y[i]=s
    return y
def place(buf,sig,t,g=1.0,pan=0.0):
    i=int(t*SR); j=min(len(buf),i+len(sig))
    if j<=i: return
    l=np.sqrt((1-pan)/2); r=np.sqrt((1+pan)/2)
    buf[i:j,0]+=sig[:j-i]*g*l; buf[i:j,1]+=sig[:j-i]*g*r
def env(n,a,r):
    e=np.ones(n); A=int(a*SR); R=int(r*SR)
    if A: e[:A]=np.linspace(0,1,A)
    if R: e[-R:]*=np.linspace(1,0,R)
    return e
nf=lambda f:440*2**((f-69)/12)
# ---------- MUSIC ----------
mus=np.zeros((N,2))
def pad(freqs,t0,d,g):
    x=tt(d); s=np.zeros_like(x)
    for f in freqs:
        for det in (-0.12,0.12):
            ff=nf(f+det); s+=np.sin(2*np.pi*ff*x)+0.3*np.sin(4*np.pi*ff*x)+0.12*np.sin(6*np.pi*ff*x)
    s*=env(len(x),0.6,0.8)/len(freqs)
    place(mus,s,t0,g,-0.2); place(mus,s,t0+0.012,g,0.2)
def pluck(f,t0,g,pan=0):
    x=tt(0.9); ff=nf(f)
    s=(np.sin(2*np.pi*ff*x)+0.5*np.sin(4*np.pi*ff*x)*np.exp(-x*9)+0.2*np.sin(6*np.pi*ff*x)*np.exp(-x*14))*np.exp(-x*5.5)
    s*=env(len(x),0.004,0.05); place(mus,s,t0,g,pan)
def kick(t0,g):
    x=tt(0.35); f=50+90*np.exp(-x*30); ph=2*np.pi*np.cumsum(f)/SR
    place(mus,np.sin(ph)*np.exp(-x*9),t0,g)
def bass(f,t0,d,g):
    x=tt(d); ff=nf(f); s=np.sin(2*np.pi*ff*x)+0.25*np.sin(4*np.pi*ff*x); s*=env(len(x),0.02,0.15); place(mus,s,t0,g)
beat=0.6
# Section A: tense/emotional  Am F Dm E  (2.4s each)
A=[[57,60,64],[53,57,60],[50,53,57],[52,56,59]]
t=0.0;k=0
while t<c(16.1)-0.1:
    ch=A[k%4]; d=min(2.4,c(16.1)-t); pad([x+12 for x in ch],t,d+0.4,0.10); bass(ch[0]-12,t,d,0.18)
    for b in range(4):
        if t+b*beat<c(16.1)-0.2: pluck(ch[b%3]+24,t+b*beat,0.05,(-1)**b*0.4)
    t+=2.4;k+=1
# Section B: hopeful  C G Am F
B=[[60,64,67],[55,59,62],[57,60,64],[53,57,60]]
t=c(16.45);k=0
while t<D-1.0:
    ch=B[k%4]; d=min(2.4,D-t); pad([x+12 for x in ch],t,d+0.4,0.11); bass(ch[0]-12,t,d,0.22)
    arp=[0,1,2,1,2,1,0,2]
    for b in range(8):
        tb=t+b*beat/2
        if tb<D-1.2: pluck(ch[arp[b]]+24,tb,0.06 if b%2==0 else 0.04,(-1)**b*0.35)
    if t>c(20.4):
        for b in range(4):
            if t+b*beat<D-1.5: kick(t+b*beat,0.35)
    t+=2.4;k+=1
# final sustained chord
pad([72,76,79,84],D-3.2,3.2,0.12); bass(48,D-3.2,3.0,0.2)
# ---------- SFX ----------
sfx=np.zeros((N,2))
def whoosh(d=0.5,bright=0.25):
    x=tt(d); n=rng.standard_normal(len(x)); e=np.sin(np.pi*np.clip(x/d,0,1))**2
    a=bright*(0.3+0.7*np.sin(np.pi*x/d)); y=np.empty_like(n); s=0.0
    for i in range(len(n)): s+=a[i]*(n[i]-s); y[i]=s
    return y*e*2.5
def pop(f=900):
    x=tt(0.12); fr=f*(1+2*np.exp(-x*60)); ph=2*np.pi*np.cumsum(fr)/SR
    return np.sin(ph)*np.exp(-x*35)
def ding(f=1568):
    x=tt(1.0); return (np.sin(2*np.pi*f*x)+0.4*np.sin(2*np.pi*f*2.01*x)+0.2*np.sin(2*np.pi*f*3*x))*np.exp(-x*5)
def thud():
    x=tt(0.5); f=45+120*np.exp(-x*25); ph=2*np.pi*np.cumsum(f)/SR
    n=lp(rng.standard_normal(len(x)),0.08)*np.exp(-x*20)
    return np.sin(ph)*np.exp(-x*7)+n*1.5
def riser(d):
    x=tt(d); n=rng.standard_normal(len(x)); y=np.empty_like(n); s=0.0; a=0.02+0.4*(x/d)**2
    for i in range(len(n)): s+=a[i]*(n[i]-s); y[i]=s
    tone=np.sin(2*np.pi*np.cumsum(200+800*(x/d)**2)/SR)*0.15
    return (y*2+tone)*(x/d)**1.5
def shimmer():
    s=np.zeros(int(SR*1.6))
    for i,f in enumerate([1047,1319,1568,2093,2637]):
        d=ding(f)*0.5; st=int(i*0.07*SR); s[st:st+len(d)]+=d[:len(s)-st]
    return s
def tick():
    x=tt(0.03); return rng.standard_normal(len(x))*np.exp(-x*300)
def ring():
    x=tt(0.9); g=(np.sin(2*np.pi*20*x)>0).astype(float)
    return (np.sin(2*np.pi*1300*x)+np.sin(2*np.pi*1700*x))*0.5*g*env(len(x),0.01,0.1)
def sparkle(d=1.2):
    s=np.zeros(int(SR*d))
    for i in range(40):
        f=2000+rng.random()*4000; p=pop(f)*0.3; st=int(rng.random()*(d-0.15)*SR); s[st:st+len(p)]+=p*(1-st/len(s))
    return s
for t,dur,g in [(0.0,0.45,0.30),(c(5.95),0.45,0.35),(c(7.4),0.4,0.3),(c(12.45),0.4,0.3),(c(20.15),0.55,0.3),(c(24.3),0.45,0.35),(c(33.95),0.45,0.3),(c(36.5),0.5,0.35),(c(40.95),0.5,0.35),(c(47.85),0.6,0.3)]:
    place(sfx,whoosh(dur),t,g)
for t,f in [(0.1,700),(c(3.1),760),(c(3.45),620),(c(6.05),520),(c(7.9),880),(c(8.65),700),(c(16.45),900),(c(20.95),880),(c(21.25),760),(c(22.3),820),(c(22.75),1000),(c(23.15),1100),(c(24.6),700),(c(31.9),760),(c(34.35),900),(c(37.25),640),(c(38.65),820),(c(39.35),900),(c(39.95),760),(c(45.25),820),(c(46.75),900),(c(48.35),700),(c(50.25),880),(c(51.45),760)]:
    place(sfx,pop(f),t,0.35)
for i,t in enumerate([c(24.9),c(28.2),c(31.1)]):
    place(sfx,whoosh(0.35,0.4),t,0.25,(-1)**i*0.5); place(sfx,ding([1319,1568,2093][i]),t+0.4,0.22)
place(sfx,thud(),c(10.45),0.9)
place(sfx,riser(2.0),c(14.1),0.35)
place(sfx,thud()*0.6,c(16.5),0.6)
place(sfx,shimmer(),c(16.55),0.35); place(sfx,whoosh(0.8,0.6),c(17.2),0.12)
place(sfx,ding(2093),c(18.2),0.15)
for k in range(int(3.0/0.5)): place(sfx,tick(),0.2+k*0.5,0.12)
place(sfx,sparkle(),c(34.35),0.6); place(sfx,sparkle(1.5),c(37.25),0.6)
place(sfx,thud()*0.5,c(37.2),0.5); place(sfx,thud()*0.5,c(41.4),0.5)
place(sfx,ring(),c(48.6),0.10); place(sfx,ring(),c(49.7),0.07)
place(sfx,pop(1500)*0.8,c(51.1),0.45)
place(sfx,shimmer(),c(51.45),0.2)
def save(fn,x):
    x=x/ max(1e-9,np.abs(x).max())*0.9
    w=wave.open(fn,'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x*32767).astype('<i2').tobytes()); w.close()
save('music.wav',mus); save('sfx.wav',sfx)
print('ok')
