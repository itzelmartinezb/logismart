import re
from app.services.llm_service import LLMService

PRIORITY_RANK={"BAJA":1,"MEDIA":2,"ALTA":3,"CRITICA":4}

def rules_classify(text):
    t=text.lower()
    if any(k in t for k in ["accidente","incendio","fuga","herido","explosivo"]): p="CRITICA"
    elif any(k in t for k in ["peligroso","robo","amenaza","intrusión","intrusion","choque"]): p="ALTA"
    elif any(k in t for k in ["peso","certificación","certificacion","acceso","retraso"]): p="MEDIA"
    else: p="BAJA"
    if any(k in t for k in ["peligroso","químico","quimico"]): c="materiales_peligrosos"
    elif any(k in t for k in ["peso","báscula","bascula"]): c="peso"
    elif any(k in t for k in ["acceso","placa","camión","camion"]): c="acceso"
    elif any(k in t for k in ["accidente","choque"]): c="accidente"
    else: c="general"
    entities=re.findall(r'\b(?:CAM|TRK)-?\d{2,4}\b', text, re.I)
    return {"categoria":c,"prioridad":p,"entidades":entities,"resumen":text.strip()[:180]}

def hybrid_classify(text, llm):
    reglas=rules_classify(text)
    llm_result, raw, latency, error=llm.classify(text)
    if llm_result is None:
        return reglas, {"origen":"reglas_fallback","requiere_revision_humana":True,"latencia":latency,"error":str(error)}
    llm_data=llm_result.model_dump()
    prioridad=max(reglas["prioridad"],llm_data["prioridad"],key=lambda x:PRIORITY_RANK[x])
    discrepancia=reglas["prioridad"]!=llm_data["prioridad"] or reglas["categoria"]!=llm_data["categoria"]
    final=dict(llm_data); final["prioridad"]=prioridad
    return final,{"origen":"hibrido","requiere_revision_humana":discrepancia,"reglas":reglas,"llm":llm_data,"raw":raw,"latencia":latency,"error":None}
