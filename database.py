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

    @staticmethod
    def update_data(bonds: list):
        moex_bond = [MoexBonds(**i) for i in bonds]
        with session_factory() as session:
            for bond in moex_bond:
                existing_record = (session.query(MoexBonds)
                                   .filter(MoexBonds.secid == bond.secid)
                                   .first())

                if existing_record:
                    # Если запись найдена, обновляем ее
                    fields_to_update = ['listlevel',
                                        'daystoredemption',
                                        'facevalue',
                                        'coupondate',
                                        'couponpercent',
                                        'couponvalue',
                                        'sumcoupon',
                                        'highrisk',
                                        'price',
                                        'accint',
                                        'effectiveyield',
                                        'yearpercent']

                    for field in fields_to_update:
                        setattr(existing_record, field, getattr(bond, field))

                    session.commit()
                else:
                    # Если запись не найдена, создаем новую запись
                    session.add(bond)
                    session.commit()
