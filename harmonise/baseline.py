import math,re
from collections import Counter
from harmonise.categories import LEXICON,VERSION

def features(text):
    words=re.findall(r'[a-z]+',text.lower());out=Counter('w:'+w for w in words)
    for word in words:
        padded='^'+word+'$'
        out.update('c:'+padded[i:i+3] for i in range(max(0,len(padded)-2)))
    return out

class Harmoniser:
    def __init__(self):
        docs={k:features(k+' '+v) for k,v in LEXICON.items()}
        df=Counter(t for d in docs.values() for t in d)
        self.idf={t:math.log((len(docs)+1)/(n+1))+1 for t,n in df.items()}
        self.docs={k:self.vector(d) for k,d in docs.items()}
    def vector(self,counts):
        v={t:(1+math.log(c))*self.idf[t] for t,c in counts.items() if t in self.idf}
        norm=math.sqrt(sum(x*x for x in v.values()))
        return {t:x/norm for t,x in v.items()} if norm else {}
    def propose(self,text,top=3):
        q=self.vector(features(text))
        ranked=sorted(({'category':k,'score':round(sum(v*q.get(t,0) for t,v in d.items()),6)} for k,d in self.docs.items()),key=lambda r:(-r['score'],r['category']))
        return {'method':'word_character_tfidf_cosine_baseline','version':VERSION,'candidates':ranked[:top],'requires_adjudication':True,'calibrated':False}
