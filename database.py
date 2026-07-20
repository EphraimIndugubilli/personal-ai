import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load the environment variable safely
DATABASE_URL = os.getenv("postgresql://neondb_owner:npg_p5QSzYd2wDtE@ep-autumn-sunset-avd8vs2h-pooler.c-11.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

# Do not raise an error immediately on import. 
# Allow Vercel to inspect the file during the build phase.
if DATABASE_URL and str(DATABASE_URL).strip() != "":
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None

Base = declarative_base()

def get_db():
    # Defer the crash to runtime. If the app is actually running and the URL 
    # is STILL missing, then we raise the error.
    if not SessionLocal:
        raise ValueError("CRITICAL ERROR: DATABASE_URL is missing from environment variables at runtime.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()