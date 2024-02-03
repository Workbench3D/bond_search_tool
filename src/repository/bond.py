from abc import ABC, abstractmethod

from sqlalchemy import select

from database.base import session_factory
from model.bond import MoexBonds


class AbstractRepository(ABC):
    @abstractmethod
    async def insert_data():
        raise NotImplementedError

    @abstractmethod
    async def update_data():
        raise NotImplementedError

    @abstractmethod
    async def select_bonds():
        raise NotImplementedError


class MoexORM(AbstractRepository):
    ''''''
    # @staticmethod
    # def create_tables():
    #     Base.metadata.drop_all(engine)
    #     Base.metadata.create_all(engine)

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

    @staticmethod
    def select_bonds(fields: list,
                     limit: int) -> list:
        with session_factory() as session:
            selected_fields = [getattr(MoexBonds, field)
                               for field in fields]
            query = select(*selected_fields)
            query = query.filter(MoexBonds.highrisk.is_(None),
                                 MoexBonds.daystoredemption > 200,
                                 MoexBonds.yearpercent < 20,
                                 MoexBonds.amortizations.is_(False),
                                 MoexBonds.floater.is_(False),
                                 MoexBonds.sumcoupon > 5)
            query = query.order_by(MoexBonds.yearpercent.desc())
            if limit:
                query = query.limit(limit)
            result = session.execute(query).all()

        return result

# class TasksRepository(SQLAlchemyRepository):
#     model = Tasks


# class UsersRepository(SQLAlchemyRepository):
#     model = Users
