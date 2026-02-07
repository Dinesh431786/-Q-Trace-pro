"""
Application configuration and settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "Q-Trace Pro"
    VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API Settings
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://qtrace-pro.com"
    ]
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/qtrace")
    
    # Redis Cache
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    CACHE_TTL: int = 3600  # 1 hour
    
    # Analysis Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_ANALYSIS_TIME: int = 300  # 5 minutes
    CONCURRENT_ANALYSES: int = 10
    
    # ML Settings
    ML_MODEL_PATH: str = "/app/models"
    ML_BATCH_SIZE: int = 32
    ML_MAX_SEQUENCE_LENGTH: int = 512
    USE_GPU: bool = os.getenv("USE_GPU", "False").lower() == "true"
    
    # Quantum Analysis
    QUANTUM_BACKEND: str = "cirq"  # Options: cirq, qiskit, pennylane
    QUANTUM_MAX_QUBITS: int = 20
    QUANTUM_SIMULATION_SHOTS: int = 1000
    
    # External Tools
    SEMGREP_PATH: str = os.getenv("SEMGREP_PATH", "semgrep")
    BANDIT_PATH: str = os.getenv("BANDIT_PATH", "bandit")
    
    # Monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    PROMETHEUS_PORT: int = 9090
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Storage
    UPLOAD_DIR: str = "/app/uploads"
    REPORTS_DIR: str = "/app/reports"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()