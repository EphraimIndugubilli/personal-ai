import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load local .env if it exists (for local development)
load_dotenv()

# Fetch the variable by its KEY name
DATABASE_URL = os.getenv("postgresql://neondb_owner:npg_3pNPtdOVL9Ug@ep-little-unit-awp830u3-pooler.c-12.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

# Final sanity check
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