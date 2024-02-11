from datetime import date
from typing import Annotated
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


intpk = Annotated[int, mapped_column(primary_key=True, index=True)]


class Base(DeclarativeBase):
    pass


class MoexBonds(Base):
    __tablename__ = 'bonds'

    id: Mapped[intpk]
    shortname: Mapped[str]
    secid: Mapped[str]
    matdate: Mapped[date]
    face_unit: Mapped[str]
    list_level: Mapped[int]
    days_to_redemption: Mapped[int]
    face_value: Mapped[float]
    coupon_frequency: Mapped[int]
    coupon_date: Mapped[date]
    coupon_percent: Mapped[float]
    coupon_value: Mapped[float]
    highrisk: Mapped[bool]
    type: Mapped[str]
    accint: Mapped[float]
    price: Mapped[float]
    moex_yield: Mapped[float]
    amortizations: Mapped[bool]
    floater: Mapped[bool]
    sum_coupon: Mapped[float]
    year_percent: Mapped[float]

    # def to_read_model(self) -> TaskSchema:
    #     return TaskSchema(
    #         id=self.id,
    #         title=self.title,
    #         author_id=self.author_id,
    #         assignee_id=self.assignee_id,
    #     )
