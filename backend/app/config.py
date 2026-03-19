from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    naver_client_id: str = ""
    naver_client_secret: str = ""
    dart_api_key: str = ""
    anthropic_api_key: str = ""
    database_url: str = ""  # postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    batch_interval_hours: int = 24

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
