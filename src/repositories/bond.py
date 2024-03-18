# TODO Добавление динамических фильтров к запросу по образцу
from abc import ABC, abstractmethod

from database.base import session_factory
from models.bond import MoexBonds
from schemas.bond import ColumnGroupModel


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
    '''Класс работы с таблицей bonds'''
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
                    fields_to_update = ['list_level',
                                        'days_to_redemption',
                                        'face_value',
                                        'coupon_date',
                                        'coupon_percent',
                                        'coupon_value',
                                        'sum_coupon',
                                        'highrisk',
                                        'price',
                                        'accint',
                                        'moex_yield',
                                        'year_percent']

                    for field in fields_to_update:
                        setattr(existing_record, field, getattr(bond, field))

                    session.commit()
                else:
                    # Если запись не найдена, создаем новую запись
                    session.add(bond)
                    session.commit()

    @staticmethod
    def select_bonds(fields: list, limit: int = 50):
        with session_factory() as session:

            query = session.query()

            for column_name in fields:
                query = query.add_columns(getattr(MoexBonds, column_name))

            query = (
                query
                .filter(MoexBonds.year_percent.between(5, 20),
                        MoexBonds.highrisk.is_(False),
                        MoexBonds.amortizations.is_(False),
                        MoexBonds.floater.is_(False),
                        MoexBonds.sum_coupon > 10,
                        MoexBonds.days_to_redemption.between(500, 1500))
                .order_by(MoexBonds.year_percent.desc())
                .limit(limit).all())

        result = ColumnGroupModel(columns=fields,
                                  data=[list(i) for i in query])

    # for column_name, filter_data in dynamic_filters.items():
    #     operator = filter_data['operator']
    #     value = filter_data['value']

    #     column = getattr(YourModelClass, column_name)

    #     if operator == '==':
    #         query = query.filter(column == value)
    #     elif operator == '>':
    #         query = query.filter(column > value)
    #     elif operator == '<':
    #         query = query.filter(column < value)
    #     elif operator == 'between':
    #         query = query.filter(between(column, *value))
    #     elif operator == 'is_':
    #         query = query.filter(column.is_(value))

        return result
