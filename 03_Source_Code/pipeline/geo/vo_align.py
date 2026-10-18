"""Align a full-script VO to N beat lines using silence gaps + char-length DP.
usage: python3 vo_align.py voice.mp3 beats.txt out_timing.json [target]"""
import json, subprocess, sys, re
import numpy as np
SR=16000
src, btxt, out = sys.argv[1], sys.argv[2], sys.argv[3]
target = float(sys.argv[4]) if len(sys.argv) > 4 else 60.0
lines=[l for l in open(btxt).read().split(" [pause] ")]
L=np.array([len(re.sub(r"\[[^\]]*\]","",l).strip()) for l in lines],float)
n=len(lines)
raw=subprocess.run(["ffmpeg","-v","error","-i",src,"-ac","1","-ar",str(SR),"-f","f32le","-"],capture_output=True,check=True).stdout
x=np.frombuffer(raw,np.float32); hop=SR//100
e=np.array([np.sqrt(np.mean(x[i:i+hop]**2)+1e-12) for i in range(0,len(x)-hop,hop)])
db=20*np.log10(e); on=db>max(-45,db.max()-38)
idx=np.where(on)[0]; s0,s1=idx[0],idx[-1]+1
# silence runs inside speech
gaps=[]; i=s0
while i<s1:
    if not on[i]:
        j=i
        while j<s1 and not on[j]: j+=1
        if j-i>=12: gaps.append((i,j))
        i=j
    else: i+=1
G=len(gaps)
# DP over choosing n-1 gaps
starts=[s0]+[g[1] for g in gaps]; ends=[g[0] for g in gaps]+[s1]
tot=(s1-s0)-sum(g[1]-g[0] for g in gaps)
rate=L.sum()/tot  # chars per frame approx (ignoring kept gaps)
INF=1e18
# seg from gap a (start index a in starts) to gap b (end index b in ends), a<=b
dp=np.full((n+1,G+2),INF); bk=np.zeros((n+1,G+2),int)
dp[0][0]=0
def cost(k,a,b):
    d=ends[b]-starts[a]
    exp=L[k]/rate
    return ((d-exp)/max(exp,60))**2
for k in range(n):
    for a in range(G+1):
        if dp[k][a]>=INF: continue
        for b in range(a,G+1):
            if k==n-1 and b!=G: continue
            if k<n-1 and b==G: continue
            gl=(gaps[b][1]-gaps[b][0]) if b<G else 0
            c=dp[k][a]+cost(k,a,b)-0.004*gl
            if c<dp[k+1][b+1]: dp[k+1][b+1]=c; bk[k+1][b+1]=a
segs=[]; b=G+1
for k in range(n,0,-1):
    a=bk[k][b]; segs.append((starts[a]/100,ends[b-1]/100)); b=a
segs=segs[::-1]
d=[q-p+0.08 for p,q in segs]
lead,tail,gap=0.25,1.3,0.35
natural=lead+sum(d)+gap*(n-1)+tail
gap+=min(0.9,max(0,target-natural)/max(1,n-1))
t,timing,src_spans=lead,[],[]
for k in range(n):
    timing.append([round(t,3),round(t+d[k],3)]); t+=d[k]+gap
json.dump(timing,open(out,"w"))
json.dump([[round(p,3),round(q+0.08,3)] for p,q in segs],open(out.replace(".json","_src.json"),"w"))
for k in range(n): print(f"{k:2d} {segs[k][0]:6.2f}-{segs[k][1]:6.2f} ({d[k]:.2f}s, exp {L[k]/rate/100:.2f}) {lines[k][:40]}")
print("total",round(timing[-1][1]+tail,2),"gap",round(gap,2))
