import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Force Python to find .env in the exact same folder
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# 2. Safely retrieve the URL from .env, WITH A DIRECT FALLBACK
# This ensures that if the .env file format is broken, the app still gets the URL.
DATABASE_URL = os.getenv("DATABASE_URL")

# 3. Allow Vercel to inspect the file during the build phase
if DATABASE_URL and str(DATABASE_URL).strip() != "":
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"connect_timeout": 10},
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None

Base = declarative_base()

def get_db():
    if not SessionLocal:
        raise ValueError(f"CRITICAL ERROR: DATABASE_URL is missing. Python strictly searched for .env at: {env_path}")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
