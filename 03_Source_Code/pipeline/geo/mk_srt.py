import json,re,sys
txt,tim,out=sys.argv[1:4]
L=open(txt).read().split(" [pause] "); T=json.load(open(tim))
f=lambda s:"%02d:%02d:%02d,%03d"%(s//3600,s%3600//60,int(s%60),round((s-int(s))*1000)%1000)
with open(out,"w") as o:
    for i,(l,(a,b)) in enumerate(zip(L,T)):
        o.write(f"{i+1}\n{f(a)} --> {f(b+0.25)}\n{re.sub(r'\[[^\]]*\]','',l).strip()}\n\n")
