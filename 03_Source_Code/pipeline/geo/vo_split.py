"""Split a full-script VO at its [pause] silences (digital silence runs) -> source spans + beat timing.
usage: python3 vo_split.py voice.mp3 N out_timing.json [target] [override 'old:new,...']"""
import json, subprocess, sys
import numpy as np
SR=16000
src,n,out=sys.argv[1],int(sys.argv[2]),sys.argv[3]
target=float(sys.argv[4]) if len(sys.argv)>4 else 60.0
ovr=dict((float(a),float(b)) for a,b in (p.split(":") for p in sys.argv[5].split(","))) if len(sys.argv)>5 and sys.argv[5] else {}
x=np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",src,"-ac","1","-ar",str(SR),"-f","f32le","-"],capture_output=True,check=True).stdout,np.float32)
hop=SR//100
db=20*np.log10(np.array([np.sqrt(np.mean(x[i:i+hop]**2)+1e-12) for i in range(0,len(x)-hop,hop)]))
on=db>-60; idx=np.where(on)[0]; s0,s1=idx[0],idx[-1]+1
q=db<-70; runs=[]; i=s0
while i<s1:
    if q[i]:
        j=i
        while j<s1 and q[j]: j+=1
        runs.append((i,j)); i=j
    else: i+=1
runs=sorted(sorted(runs,key=lambda r:r[0]-r[1])[:n-1])
cuts=[]
for a,b in runs:
    t=round(a/100,2)
    hit=[k for k in ovr if abs(k-t)<0.15]
    if hit:
        c=int(ovr[hit[0]]*100); cuts.append((c,c+1))
    else: cuts.append((a,b))
cuts.sort()
# trim each span to speech (-55dB) edges
spans=[]; st=s0
for a,b in cuts+[(s1,s1)]:
    e=a
    while e>st and db[e-1]<-55: e-=1
    s=st
    while s<e and db[s]<-55: s+=1
    spans.append((s/100,e/100)); st=b
d=[q-p for p,q in spans]
lead,tail,gap=0.25,1.3,0.35
natural=lead+sum(d)+gap*(n-1)+tail
gap+=min(0.9,max(0,target-natural)/max(1,n-1))
t,timing=lead,[]
for k in range(n):
    timing.append([round(t,3),round(t+d[k],3)]); t+=d[k]+gap
json.dump(timing,open(out,"w"))
json.dump([[round(p,3),round(q,3)] for p,q in spans],open(out.replace(".json","_src.json"),"w"))
print("lines",[round(v,2) for v in d]); print("total",round(timing[-1][1]+tail,2),"gap",round(gap,2))
