"""Database engine and session factory."""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./attendance.db")

# Fix old postgres:// URLs
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Connection args
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
else:
    # PostgreSQL (Neon) — use connection pooling compatible settings
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,       # test connection before use
        pool_recycle=300,         # recycle connections every 5 min
        connect_args={
            "sslmode": "require", # Neon requires SSL
            "connect_timeout": 10,
        }
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
