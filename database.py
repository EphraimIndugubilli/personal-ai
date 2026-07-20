import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, ".env")

# 1. First attempt: Standard load
load_dotenv(env_path)
DATABASE_URL = os.getenv("postgresql://neondb_owner:npg_3pNPtdOVL9Ug@ep-little-unit-awp830u3.c-12.us-east-1.aws.neon.tech/neondb?sslmode=require")

# 2. Fallback: If standard fails due to hidden Windows encoding/BOM, parse manually
if not DATABASE_URL and os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8-sig") as f:  # 'utf-8-sig' strips hidden Windows BOMs automatically
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.strip().split("=", 1)
                if key.strip() == "DATABASE_URL":
                    DATABASE_URL = value.strip().strip('"').strip("'")
                    os.environ["DATABASE_URL"] = DATABASE_URL

# 3. Final sanity check
if not DATABASE_URL:
    raise ValueError("CRITICAL ERROR: DATABASE_URL is missing or empty in your .env file!")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()