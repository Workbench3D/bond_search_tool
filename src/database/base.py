from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


engine = create_engine(
    url='postgresql+psycopg://admin:password@localhost:5432/moex',
    echo=False,
)

session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
