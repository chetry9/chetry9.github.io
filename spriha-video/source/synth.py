import ctypes as C, numpy as np, json, sys
import espeakng_loader as E
lib=C.CDLL(E.get_library_path())
class EV(C.Structure):
    _fields_=[('type',C.c_int),('uid',C.c_uint),('text_position',C.c_int),('length',C.c_int),('audio_position',C.c_int),('sample',C.c_int),('user_data',C.c_void_p),('id',C.c_char*8)]
CB=C.CFUNCTYPE(C.c_int,C.POINTER(C.c_short),C.c_int,C.POINTER(EV))
SR=lib.espeak_Initialize(2,500,E.get_data_path().encode(),0)
samples=[];events=[]
def cb(wav,n,ev):
    if n>0: samples.append(np.ctypeslib.as_array(wav,(n,)).copy())
    i=0
    while ev[i].type!=0:
        if ev[i].type==1: events.append((ev[i].text_position,ev[i].length,ev[i].audio_position))
        i+=1
    return 0
cbf=CB(cb);lib.espeak_SetSynthCallback(cbf)
lib.espeak_SetVoiceByName(b"bn")
lib.espeak_SetParameter(1,165,0)  # rate wpm
text=open('script.txt',encoding='utf-8').read()
b=text.encode('utf-8')
lib.espeak_Synth(C.c_char_p(b),len(b)+1,0,0,0,0x01|0x100000,None,None)  # espeakCHARS_UTF8
lib.espeak_Synchronize()
wav=np.concatenate(samples);np.save('synth.npy',wav)
# text_position is 1-based char index
words=[]
for tp,ln,ap in events:
    words.append({'pos':tp-1,'len':ln,'t':ap/1000})
json.dump({'sr':SR,'words':words},open('synth.json','w'),ensure_ascii=False)
print(SR,len(wav)/SR,len(words))
