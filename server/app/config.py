"""
Configuration centrale de l'application SIGMA.
Toutes les valeurs sensibles/variables viennent des variables d'environnement (.env).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base de données
    DATABASE_URL: str = "postgresql+psycopg2://sigma:sigma_password@db:5432/sigma"

    # Sécurité
    SECRET_KEY: str = "change-this-secret-key-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Seed (premier démarrage)
    SEED_ORG_NAME: str = "Mon Établissement"
    SEED_ADMIN_EMAIL: str = "admin@sigma.local"
    SEED_ADMIN_PASSWORD: str = "Admin123!"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
