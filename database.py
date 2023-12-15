from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from model import Base, MoexBonds


engine = create_engine(
    url='postgresql+psycopg://admin:password@localhost:5432/moex',
    echo=False,
)

session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class MoexORM:
    ''''''
    @staticmethod
    def create_tables():
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    @staticmethod
    def insert_data(bonds: list):
        with session_factory() as session:
            moex_bond = [MoexBonds(**i) for i in bonds]
            session.add_all(moex_bond)
            session.commit()
