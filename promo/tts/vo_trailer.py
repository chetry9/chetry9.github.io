import json,sys,numpy as np,soundfile as sf,librosa
from scipy.signal import butter,sosfilt,lfilter
from kokoro_onnx import Kokoro
k=Kokoro('kokoro-v1.0.onnx','voices-v1.0.bin')
voice,lines,out,semi=sys.argv[1],json.load(open(sys.argv[2])),sys.argv[3],float(sys.argv[4])
SR=24000
def shelf_low(x,fc=180,g=4.0):  # boost lows by mixing a lowpassed copy
    lo=sosfilt(butter(2,fc,'low',fs=SR,output='sos'),x); return x+lo*(10**(g/20)-1)
def presence(x): return x+0.22*sosfilt(butter(2,[2200,5200],'bandpass',fs=SR,output='sos'),x)
def comp(x,th=.18,ratio=3.5):
    env=lfilter([1-np.exp(-1/(.008*SR))],[1,-np.exp(-1/(.008*SR))],np.abs(x))
    g=np.where(env>th,(th+(env-th)/ratio)/np.maximum(env,1e-6),1.0); return x*g
for i,(_,_,text,spd) in enumerate(lines):
    a,sr=k.create(text,voice=voice,speed=spd*0.9,lang='en-us' if voice[0]=='a' else 'en-gb')
    nz=np.where(np.abs(a)>0.01)[0]; a=a[max(0,nz[0]-240):nz[-1]+3600]
    if semi: a=librosa.effects.pitch_shift(a.astype(np.float32),sr=sr,n_steps=semi,bins_per_octave=24)
    a=sosfilt(butter(2,70,'high',fs=sr,output='sos'),a)
    a=shelf_low(a); a=presence(a); a=comp(a); a=np.tanh(a*1.6)/1.6
    a*=0.9/np.max(np.abs(a))
    sf.write(f'{out}_{i:02d}.wav',a,sr); print(i,round(len(a)/sr,2),text)
