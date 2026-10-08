from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict

class LLMIncidentResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    categoria: str
    prioridad: Literal["BAJA", "MEDIA", "ALTA", "CRITICA"]
    entidades: list[str] = Field(default_factory=list)
    resumen: str

class IncidentRecord(BaseModel):
    correo_original: str
    clasificacion: LLMIncidentResult
    datos_extraidos: dict[str, Any] = Field(default_factory=dict)
    estado: Literal["nuevo", "en_atencion", "cerrado"] = "nuevo"
    fecha: datetime = Field(default_factory=datetime.now)

class AccessDecision(BaseModel):
    P: bool
    Q: bool
    R: bool
    S: bool
    A: bool
    E: bool
    reglas_nuevas: dict[str, bool]
    resultado: str
    explicacion: list[str]
