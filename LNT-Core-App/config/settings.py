import os

class Settings:
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key")

settings = Settings()
