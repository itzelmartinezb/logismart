import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    database: str = os.getenv("MONGODB_DATABASE", "logismart")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    llm_timeout: int = int(os.getenv("LLM_TIMEOUT", "60"))
    simulation_mode: bool = os.getenv("SIMULATION_MODE", "true").lower() in {"1", "true", "si", "sí", "yes"}

settings = Settings()
