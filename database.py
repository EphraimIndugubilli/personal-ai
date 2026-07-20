import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# --- DEBUGGING ---
# This will print all available keys to your Render logs so we can see what's actually there
print("=== DEBUG: AVAILABLE ENV KEYS ===")
print(list(os.environ.keys()))
print("=================================")

DATABASE_URL = os.getenv("postgresql://neondb_owner:npg_p5QSzYd2wDtE@ep-autumn-sunset-avd8vs2h-pooler.c-11.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

if not DATABASE_URL:
    raise ValueError("CRITICAL ERROR: DATABASE_URL is missing or empty in the environment!")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()