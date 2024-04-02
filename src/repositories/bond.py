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
    """Класс работы с таблицей bonds"""

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
                existing_record = (
                    session.query(MoexBonds)
                    .filter(MoexBonds.secid == bond.secid)
                    .first()
                )

                if existing_record:
                    # Если запись найдена, обновляем ее
                    fields_to_update = [
                        "list_level",
                        "days_to_redemption",
                        "face_value",
                        "coupon_date",
                        "coupon_percent",
                        "coupon_value",
                        "sum_coupon",
                        "highrisk",
                        "price",
                        "accint",
                        "moex_yield",
                        "year_percent",
                    ]

                    for field in fields_to_update:
                        setattr(existing_record, field, getattr(bond, field))

                    session.commit()
                else:
                    # Если запись не найдена, создаем новую запись
                    session.add(bond)
                    session.commit()

    @staticmethod
    def select_bonds(
        fields: list,
        year_percent: tuple,
        list_level: tuple,
        amortizations: bool,
        floater: bool,
        days_to_redemption: tuple,
        ofz_bonds: bool,
        limit: int,
    ):
        with session_factory() as session:
            query = session.query()

            for column_name in fields:
                query = query.add_columns(getattr(MoexBonds, column_name))

            query_filter = [
                MoexBonds.year_percent.between(*year_percent),
                MoexBonds.list_level.between(*list_level),
                MoexBonds.highrisk.is_(False),
                MoexBonds.amortizations.is_(amortizations),
                MoexBonds.floater.is_(floater),
                MoexBonds.sum_coupon > 10,
                MoexBonds.days_to_redemption.between(*days_to_redemption),
            ]

            if ofz_bonds:
                query_filter.append(MoexBonds.type == "ofz_bond")

            query = (
                query.filter(*query_filter)
                .order_by(MoexBonds.year_percent.desc())
                .limit(limit)
                .all()
            )

        result = ColumnGroupModel(columns=fields, data=[list(i) for i in query])

        return result
