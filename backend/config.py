import os 
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

class Config: 
        SQLALCHEMY_DATABASE_URI = os.getenv(
                "DATABASE_URL"
        )

        SQLALCHEMY_TRACK_MODIFICATIONS = False

        JWT_SECRET_KEY = os.getenv(
                "JWT_SECRET_KEY"
        )

        JWT_ACCESS_TOKEN_EXPIRES = timedelta(
                minutes=int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "5"))
        )