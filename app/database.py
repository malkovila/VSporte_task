from sqlalchemy import create_engine, URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
Base = declarative_base()

username = os.getenv('DATABASE_USERNAME')
password = os.getenv('DATABASE_PASSWORD')
hostname = os.getenv('DATABASE_HOST')
port = os.getenv('DATABASE_PORT', '5432')
database_name = os.getenv('DATABASE_NAME')

DATABASE_URL = URL.create(
    drivername='postgresql+psycopg2',
    username=username,
    password=password,
    host=hostname,
    database=database_name
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
