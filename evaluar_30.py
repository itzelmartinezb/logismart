"""Experimento: reglas vs Ollama vs híbrido sobre 30 correos etiquetados."""
import csv, time, json
from collections import Counter, defaultdict
from app.config import settings
from app.services.llm_service import LLMService
from app.services.classifier import rules_classify, hybrid_classify

PRIORITIES=["BAJA","MEDIA","ALTA","CRITICA"]

def accuracy(y,p): return sum(a==b for a,b in zip(y,p))/len(y) if y else 0

def confusion(y,p):
    d={a:{b:0 for b in PRIORITIES} for a in PRIORITIES}
    for a,b in zip(y,p):
        if a in d and b in d[a]: d[a][b]+=1
    return d

with open("data/correos_30.csv",encoding="utf8",newline="") as f: rows=list(csv.DictReader(f))
llm=LLMService(settings.ollama_host,settings.ollama_model,settings.llm_timeout)
y=[r["prioridad_humana"] for r in rows]
pr=[]; pl=[]; ph=[]; lat=[]
for r in rows:
    t=time.perf_counter(); pr.append(rules_classify(r["correo"])["prioridad"]); rule_latency=time.perf_counter()-t
    res,raw,l,e=llm.classify(r["correo"])
    pl.append(res.prioridad if res else "BAJA")
    final,meta=hybrid_classify(r["correo"],llm); ph.append(final["prioridad"]); lat.append(meta.get("latencia",l))

report={
 "n":len(rows),"accuracy_reglas":accuracy(y,pr),"accuracy_llm":accuracy(y,pl),"accuracy_hibrido":accuracy(y,ph),
 "confusion_reglas":confusion(y,pr),"confusion_llm":confusion(y,pl),"confusion_hibrido":confusion(y,ph),
 "latencia_llm_promedio":sum(lat)/len(lat),"latencia_llm_min":min(lat),"latencia_llm_max":max(lat)
}
print(json.dumps(report,ensure_ascii=False,indent=2))
with open("reportes/experimento_30.json","w",encoding="utf8") as f: json.dump(report,f,ensure_ascii=False,indent=2)
