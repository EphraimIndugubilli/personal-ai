import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL or str(DATABASE_URL).strip() == "":
    # This forces the crash log to reveal EXACTLY what value the OS handed Python
    raise ValueError(f"CRITICAL ERROR: Render gave Python this exact value: {repr(DATABASE_URL)}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()