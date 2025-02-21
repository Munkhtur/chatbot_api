import psycopg2

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

database= "postgres"
user = "postgres"
host="localhost"
password= "123456"
port = 5432

url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

engine = create_engine(url)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()