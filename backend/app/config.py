import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SIEM Analytics Engine"
    API_V1_STR: str = "/api/v1"
    
    # Database configuration
    # Default MySQL connection or fallback to SQLite if MySQL is not reachable
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "siem_db")
    
    # Force SQLite if set or fallback on connection failure
    USE_SQLITE: bool = os.getenv("USE_SQLITE", "false").lower() in ("true", "1", "yes")
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", "siem_local.db")
    
    # Auth JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "siem_super_secret_jwt_key_2026_change_in_prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours

    # Detection engine settings
    DETECTION_INTERVAL_SECONDS: int = 10
    ML_SCORING_INTERVAL_SECONDS: int = 30

    @property
    def DATABASE_URL(self) -> str:
        if self.USE_SQLITE:
            return f"sqlite:///{self.SQLITE_PATH}"
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        case_sensitive = True

settings = Settings()
