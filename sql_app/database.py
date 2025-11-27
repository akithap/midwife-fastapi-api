import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Get the Database URL from environment variables (for Railway).
# 2. If not found (running locally), use your hardcoded local connection.
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+mysqlconnector://root:1234@localhost/midwife_db"
)

# CRITICAL FIX FOR RAILWAY:
# Railway provides URLs starting with "mysql://", but the driver 
# 'mysql-connector-python' (which you have in requirements.txt) 
# strictly requires "mysql+mysqlconnector://".
if SQLALCHEMY_DATABASE_URL.startswith("mysql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("mysql://", "mysql+mysqlconnector://", 1)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
