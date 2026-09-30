import json,sys,soundfile as sf,numpy as np
from kokoro_onnx import Kokoro
k=Kokoro('kokoro-v1.0.onnx','voices-v1.0.bin')
voice=sys.argv[1]; lines=json.load(open(sys.argv[2])); out=sys.argv[3]
res=[]
for i,(start,win,text,spd) in enumerate(lines):
    a,sr=k.create(text,voice=voice,speed=spd,lang='en-us')
    # trim silence
    nz=np.where(np.abs(a)>0.01)[0]; a=a[max(0,nz[0]-240):nz[-1]+2400]
    sf.write(f'{out}_{i:02d}.wav',a,sr); d=len(a)/sr
    res.append([start,win,round(d,2),text]); print(f'{i:2d} start {start:5.2f} win {win:4.2f} dur {d:4.2f} {"!!" if d>win else ""} {text}')
json.dump(res,open(out+'.json','w'))
