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
    # url: Mapped[str | None]
    secid: Mapped[str | None]
    isin: Mapped[str | None]
    matdate: Mapped[str | None]
    initialfacevalue: Mapped[float | None]
    faceunit: Mapped[str | None]
    listlevel: Mapped[int | None]
    daystoredemption: Mapped[int | None]
    facevalue: Mapped[float | None]
    isqualifiedinvestors: Mapped[str | None]
    couponfrequency: Mapped[float | None]
    coupondate: Mapped[str | None]
    couponpercent: Mapped[float | None]
    couponvalue: Mapped[float | None]
    group: Mapped[str | None]
    type: Mapped[str | None]
    price: Mapped[float | None]
    accint: Mapped[float | None]
    effectiveyield: Mapped[float | None]
    # margin: Mapped[float | None]
    # day_percent: Mapped[float | None]
    # year_percent: Mapped[float | None]
