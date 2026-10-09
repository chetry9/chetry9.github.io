import numpy as np, librosa, json
d=json.load(open('synth.json'));text=open('script.txt',encoding='utf-8').read()
s=np.load('synth.npy').astype(np.float32)/32768; s=librosa.resample(s,orig_sr=d['sr'],target_sr=16000)
r=np.fromfile('../video/voice.raw',np.int16).astype(np.float32)/32768
def feat(x):
    m=librosa.feature.mfcc(y=x,sr=16000,n_mfcc=20,hop_length=160,n_fft=512)[1:]
    m=(m-m.mean(1,keepdims=True))/(m.std(1,keepdims=True)+1e-6)
    e=librosa.feature.rms(y=x,hop_length=160,frame_length=512)[0]
    e=librosa.amplitude_to_db(e,ref=np.max);e=(e-e.mean())/e.std()
    n=min(m.shape[1],len(e));return np.vstack([m[:,:n],2.0*e[None,:n]])
A=feat(s);B=feat(r)
D,wp=librosa.sequence.dtw(X=A,Y=B,metric='cosine',step_sizes_sigma=np.array([[1,1],[0,1],[1,0]]),weights_add=np.array([0,1,1]))
wp=wp[::-1]
m={}
for i,j in wp:
    m.setdefault(i,j)
def map_t(t):
    i=int(t*100);i=min(i,A.shape[1]-1)
    while i not in m: i-=1
    return m[i]/100
out=[]
for w in d['words']:
    # pos is char index in utf-8? test
    out.append((map_t(w['t']),w['t'],w['pos'],w['len']))
b=text.encode('utf-8')
for rt,st,p,l in out:
    print(f"{rt:6.2f} (syn {st:6.2f}) {text[p:p+l] if p<len(text) else '?'}")
json.dump(out,open('aligned.json','w'))
