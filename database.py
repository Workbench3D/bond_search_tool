from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from model import Base, MoexBonds


engine = create_engine(
    url='postgresql+psycopg://admin:password@localhost:5432/moex',
    echo=True,
)

session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class MoexORM:
    ''''''
    @staticmethod
    def create_tables():
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    @staticmethod
    def insert_data(bond: dict):
        with session_factory() as session:
            moex_bond = MoexBonds(
                shortname=bond.get('shortname'),
                isin=bond.get('isin'),
                matdate=bond.get('matdate'),
                initialfacevalue=bond.get('initialfacevalue'),
                faceunit=bond.get('faceunit'),
                listlevel=bond.get('listlevel'),
                daystoredemption=bond.get('daystoredemption'),
                facevalue=bond.get('facevalue'),
                isqualifiedinvestors=bond.get('isqualifiedinvestors'),
                couponfrequency=bond.get('couponfrequency'),
                coupondate=bond.get('coupondate'),
                couponpercent=bond.get('couponpercent'),
                couponvalue=bond.get('couponvalue'),
                group=bond.get('group'),
                type=bond.get('type'),
                price=bond.get('price'),
                accint=bond.get('accint'),
                effectiveyield=bond.get('effectiveyield'),
                margin=bond.get('margin'),
                day_percent=bond.get('day_percent'),
                year_percent=bond.get('year_percent'),
            )
            session.add(moex_bond)
            session.commit()
