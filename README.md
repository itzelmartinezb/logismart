# LogiSmart - Proyecto integrador LLM + MongoDB

Proyecto basado en los siete scripts entregados en la práctica. La solución conserva las reglas originales y las transforma en una aplicación modular con persistencia MongoDB, Ollama, Pydantic y GUI Tkinter.

## 1. Arquitectura

- `app/config.py`: configuración por variables de entorno.
- `app/db/mongo.py`: conexión, CRUD, índices y agregación.
- `app/repositories/`: acceso a datos.
- `app/services/rules_engine.py`: lógica proposicional A/E + V/H y tabla de verdad.
- `app/services/llm_service.py`: Ollama y validación Pydantic.
- `app/services/classifier.py`: reglas + LLM + fallback + prioridad de seguridad.
- `app/ui/gui.py`: interfaz gráfica.
- `app/services/reports.py`: PDF/CSV/JSON.
- `seed.py`: datos de demostración, incluyendo 30 correos.

## 2. Instalación

1. Crear entorno: `python -m venv .venv`
2. Activarlo.
3. `pip install -r requirements.txt`
4. Copiar `.env.example` a `.env` y colocar la URI de MongoDB del alumno.
5. Instalar Ollama y descargar el modelo indicado: `ollama pull llama3.2`.
6. Ejecutar `python seed.py` para datos demo.
7. Ejecutar `python main.py`.

El primer ejercicio se ejecuta con `python -m app.p02primertutor_llm`.

## 3. Reglas

Originales:
- `A = P ∧ S ∧ ¬Q`
- `E = P ∧ (R ∨ Q)`

Nuevas:
- `V = P ∧ certificacion_vigente`
- `H = ¬R ∨ horario_seguro`
- Acceso seguro final: `A ∧ V ∧ H`

Justificación: un vehículo no debe autorizarse si la certificación ya no es vigente; además, los materiales peligrosos requieren horario seguro.

## 4. Clasificador híbrido

El LLM debe devolver exactamente:

```json
{"categoria":"...","prioridad":"BAJA|MEDIA|ALTA|CRITICA","entidades":[],"resumen":"..."}
```

Pydantic rechaza campos adicionales. Si falla la respuesta se reintenta una vez y después se usa `rules_classify`. Cuando reglas y LLM discrepan, se conserva la prioridad más alta y se marca `requiere_revision_humana`.

## 5. RAG

El asistente no recibe la pregunta directamente como conocimiento factual. Primero consulta MongoDB, arma un contexto y después lo entrega a Ollama. Si no existe contexto pertinente, responde `no tengo información`.

## 6. Datos demo y experimento

`seed.py` genera 30 correos etiquetados por reglas de referencia. Para el informe, deben conservar una copia de las etiquetas humanas y ejecutar la evaluación en su equipo con Ollama activo. El proyecto deja registrada latencia y coincidencia en `evaluaciones_llm`.

## 7. Riesgos éticos

Se incluyen cuatro riesgos propios: alucinaciones, sesgo por ortografía informal, privacidad de datos del conductor y dependencia excesiva de automatización. La matriz almacena probabilidad, impacto, puntaje inicial, mitigación y residual.

## 8. Entregables sugeridos

- Repositorio Git con este proyecto.
- Capturas de GUI y MongoDB Compass.
- Informe técnico: arquitectura, colecciones, prompts, experimento de 30 correos, matriz de confusión, latencia y análisis ético.
- Demostración en vivo.
