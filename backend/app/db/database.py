from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
import os
import time

# ------------------------
# DB URL
# ------------------------
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# ------------------------
# Retry DB Connection
# ------------------------
engine = None

for i in range(10):  # retry 10 times
    try:
        engine = create_engine(DB_URL)

        # Try connecting
        conn = engine.connect()
        conn.close()

        print("✅ Connected to PostgreSQL")
        break

    except OperationalError as e:
        print(f"⏳ DB not ready, retrying... ({i+1}/10)")
        time.sleep(3)

# If still not connected → fail
if engine is None:
    raise Exception("❌ Could not connect to PostgreSQL after multiple attempts")

# ------------------------
# Session
# ------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ------------------------
# Base
# ------------------------
Base = declarative_base()