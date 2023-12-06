# import datetime
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
    isin: Mapped[str | None]
    matdate: Mapped[str | None]
    initialfacevalue: Mapped[str | None]
    faceunit: Mapped[str | None]
    listlevel: Mapped[str | None]
    daystoredemption: Mapped[str | None]
    facevalue: Mapped[str | None]
    isqualifiedinvestors: Mapped[str | None]
    couponfrequency: Mapped[str | None]
    coupondate: Mapped[str | None]
    couponpercent: Mapped[str | None]
    couponvalue: Mapped[str | None]
    group: Mapped[str | None]
    type: Mapped[str | None]
    price: Mapped[float | None]
    accint: Mapped[float | None]
    effectiveyield: Mapped[float | None]
    margin: Mapped[float | None]
    day_percent: Mapped[float | None]
    year_percent: Mapped[float | None]
