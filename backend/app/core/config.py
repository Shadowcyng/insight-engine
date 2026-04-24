from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # This is our Contract. If these are missing from .env, 
    # the app will crash immediately with a clear error.
    PROJECT_NAME :str = "InsightEngine"
    DATABASE_URL :str
    REDIS_URL :str = "redis://localhost:6379/0"
    ENVIRONMENT: str = "development"
    # Security (We'll use this later for JWT)
    SECRET_KEY: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    AI_API_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES : int = 15
    REFRESH_TOKEN_EXPIRE_DAYS :int = 7
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()


