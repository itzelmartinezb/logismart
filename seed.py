from datetime import datetime, timedelta
from app.config import settings
from app.db.mongo import MongoDB
from app.services.rules_engine import evaluar_camion

emails=[
("Acceso", "CAM-101 tiene autorización y certificación vigente."),
("Peso", "CAM-102 llegó con peso excedido en báscula."),
("Peligroso", "CAM-103 transporta material peligroso."),
("Accidente", "Se reporta accidente en patio de maniobras."),
("General", "Se solicita información del acceso."),
("Peso", "La báscula detectó exceso de peso en CAM-104."),
("Acceso", "CAM-105 no aparece autorizado."),
("Peligroso", "Hay fuga de material químico en CAM-106."),
("General", "Retraso de proveedor en la entrada."),
("Accidente", "Choque entre unidades cerca de la puerta."),
]
emails=emails*3

db=MongoDB(settings.mongodb_uri,settings.database); ok,msg=db.connect(); print(msg)
if not ok: raise SystemExit(1)
for c in ["camiones","accesos","incidentes","riesgos_eticos","evaluaciones_llm"]: db.collection(c).delete_many({})
for i in range(1,11): db.create("camiones",{"placa":f"CAM-{100+i}","camion_id":i,"empresa":"LogiTrans","autorizacion":i%3!=0,"certificacion_conductor":True})
for i in range(10):
    d=evaluar_camion(True,i%4==1,i%5==0,True)
    d.update({"placa":f"CAM-{101+i}","marca_tiempo":datetime.now()-timedelta(days=i),"operador":"DEMO"}); db.create("accesos",d)
for i,(tipo,mail) in enumerate(emails):
    p="CRITICA" if tipo=="Accidente" else "ALTA" if tipo=="Peligroso" else "MEDIA" if tipo=="Peso" else "BAJA"
    cat=tipo.lower(); db.create("incidentes",{"correo_original":mail,"clasificacion":{"categoria":cat,"prioridad":p,"entidades":[f"CAM-{101+i%10}"],"resumen":mail},"datos_extraidos":{},"estado":"nuevo" if i%2 else "cerrado","fecha":datetime.now()-timedelta(days=i%21)})
risks=[
("LLM","Alucinaciones del LLM","Confiabilidad",3,4,"RAG con fuentes, JSON validado y fallback"),
("Clasificador","Sesgo en correos con ortografía informal","Sesgo",3,3,"Conjunto etiquetado diverso y revisión humana"),
("MongoDB","Privacidad de datos del conductor","Privacidad",2,5,"Minimización, roles y retención"),
("Automatización","Dependencia excesiva de la automatización","Supervisión",3,5,"Override humano y auditoría"),
]
for m,r,c,prob,imp,mit in risks: db.create("riesgos_eticos",{"modulo":m,"descripcion":r,"categoria":c,"probabilidad":prob,"impacto":imp,"puntaje_inicial":prob*imp,"mitigacion":mit,"riesgo_residual":max(1,(prob*imp)-5),"historico":[]})
print("Datos de demostración cargados.")
