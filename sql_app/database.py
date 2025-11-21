from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Format: "mysql+mysqlclient://USER:PASSWORD@HOST/DB_NAME"
SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:1234@localhost/midwife_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()