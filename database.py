import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("postgresql://neondb_owner:npg_p5QSzYd2wDtE@ep-autumn-sunset-avd8vs2h-pooler.c-11.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

# --- DEBUGGING ---
# flush=True forces the server to instantly print this to the logs before it crashes
print(f"=== DEBUG: VALUE TYPE: {type(DATABASE_URL)} ===", flush=True)
print(f"=== DEBUG: REPR: {repr(DATABASE_URL)} ===", flush=True)
print("===========================================", flush=True)

if not DATABASE_URL or str(DATABASE_URL).strip() == "":
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