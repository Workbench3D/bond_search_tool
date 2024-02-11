from datetime import date
from pydantic import BaseModel, Field, field_validator


class ColumnGroupModel(BaseModel):
    columns: list[str]
    data: list[list]


class BondListModel(BaseModel):
    securities: ColumnGroupModel


class PrimaryRequestModel(BaseModel):
    description: ColumnGroupModel


class YieldRequestModel(BaseModel):
    securities: ColumnGroupModel
    marketdata: ColumnGroupModel


class CouponRequestModel(BaseModel):
    amortizations: ColumnGroupModel
    coupons: ColumnGroupModel


class PrimaryDataModel(BaseModel):
    short_name: str = Field(alias='SHORTNAME')
    secid: str = Field(alias='SECID')
    isin: str = Field(alias='ISIN')
    matdate: date = Field(alias='MATDATE', default=date(2000, 1, 1))
    initial_face_value: int = Field(alias='INITIALFACEVALUE')
    face_unit: str = Field(alias='FACEUNIT')
    list_level: int = Field(alias='LISTLEVEL')
    days_to_redemption: int = Field(alias='DAYSTOREDEMPTION', default=0)
    face_value: float = Field(alias='FACEVALUE')
    is_qualified_investors: bool = Field(alias='ISQUALIFIEDINVESTORS')
    coupon_frequency: int = Field(alias='COUPONFREQUENCY', default=0)
    coupon_date: date = Field(alias='COUPONDATE', default=date(2000, 1, 1))
    coupon_percent: float = Field(alias='COUPONPERCENT', default=0.0)
    coupon_value: float = Field(alias='COUPONVALUE', default=0.0)
    high_risk: bool = Field(alias='HIGHRISK', default=False)
    type: str = Field(alias='TYPE')
    name: str = Field(alias='NAME')
    reg_number: str = Field(alias='REGNUMBER', default='None')
    issue_date: str = Field(alias='ISSUEDATE')
    lat_name: str = Field(alias='LATNAME')
    start_date: str = Field(alias='STARTDATEMOEX', default=date(2000, 1, 1))
    registry_number: str = Field(alias='PROGRAMREGISTRYNUMBER', default='')
    earlyre_payment: str = Field(alias='EARLYREPAYMENT', default='')
    issue_size: str = Field(alias='ISSUESIZE')
    type_name: str = Field(alias='TYPENAME')
    group: str = Field(alias='GROUP')
    group_name: str = Field(alias='GROUPNAME')
    emitter_id: str = Field(alias='EMITTER_ID')


class YieldDataModel(BaseModel):
    accint: float = Field(alias='ACCRUEDINT')
    last_price: float | None = Field(alias='LAST')
    last_day_price: float | None = Field(alias='MARKETPRICE')
    moex_yield: float = Field(alias='YIELD')

    @field_validator('last_price')
    def validate_last_price(cls, v):
        if v is None:
            v = 0
            return v
        return v

    @field_validator('last_day_price')
    def validate_last_day_price(cls, v):
        if v is None:
            v = 0
            return v
        return v


class CouponDataModel(BaseModel):
    amortizations: bool
    floater: bool
    sum_coupon: float


class BondModel(BaseModel):
    shortname: str
    secid: str
    matdate: date
    face_unit: str
    list_level: int
    days_to_redemption: int
    face_value: float
    coupon_frequency: int
    coupon_date: date
    coupon_percent: float
    coupon_value: float
    highrisk: bool
    type: str
    accint: float
    price: float
    moex_yield: float
    amortizations: bool
    floater: bool
    sum_coupon: float
    year_percent: float
