"""Application Configuration"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = True

    # Database Settings
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "poker_game"
    

    # Game Settings
    small_blind: int = 5
    big_blind: int = 10
    default_starting_chips: int = 1000

    # Admin
    admin_token: str = "ac10010362cbef72a8c76418d8369505321a6541230784ff1390bba348bcd131"

    # Database Reset on Startup (for testing)
    reset_db_on_startup: bool = False

    @property
    def database_url(self) -> str:
        """Construct database URL from components"""
        return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
