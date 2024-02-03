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
    shortname: Mapped[str | None]
    secid: Mapped[str | None]
    isin: Mapped[str | None]
    matdate: Mapped[date | None]
    initialfacevalue: Mapped[int | None]
    faceunit: Mapped[str | None]
    listlevel: Mapped[int | None]
    daystoredemption: Mapped[int | None]
    facevalue: Mapped[float | None]
    isqualifiedinvestors: Mapped[int | None]
    amortizations: Mapped[bool]
    floater: Mapped[bool]
    couponfrequency: Mapped[int | None]
    coupondate: Mapped[date | None]
    couponpercent: Mapped[float | None]
    couponvalue: Mapped[float | None]
    sumcoupon: Mapped[float | None]
    highrisk: Mapped[int | None]
    type: Mapped[str | None]
    price: Mapped[float | None]
    accint: Mapped[float | None]
    effectiveyield: Mapped[float | None]
    yearpercent: Mapped[float | None]

    # def to_read_model(self) -> TaskSchema:
    #     return TaskSchema(
    #         id=self.id,
    #         title=self.title,
    #         author_id=self.author_id,
    #         assignee_id=self.assignee_id,
    #     )
