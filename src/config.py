from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ponytail: default to relative paths within workspace for local-first zero-setup execution
    database_path: str = "data/leads.db"
    
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.1:8b-instruct-q4_K_M"
    
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    sender_name: str = "Garment Export Ops"
    
    dispatch_min_delay_seconds: int = 150
    dispatch_max_delay_seconds: int = 360
    dispatch_daily_limit: int = 25
    
    proxies_file: str = "data/proxies.txt"
    headless: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def resolved_database_path(self) -> Path:
        return Path(self.database_path).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
