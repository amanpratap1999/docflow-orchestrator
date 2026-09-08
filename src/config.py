import os
from pydantic import BaseModel

class Settings(BaseModel):
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8003"))
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./workflow.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    AUTO_APPROVE_CONFIDENCE_THRESHOLD: float = float(os.getenv("AUTO_APPROVE_CONFIDENCE_THRESHOLD", "0.90"))
    INVOICE_AUTO_APPROVE_MAX_AMOUNT: float = float(os.getenv("INVOICE_AUTO_APPROVE_MAX_AMOUNT", "1000.00"))
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

settings = Settings()
