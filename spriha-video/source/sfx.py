import numpy as np, wave
SR=44100; D=58.0; N=int(SR*D); t=np.arange(N)/SR
out=np.zeros((N,2))
def lp(x,a):  # one-pole lowpass
    y=np.zeros_like(x); s=0.0; a=np.broadcast_to(a,x.shape)
    for i in range(len(x)): s+=a[i]*(x[i]-s); y[i]=s
    return y
rng=np.random.default_rng(1)
# --- music bed: chords, bpm 100, bar=2.4s ---
def note(f): return 440*2**((f-69)/12)
prog=[[57,60,64,69],[53,57,60,65],[48,52,55,60],[55,59,62,67]]  # Am F C G
bar=2.4
pad=np.zeros(N)
for b in range(int(D/bar)+1):
    s=int(b*bar*SR); e=min(N,int((b+1)*bar*SR)+SR//2)
    if s>=N: break
    tt=np.arange(e-s)/SR; env=np.minimum(1,tt/0.6)*np.exp(-tt*0.35)
    for m in prog[b%4]:
        f=note(m)
        pad[s:e]+=env*(np.sin(2*np.pi*f*tt)+0.3*np.sin(2*np.pi*2*f*tt+0.3)+0.15*np.sin(2*np.pi*f*1.003*tt))*0.05
    # bass
    f=note(prog[b%4][0]-12); pad[s:e]+=env*np.sin(2*np.pi*f*tt)*0.12
# pulse pluck 8ths after 6.29s
beat=60/100
plk=np.zeros(N)
k=0; tt0=6.29
while tt0<D:
    s=int(tt0*SR); L=int(0.25*SR)
    if s+L<N:
        tt=np.arange(L)/SR; b=int(tt0/bar)%4; m=prog[b][(k%3)+1]+12
        plk[s:s+L]+=np.sin(2*np.pi*note(m)*tt)*np.exp(-tt*18)*0.05
    # kick on beats
    if k%2==0 and s+L<N:
        tt=np.arange(L)/SR; plk[s:s+L]+=np.sin(2*np.pi*(50+80*np.exp(-tt*30))*tt)*np.exp(-tt*12)*0.22
    tt0+=beat/2; k+=1
music=pad+plk
# hook section: tense low drone instead of pulse
hook=t<6.29
drone=np.sin(2*np.pi*55*t)*0.10+np.sin(2*np.pi*58.3*t)*0.06
music=np.where(hook, drone+pad*0.4, music)
# ducking-ish fades
music*=np.minimum(1,t/0.3)*np.clip((D-t)/2.5,0,1)
out+=np.stack([music,music],1)*0.9
# --- whooshes ---
def whoosh(at,dur=0.6,g=0.35):
    s=int((at-dur*0.7)*SR); L=int(dur*SR)
    if s<0: L+=s; s=0
    n=rng.standard_normal(L); tt=np.arange(L)/L
    env=np.sin(np.pi*tt)**2
    y=lp(n,0.04+0.25*np.sin(np.pi*tt))*env*g*3
    out[s:s+L,0]+=y*(1-tt*0.6); out[s:s+L,1]+=y*(0.4+tt*0.6)
def impact(at,g=0.6):
    s=int(at*SR); L=int(1.2*SR); tt=np.arange(L)/SR
    y=np.sin(2*np.pi*(40+120*np.exp(-tt*20))*tt)*np.exp(-tt*4)*g
    y+=lp(rng.standard_normal(L),0.2)*np.exp(-tt*25)*g*0.8
    out[s:s+L]+=np.stack([y,y],1)
def ding(at,f=1318.5,g=0.12):
    s=int(at*SR); L=int(0.8*SR); tt=np.arange(L)/SR
    y=(np.sin(2*np.pi*f*tt)+0.5*np.sin(2*np.pi*f*2*tt))*np.exp(-tt*6)*g
    out[s:s+L]+=np.stack([y,y],1)
for a in [0.02,2.31,3.79]: impact(a,0.55)
impact(6.29,0.5); whoosh(6.29,0.8,0.4)
impact(10.6,0.45); whoosh(10.85,1.0,0.3); ding(11.4,1046.5,0.14); ding(11.55,1568,0.10)
for a in [13.5,17.4,18.55,20.25,22.19,23.0,24.0,25.77,26.75,28.57,36.25,37.35,45.35]: whoosh(a,0.5,0.22)
impact(36.05,0.45); ding(33.9,1760,0.1)
whoosh(40.65,0.9,0.45); impact(40.65,0.7); ding(40.75,1318.5,0.14); ding(40.9,1975,0.1)
ding(7.75,1318.5,0.12); ding(54.6,1568,0.12); impact(50.2,0.35)
out=np.tanh(out*1.1)*0.9
w=wave.open('bed.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
