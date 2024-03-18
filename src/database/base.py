import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


user = os.getenv("POSTGRES_USER", default="admin")
password = os.getenv("POSTGRES_PASSWORD", default="password")
host = os.getenv("POSTGRES_HOST", default="localhost")
db = os.getenv("POSTGRES_DB", default="moex")
port = os.getenv("POSTGRES_PORT", default=5432)

url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"

engine = create_engine(url=url, echo=False)

session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
