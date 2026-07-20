import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load the environment variable safely
DATABASE_URL = os.getenv("postgresql://neondb_owner:npg_p5QSzYd2wDtE@ep-autumn-sunset-avd8vs2h-pooler.c-11.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

# Production-safe error check
if not DATABASE_URL or str(DATABASE_URL).strip() == "":
    raise ValueError("CRITICAL ERROR: DATABASE_URL is missing from environment variables.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()