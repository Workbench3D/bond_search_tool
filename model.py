# import datetime
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
    couponfrequency: Mapped[int | None]
    coupondate: Mapped[date | None]
    couponpercent: Mapped[float | None]
    couponvalue: Mapped[float | None]
    highrisk: Mapped[int | None]
    group: Mapped[str | None]
    type: Mapped[str | None]
    price: Mapped[float | None]
    accint: Mapped[float | None]
    effectiveyield: Mapped[float | None]
    year_percent: Mapped[float | None]
