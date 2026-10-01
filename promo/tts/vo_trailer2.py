import json,sys,numpy as np,soundfile as sf
from scipy.signal import butter,sosfilt,lfilter
from kokoro_onnx import Kokoro
k=Kokoro('kokoro-v1.0.onnx','voices-v1.0.bin')
voice,lines,out=sys.argv[1],json.load(open(sys.argv[2])),sys.argv[3]
SR=24000
def biquad(kind,f0,gdb,q=0.8):
    A=10**(gdb/40); w=2*np.pi*f0/SR; al=np.sin(w)/(2*q); c=np.cos(w)
    if kind=='peak':
        b=[1+al*A,-2*c,1-al*A]; a=[1+al/A,-2*c,1-al/A]
    elif kind=='low':
        s=2*np.sqrt(A)*al
        b=[A*((A+1)-(A-1)*c+s),2*A*((A-1)-(A+1)*c),A*((A+1)-(A-1)*c-s)]; a=[(A+1)+(A-1)*c+s,-2*((A-1)+(A+1)*c),(A+1)+(A-1)*c-s]
    else:
        s=2*np.sqrt(A)*al
        b=[A*((A+1)+(A-1)*c+s),-2*A*((A-1)+(A+1)*c),A*((A+1)+(A-1)*c-s)]; a=[(A+1)-(A-1)*c+s,2*((A-1)-(A+1)*c),(A+1)-(A-1)*c-s]
    return np.array(b)/a[0],np.array(a)/a[0]
def eq(x,*args): b,a=biquad(*args); return lfilter(b,a,x)
def comp(x,th=.25,ratio=2.5):
    env=lfilter([1-np.exp(-1/(.012*SR))],[1,-np.exp(-1/(.012*SR))],np.abs(x))
    g=np.where(env>th,(th+(env-th)/ratio)/np.maximum(env,1e-6),1.0); return x*g
for i,(_,_,text,spd) in enumerate(lines):
    a,sr=k.create(text,voice=voice,speed=spd*0.95,lang='en-us' if voice[0]=='a' else 'en-gb')
    nz=np.where(np.abs(a)>0.01)[0]; a=a[max(0,nz[0]-240):nz[-1]+1200].astype(float)
    a=sosfilt(butter(2,80,'high',fs=sr,output='sos'),a)
    a=eq(a,'low',140,2.5); a=eq(a,'peak',380,-3.5,1.0); a=eq(a,'peak',3200,1.5,1.0); a=eq(a,'high',9000,2.0)
    a=comp(a); a*=0.95/np.max(np.abs(a))
    fade=np.ones(len(a)); n=int(.03*sr); fade[-n:]=np.linspace(1,0,n); a*=fade
    sf.write(f'{out}_{i:02d}.wav',a,sr); print(i,round(len(a)/sr,2),text)
