import json, time
from ollama import Client
from pydantic import ValidationError
from app.models.schemas import LLMIncidentResult

SYSTEM = """Eres un clasificador de incidentes de un centro logístico. Responde ÚNICAMENTE JSON válido con exactamente estas claves: categoria, prioridad, entidades, resumen. prioridad solo puede ser BAJA, MEDIA, ALTA o CRITICA. No inventes entidades; si no aparecen, usa []."""

class LLMService:
    def __init__(self, host, model, timeout=60):
        self.model=model
        self.client=Client(host=host, timeout=timeout)

    def classify(self, correo, retries=1):
        prompt=f"{SYSTEM}\n\nCorreo:\n{correo}"
        last=None
        for intento in range(retries+1):
            t=time.perf_counter()
            try:
                r=self.client.chat(model=self.model, messages=[{"role":"system","content":SYSTEM},{"role":"user","content":correo}], format="json")
                raw=r["message"]["content"]
                parsed=LLMIncidentResult.model_validate_json(raw)
                return parsed, raw, time.perf_counter()-t, None
            except (Exception, ValidationError) as e:
                last=e
                if intento < retries:
                    continue
        return None, "", time.perf_counter()-t, last

    def explain(self, question, context):
        if not context:
            return "no tengo información"
        system="Responde exclusivamente con la información del contexto. Si la respuesta no está sustentada por el contexto, responde exactamente: no tengo información. Cita al final los IDs de los registros usados."
        r=self.client.chat(model=self.model, messages=[{"role":"system","content":system},{"role":"user","content":f"Pregunta: {question}\nContexto MongoDB:\n{json.dumps(context, default=str, ensure_ascii=False)}"}])
        return r["message"]["content"]
